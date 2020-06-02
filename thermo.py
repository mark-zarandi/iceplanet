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
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import linear_model
import numpy as np
import sys

level    = logging.NOTSET
format   = '%(asctime)-8s %(levelname)-8s %(message)s'
handlers = [logging.handlers.TimedRotatingFileHandler('thermo',when="D",interval=1,backupCount=5,encoding=None,delay=False,utc=False,atTime=None)]
logging.basicConfig(level = level, format = format, handlers = handlers)

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
    adj_temp = db.Column(db.Integer)
    adj_hum = db.Column(db.Integer)
    TC_temp = db.Column(db.Float)
    avg_temp = db.Column(db.Float)

    
    def __str__(self):
        return "Actual Temp %s, Adj Temp %s, Current Set %s" % ((self.curr_temp), self.adj_temp, self.curr_setpoint)

    def __init__(self, read_date, setpoint, curr_hum,curr_temp):

        self.read_date = read_date
        self.curr_setpoint = setpoint
        self.curr_hum = round(curr_hum,2)
        self.curr_temp = round(curr_temp,2)
        self.adj_temp = temp_cond(self.curr_temp + settings['temp_offset'])
        self.adj_hum = hum_cond(self.curr_hum + settings['hum_offset'])
        self.TC_temp = round(-8.96584011843079 + (self.adj_temp * 1.09058722) + ((self.adj_hum/100)*9.73214286),2)
        self.avg_temp = (self.adj_temp + self.TC_temp)/2

def reading_logger():
    logging.info('taking measurements.')


    while True:
        r = requests.get('http://raspberrypi:2121/get_temp').json()
        measure_new = measure(datetime.now(),68,r['hum'],r['temp'])
        db.session.add(measure_new)
        db.session.commit()
        logging.info("read " + str(measure_new))
        therm.set_current_temp(measure_new)
        time.sleep(30)

@app.route('/')
def index():
    temperature_table = measure.query.order_by(measure.read_date.desc()).all()
    return render_template('temperature_table.html',measure_list=temperature_table)
    
def start_over():
    db.reflect()
    db.drop_all()

def main():

    #needs boolean, don't start until reading logger has completed first value.
    global therm
    therm = ThermoMonitor(68)
    logging.info('monitoring temp')
    start_temp_up = threading.Thread(name="recording temp values",target=reading_logger,daemon=True)
    start_temp_up.start()


if __name__ == "__main__":

    #start_over()
    #db.create_all()
    
    bootstrap = Bootstrap(app)
    socketio.run(app,'0.0.0.0')