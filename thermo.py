import logging
from logging import handlers
from flask import Flask,render_template, request, g
from flask import Flask, request, flash, url_for, redirect, \
     render_template, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_socketio import SocketIO, send, emit
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
import threading
from thermo_monitor import ThermoMonitor
import requests
from resources import settings
import math
import os
import time
from datetime import datetime, timedelta
import flask_excel as excel
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
#import numpy as np
import sys
import random
import io
import numpy as np
import matplotlib.dates as mdates
import matplotlib.cbook as cbook
import dateutil.parser
import smbus2
import bme280

level    = logging.NOTSET
format   = '%(asctime)-8s %(levelname)-8s %(message)s'
formatter = logging.Formatter(format,"%Y-%m-%d %H:%M:%S")
writer = logging.StreamHandler()
writer.setFormatter(formatter)
handlers = [writer,logging.handlers.TimedRotatingFileHandler('thermo',when="D",interval=1,backupCount=5,encoding=None,delay=False,utc=False,atTime=None)]
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

thread_stop_event = threading.Event()
socket_thread = threading.Thread()
#bus = smbus2.SMBus(port)

logging.basicConfig(level = level, format = format, handlers = handlers)


thermo_handle = ThermoMonitor(70)

def reading_logger():
    logging.info('LOGGER: Taking measurements.')
    port = 1
    address = 0x76
    try:
        bus = smbus2.SMBus(port)
        calibration_params = bme280.load_calibration_params(bus, address)
        while True:
            current_set = thermo_handle.get_set()
            data = bme280.sample(bus, address, calibration_params)
            temperature = ((data.temperature*1.8)+32) + settings['setpoints'][int(current_set)]['temp_offset']
            measure_new = measure(datetime.now(),int(current_set),data.humidity,temperature,0)
            add_this = thermo_handle.set_current_temp(measure_new, mode)
            logging.info("STATE: " + add_this)
            measure_new.set_state(add_this)
            db.session.add(measure_new)
            db.session.commit()
            logging.info("LOGGER Read: " + str(measure_new))
            time.sleep(60)
    except OSError:
        note = requests.get('https://maker.ifttt.com/trigger/change/with/key/bwuymkNBi9Ga5iBN0-NXDD')
        time.sleep(120)
        os.system('reboot')
def main():

    #needs boolean, don't start until reading logger has completed first value.

    logging.info('MAIN: Starting Up')
    #start_temp_up = threading.Thread(name="recording temp values",target=reading_logger,daemon=True)
    #start_temp_up.start()

class MyFlaskApp(SocketIO):

  def run(self, app, host=None, port=None, debug=None, load_dotenv=True, **options):
    start_HVAC = threading.Thread(name="HVAC_unit",target=reading_logger, daemon=True)
    start_HVAC.start()


    super(MyFlaskApp, self).run(app=app,host=host, port=port, debug=True,use_reloader=False,**options)



app = Flask(__name__)
app.config.from_pyfile(os.path.abspath('pod_db.cfg'))
global db
db = SQLAlchemy(app)
migrate = Migrate(app,db)
excel.init_excel(app)
mode = "heat"
socketio = MyFlaskApp(app)

def temp_cond(fix_this):
#greater than .8 roundup, otherwise roundDOWN
    x = round(fix_this - math.floor(fix_this),1)
    if x >= .8:
        return int(round(fix_this,0))
    else:
        return int(math.floor(fix_this))

def hum_cond(fix_this):
#greater than .8 roundup, otherwise roundDOWN
    x = round(fix_this - math.floor(fix_this),1)
    if x >= .8:
        return int(round(fix_this,0))
    else:
        return int(math.floor(fix_this))

class measure(db.Model):
    __tablename__ = "measurements"
    id = db.Column('measure_id', db.Integer, primary_key=True)
    read_date = db.Column(db.DateTime)
    #read_time = db.Column(db.DateTime)
    curr_setpoint = db.Column(db.Integer)
    curr_hum = db.Column(db.Float)
    curr_temp = db.Column(db.Float)
    adj_temp = db.Column(db.Float)
    adj_hum = db.Column(db.Float)
    HVAC_state = db.Column(db.String)

    def set_state(self, the_state):
        self.HVAC_state = the_state

    
    def __str__(self):
        return "Actual Temp %s, Adj Temp %s, Current Set %s" % ((self.curr_temp), self.adj_temp, self.curr_setpoint)

    def __init__(self, read_date, setpoint, curr_hum,curr_temp,offset):

        self.read_date = read_date
        self.curr_setpoint = setpoint
        self.curr_hum = round(curr_hum/100,2)
        self.curr_temp = round(curr_temp,2)
        self.adj_temp = temp_cond(self.curr_temp+offset)
        self.HVAC_state = ""
	#make sure this gets fix on
        #self.adj_hum = round(self.curr_hum-((.43785694*self.curr_hum)-22.253659085944268),2)
        self.adj_hum = self.curr_hum
        #self.TC_temp = round(-8.96584011843079 + (self.curr_temp * 1.09058722) + ((self.adj_hum/100)*9.73214286),2)
        #self.avg_temp = (self.adj_temp + self.TC_temp)/2

