import logging
from logging import handlers
from flask import Flask,render_template, request
from flask import Flask, request, flash, url_for, redirect, \
     render_template, jsonify
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
from datetime import datetime
import flask_excel as excel
#import matplotlib.pyplot as plt
#import numpy as np
import sys
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
port = 1
address = 0x77
bus = smbus2.SMBus(port)

logging.basicConfig(level = level, format = format, handlers = handlers)
calibration_params = bme280.load_calibration_params(bus, address)

class MyFlaskApp(SocketIO):
  def run(self, app, host=None, port=None, debug=None, load_dotenv=True, **options):
    #if self.debug or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
     # with self.app_context():

    start_HVAC = threading.Thread(name="HVAC_unit",target=main, daemon=True)
    start_HVAC.start()

    super(MyFlaskApp, self).run(app=app,host=host, port=port, debug=True,use_reloader=False,**options)



app = Flask(__name__)
app.config.from_pyfile(os.path.abspath('pod_db.cfg'))
global db
db = SQLAlchemy(app)
migrate = Migrate(app,db)
excel.init_excel(app)

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
    curr_setpoint = db.Column(db.Integer)
    curr_hum = db.Column(db.Float)
    curr_temp = db.Column(db.Float)
    adj_temp = db.Column(db.Float)
    adj_hum = db.Column(db.Float)
    TC_temp = db.Column(db.Float)
    avg_temp = db.Column(db.Float)
    HVAC_state = db.Column(db.String)

    def set_state(self, the_state):
        self.HVAC_state = the_state

    
    def __str__(self):
        return "Actual Temp %s, Adj Temp %s, Current Set %s" % ((self.curr_temp), self.adj_temp, self.curr_setpoint)

    def __init__(self, read_date, setpoint, curr_hum,curr_temp):

        self.read_date = read_date
        self.curr_setpoint = setpoint
        self.curr_hum = round(curr_hum,2)
        self.curr_temp = round(curr_temp,2)
        self.adj_temp = temp_cond(self.curr_temp)
        #make sure this gets fix on
        #self.adj_hum = round(self.curr_hum-((.43785694*self.curr_hum)-22.253659085944268),2)
        self.adj_hum = self.curr_hum
        self.TC_temp = round(-8.96584011843079 + (self.curr_temp * 1.09058722) + ((self.adj_hum/100)*9.73214286),2)
        self.avg_temp = (self.adj_temp + self.TC_temp)/2



def reading_logger():
    logging.info('LOGGER: Taking measurements.')


    while True:
        data = bme280.sample(bus, address, calibration_params)
        temperature = ((data.temperature*1.8)+32)
        measure_new = measure(datetime.now(),70,data.humidity,temperature)
        add_this = therm.set_current_temp(measure_new)
        measure_new.set_state(add_this)
        db.session.add(measure_new)
        db.session.commit()
        logging.info("LOGGER Read: " + str(measure_new))
        therm.set_current_temp(measure_new)
        time.sleep(60)

@app.route('/')
def index():
    temperature_table = measure.query.order_by(measure.read_date.desc()).limit(60)
    return render_template('temperature_table.html',measure_list=temperature_table)
@app.route('/export', methods=['GET'])
def xls_out():
    now = datetime.now()
    date_time = "dump_thermo-" + now.strftime("%m.%d.%Y-%H.%M")
    return excel.make_response_from_a_table(session=db.session,status=200,table=measure,file_type="xlsx",file_name=date_time)


def start_over():
    db.reflect()
    db.drop_all()

def main():

    #needs boolean, don't start until reading logger has completed first value.
    global therm
    therm = ThermoMonitor(70)
    logging.info('MAIN: Starting Up')
    start_temp_up = threading.Thread(name="recording temp values",target=reading_logger,daemon=True)
    start_temp_up.start()


if __name__ == "__main__":

    #start_over()
    db.create_all()
    
    bootstrap = Bootstrap(app)
    socketio.run(app,host='0.0.0.0',port=1949)
