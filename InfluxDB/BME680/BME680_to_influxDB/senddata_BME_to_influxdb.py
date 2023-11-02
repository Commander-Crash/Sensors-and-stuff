#!/usr/bin/env python
import time
import sys
import datetime
from influxdb import InfluxDBClient
import socket
import bme680
import configparser
import math
from sense_hat import SenseHat

sense = SenseHat()
sense.set_rotation(90)

def display_message(message, color, scroll_speed):
    sense.show_message(message, text_colour=color, scroll_speed=scroll_speed)

def get_raspid():
    cpuserial = "0000000000000000"
    with open('/proc/cpuinfo', 'r') as f:
        for line in f:
            if line[0:6] == 'Serial':
                cpuserial = line[10:26]
    return cpuserial

def calculate_dew_point(temp, hum):
    dew_point = (temp - ((100 - hum) / 5))
    return dew_point

def calculate_delta_t(temp, hum):
    delta_t = 0.36 * (temp - 45) + 0.1 * (hum - 45) + 21.7
    return delta_t

if len(sys.argv) == 2:
    configpath = sys.argv[1]
else:
    print("ParameterError: You must define the path to the config.ini!")
    sys.exit()

config = configparser.ConfigParser()
try:
    config.read(configpath)
    influxserver = config['influxserver']
    host = influxserver.get('host')
    port = influxserver.get('port')
    user = influxserver.get('user')
    password = influxserver.get('password')
    dbname = influxserver.get('dbname')
    sensor = config['sensor']
    enable_gas = sensor.getboolean('enable_gas')
    session = sensor.get('session')
    location = sensor.get('location')
    temp_offset = float(sensor['temp_offset'])
    interval = int(sensor['interval'])
    burn_in_time = float(sensor['burn_in_time'])

except TypeError:
    print("TypeError parsing config.ini file. Check boolean datatypes!")
    sys.exit()
except KeyError:
    print("KeyError parsing config.ini file. Check file and its structure!")
    sys.exit()
except ValueError:
    print("ValueError parsing config.ini file. Check number datatypes!")
    sys.exit()

sensor = bme680.BME680(0x77)
raspid = get_raspid()

now = datetime.datetime.now()
runNo = now.strftime("%Y%m%d%H%M")
hostname = socket.gethostname()

print("Session: ", session)
print("runNo: ", runNo)
print("raspid: ", raspid)
print("hostname: ", hostname)
print("location: ", location)

client = InfluxDBClient(host, port, user, password, dbname)

sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_temp_offset(temp_offset)

if enable_gas:
    sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
    sensor.set_gas_heater_temperature(320)
    sensor.set_gas_heater_duration(150)
    sensor.select_gas_heater_profile(0)
else:
    sensor.set_gas_status(bme680.DISABLE_GAS_MEAS)

start_time = time.time()
curr_time = time.time()
burn_in_data = []

try:
    sense.clear()
    
    if enable_gas:
        display_message("INITIALIZING BME", [255, 255, 255], 0.1)
        print("Collecting gas resistance burn-in data\n")
        while curr_time - start_time < burn_in_time:
            curr_time = time.time()
            if sensor.get_sensor_data() and sensor.data.heat_stable:
                gas = sensor.data.gas_resistance
                burn_in_data.append(gas)
                print("Gas: {0} Ohms".format(gas))
                time.sleep(1)

        gas_baseline = int(sum(burn_in_data[-50:]) / 50.0)
        hum_baseline = 40.0
        hum_weighting = 0.25

        print("Gas baseline: {0} Ohms, humidity baseline: {1:.2f} %RH\n".format(gas_baseline, hum_baseline))

        display_message("BME READY", [255, 255, 255], 0.1)

    while True:
        if sensor.get_sensor_data():
            hum = sensor.data.humidity
            temp = sensor.data.temperature
            press = sensor.data.pressure + 7
            temp = temp * 9/5.0 + 32 - 4
            dew_point = calculate_dew_point(temp, hum)
            delta_t = calculate_delta_t(temp, hum)
            iso = time.asctime(time.gmtime())

            if enable_gas:
                hum_offset = hum - hum_baseline
                gas = int(sensor.data.gas_resistance)
                gas_offset = gas_baseline - gas

                if hum_offset > 0:
                    hum_score = (100 - hum_baseline - hum_offset) / (100 - hum_baseline) * (hum_weighting * 100)
                else:
                    hum_score = (hum_baseline + hum_offset) / hum_baseline * (hum_weighting * 100)

                if gas_offset > 0:
                    gas_score = (gas / gas_baseline) * (100 - (hum_weighting * 100))
                else:
                    gas_score = 100 - (hum_weighting * 100)

                air_quality_score = hum_score + gas_score
                air_quality_score = round(air_quality_score, 0)

                json_body = [
                    {
                        "measurement": session,
                        "tags": {
                            "run": runNo,
                            "raspid": raspid,
                            "hostname": hostname,
                            "location": location
                        },
                        "time": iso,
                        "fields": {
                            "temp": temp,
                            "press": press,
                            "humi": hum,
                            "dew_point": dew_point,
                            "delta_t": delta_t,
                            "gas": gas,
                            "iaq": air_quality_score,
                            "gasbaseline": gas_baseline,
                            "humbaseline": hum_baseline
                        }
                    }
                ]

            else:
                json_body = [
                    {
                        "measurement": session,
                        "tags": {
                            "run": runNo,
                            "raspid": raspid,
                            "hostname": hostname,
                            "location": location
                        },
                        "time": iso,
                        "fields": {
                            "temp": temp,
                            "press": press,
                            "humi": hum,
                            "dew_point": dew_point,
                            "delta_t": delta_t
                        }
                    }
                ]

            print(json_body)

            res = client.write_points(json_body)
            print(res)
        else:
            print("Error: .get_sensor_data() or heat_stable failed.")
            break

        time.sleep(interval)

except KeyboardInterrupt:
    pass
