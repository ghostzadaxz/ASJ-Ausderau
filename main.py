# These two modules allow us to run a web server.
from flask import Flask, render_template
from flask_socketio import SocketIO

import random

# Creates the necessary base app
app = Flask(__name__)
socketio = SocketIO(app)

# When someone requests the root page from the web server, returns 'index.html'.
@app.route('/')
def index():
    return render_template('index.html')

# Runs in the background to transmit data to connected clients.
def background_thread():
    while True:
        socketio.sleep(1)
        # You should replace the data being sent back with your sensor data
        # that you fetch from things connected to your Pi.
        socketio.emit(
            'update_data',
            {
                'randomNumber': random.randint(1, 100),
                # you can add more here! for instance, something along the lines of:
                # 'mySensor': mysensor.get_sensor_data(),
            }
        )
        # To add a your first new sensor, try giving https://docs.aerospacejam.org/getting-started/first-sensor a read!

# Runs when someone connects to the server - starts the background thread to update the data.
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    socketio.start_background_task(target=background_thread)

def main():
    # These specific arguments are required to make sure the webserver is hosted in a consistent spot, so don't change them unless you know what you're doing.
    socketio.run(app, host='0.0.0.0', port=90, allow_unsafe_werkzeug=True)
    
if __name__ == '__main__':
    main()
