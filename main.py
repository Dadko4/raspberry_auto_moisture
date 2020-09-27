from flask import Flask, render_template, make_response, jsonify
from gpiozero import MCP3008
import RPi.GPIO as gpio
import time
import numpy as np
from threading import Thread
state = None
divider = MCP3008(0)
app = Flask(__name__)

def get_moisture():
    values = []
    for _ in range(10):
        values.append(float(divider.value))
        time.sleep(0.01)
    return round(1 - np.mean(values), 2)
    
@app.before_first_request
def init_output():
    gpio.setup(14, gpio.OUT)
    gpio.output(14, gpio.HIGH)
    
@app.route('/off')
def off():
    global state
    gpio.output(14, gpio.HIGH)
    state = gpio.HIGH
    color = "#123d94"
    return jsonify({"color": color}), 200
    
@app.route('/on')
def on():
    global state
    gpio.output(14, gpio.LOW)
    state = gpio.LOW
    color = "#c10000"
    return jsonify({"color": color}), 200
    
@app.route('/one_time')
def one_time():
    for _ in range(5):
        gpio.output(14, gpio.LOW)
        time.sleep(1.2)
        gpio.output(14, gpio.HIGH)
        time.sleep(1)
    state = gpio.HIGH
    color = "#123d94"
    return jsonify({"color": color}), 200

@app.route('/on_off')
def on_off():
    global state
    if state == gpio.HIGH:
        return on()
    else:
        return off()

@app.route('/moisture')
def moisture_route():
    moisture = get_moisture()
    return jsonify({"moisture": moisture}), 200

@app.route('/', methods=['POST', 'GET'])
def home():
    gpio.output(14, gpio.HIGH)
    state = gpio.HIGH
    color = "#123d94"
    moisture = get_moisture()
    return render_template('index.html', color=color,
                           moisture=moisture)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=14000)

