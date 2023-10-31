#!/usr/bin/env python3

# By Commander Crash 29a Society
# Adafruit_ads1x15 to influx. 
# By defualt reads all 4 channles and puts it in DB called AQI with Chan0-3. 
# You can use -c in command line to only read specific channels -c 1-3
# Change user and pass on ln 23 to match

import argparse
import time
import board
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.ads1x15 import Mode
from adafruit_ads1x15.analog_in import AnalogIn
from influxdb import InfluxDBClient

# Set up command line arguments
parser = argparse.ArgumentParser(description='Read data from an ADS1x15 sensor and insert it into an InfluxDB database.')
parser.add_argument('--channel', '-c', type=int, help='The channel to read from (0-3). If not specified, data will be read from all channels.')
args = parser.parse_args()

# Set up InfluxDB connection
client = InfluxDBClient('localhost', 8086, '#Your_username', '#Your_pass', '#Your_Database')

# Set up ADS1x15 sensor
i2c = board.I2C()
ads = ADS.ADS1115(i2c)
ads.mode = Mode.CONTINUOUS
ads.data_rate = 860
ads.gain = 1

# Set up analog inputs
chan0 = AnalogIn(ads, ADS.P0)
chan1 = AnalogIn(ads, ADS.P1)
chan2 = AnalogIn(ads, ADS.P2)
chan3 = AnalogIn(ads, ADS.P3)

# Read data from specified channel(s) or all channels
if args.channel is not None:
    channels = [args.channel]
else:
    channels = [0, 1, 2, 3]

while True:
    for channel in channels:
        if channel == 0:
            value = chan0.value + 18
            name = 'chan0'
        elif channel == 1:
            value = chan1.value
            name = 'chan1'
        elif channel == 2:
            value = chan2.value
            name = 'chan2'
        elif channel == 3:
            value = chan3.value
            name = 'chan3'
        else:
            continue

        # Insert data into InfluxDB
        data = [{
            "measurement": name,
            "fields": {
                "value": value,
            }
        }]
        client.write_points(data)

    # Wait for 323 seconds before reading again you can lower this if you have nothing else accessing the ADS. If 2 or more scripts tries to read at the same time it will crash.
    time.sleep(323)