@app.route('/force_on')
def force_on():
    thermo_handle.start_cooling('FORCE')
    succ_response = {"status":"OK",'task':'forced on'}
    return jsonify(succ_response)

@app.route('/setpoint/<change_point>')
def change_set(change_point):
    #this needs if in for missing setpoints
    thermo_handle.change_set(int(change_point))
    succ_response = {"status":"OK","new set":change_point}
    return jsonify(succ_response)

@app.route('/mode/<new_mode>')
def change_mode(new_mode):
    mode = str(new_mode)
    succ_response = {"status":"OK","new_mode":new_mode}
    return jsonify(succ_response)

@app.route('/force_off')
def force_off():
    thermo_handle.turn_off()
    succ_response = {"status":"OK",'task':'forced off'}
    return jsonify(succ_response)

@app.route('/plot.png')
def plot_png():
    fig = create_figure()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

def create_figure():
    hours_tick = mdates.HourLocator()
    minute_tick = mdates.MinuteLocator(byminute=30)
    the_look = mdates.DateFormatter("%H:%M")
    fig = Figure(figsize=(8,6))
    axis = fig.add_subplot(1, 1, 1)
    xs =[]
    ys = []
    xs_query = measure.query.with_entities(measure.curr_temp).order_by(measure.read_date.desc()).all()
    for x in xs_query:
        xs.append(x)

    xs = np.asarray(xs)

    ys_query = measure.query.with_entities(measure.read_date).order_by(measure.read_date.desc()).all()
    for y in ys_query:
        ys.append(y)
    ys = np.asarray(ys)

    axis.plot(ys, xs)
    axis.xaxis.set_major_locator(hours_tick)
    axis.xaxis.set_major_formatter(the_look)
    axis.xaxis.set_minor_locator(minute_tick)
    fig.autofmt_xdate()
    
    return fig


@app.route('/date_pick')
def render_date_chooser():
    return render_template('date_pick.html')


@app.route('/filter_test', methods=['POST'])
def filter_date():
    #user_submit and user end will BOTH need to have times.

    user_submit = datetime.strptime(request.form['date_pick'],'%m/%d/%Y')
    print(user_submit)
    user_end = user_submit + timedelta(hours=23,minutes=59)
    print(user_end)
    temp_table_x = measure.query.with_entities(measure.curr_temp).filter(measure.read_date.between(user_submit,user_end)).order_by(measure.read_date.desc()).all()
    temp_table_y = measure.query.with_entities(measure.read_date).filter(measure.read_date.between(user_submit,user_end)).order_by(measure.read_date.desc()).all()
    fig = create_figure()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

    #return render_template('temperature_table.html',measure_list=temperature_table)

@app.route('/')
def index():
    temperature_table = measure.query.order_by(measure.read_date.desc()).limit(60)
    return render_template('temperature_table.html',measure_list=temperature_table)

@app.route('/change_set/<new_set>')
def change_set_at_monitor(new_set):
    thermo_handle.change_set(int(new_set))
    succ_response = {"status":"OK",'new set':new_set}
    return jsonify(succ_response)

@app.route('/export', methods=['GET'])
def xls_out():
    now = datetime.now()
    date_time = "dump_thermo-" + now.strftime("%m.%d.%Y-%H.%M")
    return excel.make_response_from_a_table(session=db.session,status=200,table=measure,file_type="xlsx",file_name=date_time)


def start_over():
    db.reflect()
    db.drop_all()

@app.route("/test")
def does_it_work():
    figure_look = measure.query.first()
    print(figure_look)
    succ_response = {"status":"OK"}
    return jsonify(succ_response)

def temp_sender_thread():
    """
    Generate a random number every 1 second and emit to a socketio instance (broadcast)
    Ideally to be run in a separate thread?
    """
    
    logging.info("Sending Temp Updates")
    while not thread_stop_event.isSet():
        number = measure.query.order_by(measure.id.desc()).first()
        logging.info(number)
        socketio.emit('newtemp', {'temp': number.curr_temp,"hum":number.curr_hum,"set":number.curr_setpoint,"state":number.HVAC_state}, namespace='/thermostat')
        socketio.sleep(30)

@socketio.on('connect', namespace='/thermostat')
def temperature_connect():
    # need visibility of the global thread object
    global socket_thread
    print('Client connected')
    thread_stop_event.clear()
    #Start the random number generator thread only if the thread has not been started before.
    if not socket_thread.isAlive():
        print("Starting Thread")
        socket_thread = socketio.start_background_task(temp_sender_thread)

@socketio.on('disconnect', namespace='/thermostat')
def temperature_disconnect():

    print('Client disconnected')
    if socket_thread.isAlive():
        global thread_stop_event
        thread_stop_event.set()
        print('Disconected & thread stopped')



if __name__ == "__main__":

    #start_over()
    db.create_all()
    
    bootstrap = Bootstrap(app)
    socketio.run(app,host='0.0.0.0',port=1949)
