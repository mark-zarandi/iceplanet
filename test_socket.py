import socketio
import sys

sio = socketio.Client()

def start_up():

    sio.connect("http://thermostat:1949/",namespaces=['/thermostat'])
    sio.wait()

@sio.event
def connect():
    print('connected')

@sio.on('newtemp',namespace='/thermostat')
def message(data):
    print(data)

if __name__ == "__main__":
    sys.exit(start_up())



    
