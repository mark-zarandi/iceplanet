import os
from flask import Flask, request, jsonify
import flask_excel as excel
from sqlalchemy.dialects.mysql import TIME
from flask import Flask,render_template, request, g
from flask import Flask, request, flash, url_for, redirect, \
     render_template, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate     
from apscheduler.scheduler import Scheduler
import atexit

app = Flask(__name__)
app.config.from_pyfile(os.path.abspath('pod_db.cfg'))
global db
db = SQLAlchemy(app)
migrate = Migrate(app,db)
excel.init_excel(app)

class trans(db.Model):
    __tablename__ = "trans_BW"
    id = db.Column('trans_id', db.Integer, primary_key=True)
    vend_id = db.Column(db.Integer)
    #read_time = db.Column(db.DateTime)
    vend_text = db.Column(db.String)
    trans_text = db.Column(db.String)
    trans_amont = db.Column(db.Float)


    def __init__(self, vend_id,vend_text,trans_text,trans_amount):

        self.vend_id = vend_id
        self.vend_text = vend_text
        self.trans_text = trans_text
        self.trans_amount = trans_amount

@app.route("/upload", methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        db.session.query(trans).delete()
        db.session.commit()
        x = request.get_array(field_name='file')
        iter_x = iter(x)
        y = 0
        for y in range(5):
            next(iter_x)
        for trans_row in iter_x:
            iter_row = iter(trans_row)
            next(iter_row)
            print(iter_row[1])

        return jsonify({"result": "success"})

    return '''
    <!doctype html>
    <title>Upload an excel file</title>
    <h1>Excel file upload (csv, tsv, csvz, tsvz only)</h1>
    <form action="" method=post enctype=multipart/form-data><p>
    <input type=file name=file><input type=submit value=Upload>
    </form>
    '''

def setup_cron():
    cron_list = sch_set.query.order_by(sch_set.id.desc()).all()
    scheduler = BackgroundScheduler()
    scheduler.add_cron_job(func=print_date_time, trigger="interval", seconds=3)
    scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
    print(cron_list)

@app.route("/view", methods=['GET'])
def display_cron():
    cron_list = sch_set.query.order_by(sch_set.id.desc()).all()
    return render_template('set_table.html',set_list=cron_list)

def start_over():
    db.reflect()
    db.drop_all()

if __name__ == "__main__":
    start_over()
    db.create_all()
    app.run()