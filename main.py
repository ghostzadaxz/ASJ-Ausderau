# These two modules allow us to run a web server.
from flask import Flask, render_template
from flask_socketio import SocketIO

# Creates the necessary base app
app = Flask(__name__)
socketio = SocketIO(app)

# When someone requests the root page from the web server, returns 'index.html'.
@app.route('/')
def index():
    return render_template('index.html')

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@socketio.on('stopButton')
def stop():
    return True

# BMP

from bmp180 import BMP180

bmp_sensor = BMP180()

@socketio.on('bmpButton')
def get_bmp(msg):
    if msg[start]:
        return True
    else:
        return False

@socketio.on('setZero')
def zero():
    zero_bmp = bmp_sensor.get_pressure()

# Runs in the background to transmit data to connected clients.
def background_thread():
    while True:
        if get_bmp():
            while True:
                if stop():
                    break
                socketio.sleep(1)
                bmp = bmp_sensor.get_pressure() / 100
                altitude = bmp_sensor.get_altitude(sea_level_pressure = zero_bmp)
                socketio.emit(
                    'update_bmp',
                    {
                        'bmp': bmp,
                        'altitude': altitude
                    }
                )

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------        
        
# Runs when someone connects to the server - starts the background thread to update the data.
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    socketio.start_background_task(target=background_thread)

def main():
    # These specific arguments are required to make sure the webserver is hosted in a consistent spot, so don't change them unless you know what you're doing.
    socketio.run(app, host='0.0.0.0', port=80, allow_unsafe_werkzeug=True)
    
if __name__ == '__main__':
    main()
