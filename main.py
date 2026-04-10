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

# MAIN

stop = False
bmp_runner = False
gyro_runner = False
prox_runner = False
sum = False
map_runner = False

@socketio.on('stopButton')
def stop():
    global stop = True

# BMP

from bmp180 import BMP180

bmp_sensor = BMP180()
alt_log = []

@socketio.on('bmpButton')
def get_bmp():
    global bmp_runner = True

@socketio.on('setZero')
def zero():
    global zero_bmp = bmp_sensor.get_pressure()

# GYRO

from mpu6050 import mpu6050

gyro = mpu6050(0x68)
acc_log = [(0, 0, 0),]
dps_log = [(0, 0, 0),]
vel_log = [(0, 0, 0),]
pos_log = [(0, 0, 0),]

@socketio.on('gyroButton')
def get_gyro():
    global gyro_runner = True

# PROX

from tfluna import TFLuna

prox_sensor = TFLuna()
tfluna.open()
tfluna.set_samp_rate(5)
dist_log = []
map_data = []

@socketio.on('proxButton')
def get_prox():
    global prox_runner = True

@socketio.on('sumButton')
def get_prox():
    global sum = True

@socketio.on('mapButton')
def get_map():
    global map_runner = True

# Runs in the background to transmit data to connected clients.
def background_thread():
    while True:
        if bmp_runner:
            while True:
                if stop:
                    stop = False
                    bmp_runner = False
                    break
                socketio.sleep(2)
                bmp = bmp_sensor.get_pressure() / 100
                if zero_bmp:
                    altitude = bmp_sensor.get_altitude(sea_level_pressure = zero_bmp)
                    alt_log.append(altitude)
                socketio.emit(
                    'update_bmp',
                    {
                        'bmp': bmp,
                        'altitude': altitude,          # possible error due to inexistent values (if so, create 2 different path for "emit" with "if" statement)
                        'altLog': alt_log             # possible error due to conversion list/tuple to array
                    }
                )
                
        if gyro_runner:
            while True:
                if stop:
                    stop = False
                    gyro_runner = False
                    break
                socketio.sleep(2)
                acc = gyro.get_accel_data()
                acc_data = (acc['x'], acc['y'], acc['z'])
                acc_log.append(acc_data)
                
                dps = gyro.get_gyro_data()
                dps_data = (dps['x'], dps['y'], dps['z'])
                dps_log.append(dps_data)
                
                #INTEGRATION
                x_vel = vel_log[-1][0] + ((acc_log[-2][0] + acc_log[-1][0]) / 2) * 2
                y_vel = vel_log[-1][1] + ((acc_log[-2][1] + acc_log[-1][1]) / 2) * 2
                z_vel = vel_log[-1][2] + ((acc_log[-2][2] + acc_log[-1][2]) / 2) * 2
                vel_data = (x_vel, y_vel, z_vel)
                vel_log.append(vel_data)
                x_pos = pos_log[-1][0] + ((vel_log[-2][0] + vel_log[-1][0]) / 2) * 2
                y_pos = pos_log[-1][1] + ((vel_log[-2][1] + vel_log[-1][1]) / 2) * 2
                z_pos = pos_log[-1][2] + ((vel_log[-2][2] + vel_log[-1][2]) / 2) * 2
                pos_data = (x_pos, y_pos, z_pos)
                pos_log.append(pos_data)
                
                socketio.emit(
                    'update_gyro',
                    {
                        'acc': acc,
                        'accLog': acc_log,            # possible error due to conversion list/tuple to array
                        'dps': dps,
                        'dpsLog': dps_log,         # possible error due to conversion list/tuple to array
                        'pos': pos_data,
                        'posLog': pos_log
                    }
                )

        if prox_runner:
            prox, _, _ = tfluna.read()
            prox = round(prox * 100.0, 2)
            dist_log.append(prox)
            prox_runner = False
            socketio.emit(
                'update_prox',
                {
                    'prox': prox
                }
            )

        if sum:
            dist_sum = dist_log[-2] + dist_log[-1]
            sum = False
            socketio.emit(
                'update_sum',
                {
                    'sum': dist_sum
                }
            )

        if map_runner:
            while True:
                if stop:
                    stop = False
                    map_runner = False
                    break
                socketio.sleep(1)
                rad, _, _ = tfluna.read()
                rad = round(rad * 100.0, 2)
                #theta = gyro.get_gyro_data()
                #theta_data = (theta['x'], theta['y'], theta['z'])
                #map_data.append((rad, theta))
                

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------        
        
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
