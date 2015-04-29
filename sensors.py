import pyupm_i2clcd as lcd
import mraa
import time
import sys
import math
import os
import socket
import json
from datetime import datetime
import netifaces as ni

# MACRO
DATA_INTERVAL = 600 # 600 seconds

# Network information
HOST = "127.0.0.1"
PORT = 41234

print "Initializing components...\n"

# Hardware Data

# Analog Inputs
# Light Sensor
lightPin = 0
lum = mraa.Aio(lightPin)
lumVal = 0

tmpPin = 1
tmp = mraa.Aio(tmpPin)
tmpVal = 0

potPin = 2
pot = mraa.Aio(potPin)
potVal = 0
potGrnVal=0
potBluVal=0

# Digital Outputs
# Red LED
ledPin = mraa.Gpio(8)
ledPin.dir(mraa.DIR_OUT)
ledPin.write(0)

# Buzzer
#buzPin = mraa.Gpio(8)
#buzPin.dir(mraa.DIR_OUT)
#buzPin.write(0)

# RGB LCD Display
lcdDisplay = lcd.Jhd1313m1(0, 0x3E, 0x62)

# Digital Inputs
# Button
touchPin = mraa.Gpio(7)
touchPin.dir(mraa.DIR_IN)

def register_metric(metric_name, metric_type):

    msg = {
        "n": metric_name,

         "t": metric_type
    }


    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.sendto(json.dumps(msg), (HOST, PORT))

def send_data(metric_name, value):

    msg = {

        "n": metric_name,

        "v": value

    }

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.sendto(json.dumps(msg), (HOST, PORT))

start = time.time() + 600   # Forces sending at startup for debugging puporses

show_ip = False

print "Components initialized!\n"

while 1:

    # read pot/print/convert to string/display on lcd
    potVal = int(pot.read()*.249)
    lumVal = float(lum.read())
    tmpVal = float(tmp.read())
    bVal = 3975
    resistanceVal = (1023 - tmpVal) * 10000 / tmpVal
    celsiusVal = 1 / (math.log(resistanceVal / 10000) / bVal + 1 / 298.15) - 273.15
    #fahrVal = (celsiusVal * (9 / 5)) + 32

    if touchPin.read() == 1:
        print "Pot: "+ str(potVal) + "\tLumens: " + str(lumVal) + "\tTemp: " + str(celsiusVal) + "\tTime: " + str(datetime.now()) + "\t TTS: " + str(DATA_INTERVAL - (time.time() - start))
        # Toggle showing IP
        show_ip = not show_ip

    lcdDisplay.clear()
    lcdDisplay.setCursor(0, 0)
    lcdDisplay.setColor(potVal,0,0)

    if show_ip:
        ip = ni.ifaddresses('wlan0')[2][0]['addr']
        lcdDisplay.write(ip)
    else:
        potStr = "P:" + str(potVal) + " - L:" + str(lumVal)
        lcdDisplay.write(potStr)

    lumStr = "Temp: " + str(celsiusVal)
    lcdDisplay.setCursor(1, 0)
    lcdDisplay.write(lumStr)

    # Check if DATA_INTERVAL has passed
    if (time.time() - start) > DATA_INTERVAL:
        # Turn LED on
        ledPin.write(1)
        # Register component and send value to the cloud
        register_metric("temp", "temperature.v1.0")
        send_data("temp", celsiusVal)
        print "Sent data to the cloud!\n"
        # Turn LED off
        ledPin.write(0)

        # Reset timer
        start = time.time()

    time.sleep(0.2)
