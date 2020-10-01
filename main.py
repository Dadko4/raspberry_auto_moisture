from flask import Flask, render_template, make_response, jsonify, request
from gpiozero import MCP3008
import RPi.GPIO as gpio
import time
from datetime import datetime
import numpy as np
import requests
state = None
mode = None
rains = None


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


@app.route('/rain')
def get_rain():
    global rains
    city = request.args.get('city', '')
    now_hour = datetime.now().hour
    for i in range(3):
        if (now_hour - i) % 3 == 0:
            now_hour -= i
            break
    next_hours = set(
        [f'{h%24}:00:00' for h in range(now_hour, now_hour + 5, 3)])
    if rains is None or not next_hours.issubset(rains):
        url = ("http://api.openweathermap.org/data/2.5/forecast?"
               "q={city}&units=metric&"
               "appid=4280c297a11c3965f90379ab64819a43").format(city=city)
        try:
            r = requests.get(url)
        except:
            return jsonify({"rain": 0.0}), 200
        weather_list = r.json().get('list', [])
        rains = {}
        for l in weather_list[:6]:
            key = l.get('dt_txt')
            if key is not None:
                rains[key.split()[1]] = l.get('rain', {'3h': 0.0})['3h']
    sel_rains = [rains.get(h, 0.0) for h in next_hours]
    return jsonify({"rain": np.sum(sel_rains)}), 200


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
def moisture():
    moisture = get_moisture()
    return jsonify({"moisture": moisture}), 200


@app.route('/change_mode')
def change_mode():
    global mode
    if mode == "OFF":
        mode = "ON"
        color = "#2f7527"
    else:
        mode = "OFF"
        color = "#c10000"
    return jsonify({"state": mode, "color": color}), 200


@app.route('/', methods=['POST', 'GET'])
def home():
    gpio.output(14, gpio.HIGH)
    state = gpio.HIGH
    mode = "ON"
    color = "#123d94"
    moisture = get_moisture()
    with open("mesta.txt", "r", encoding="utf-8") as f:
        cities = f.readlines()
    cities = [city.replace('\n', '') for city in cities]
    return render_template('index.html', color=color,
                           moisture=moisture, cities=cities)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=14000)
