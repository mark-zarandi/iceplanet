import socketio

sio = socketio.Client()
@sio.event
def message(data):
    print("i received a message")


sio.connect("http://zarandi.duckdns.org:1949/thermostat")
sio.wait()
    