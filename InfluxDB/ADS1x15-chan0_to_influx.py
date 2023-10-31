#!/usr/bin/env python

import time
import Adafruit_SSD1306
import Adafruit_ADS1x15
import board
from PIL import Image, ImageDraw, ImageFont
from influxdb import InfluxDBClient

# Set up InfluxDB client for Chan0
CHAN0_HOST = 'localhost'
CHAN0_PORT = 8086
CHAN0_USERNAME = 'Your_username'
CHAN0_PASSWORD = 'Your_Password'
CHAN0_DATABASE = 'Your_database'
CHAN0_MEASUREMENT = 'Your Mesurement'
chan0_client = InfluxDBClient(host=CHAN0_HOST, port=CHAN0_PORT, username=CHAN0_USERNAM, password=CHAN0_PASSWORD, database=CHAN0_DATABASE)

# Create an ADS1115 ADC (16-bit) instance.
adc = Adafruit_ADS1x15.ADS1115()

# ADC settings
REFERENCE_VOLTAGE = 5.0  # Reference voltage in volts
GAIN = 1

# Define conversion constants for chan0
VOLTAGE_MIN_CHAN0 = 0.0  # Minimum voltage value for CHAN0 sensor
VOLTAGE_MAX_CHAN0 = 5.1  # Maximum voltage value for CHAN0 sensor
CHAN0_MIN = 0  # Minimum CHAN0 concentration (parts per million)
CHAN0_MAX = 10000  # Maximum CHAN0 concentration (parts per million)

# Read CHAN0
def read_chan0_concentration():
    # Read the ADC conversion value.
    value = adc.read_adc(0, gain=GAIN)

    # Convert the ADC value to voltage.
    voltage = value / 32767.0 * REFERENCE_VOLTAGE

    # Map analog voltage to CHAN0.
    chan0_concentration = (voltage - VOLTAGE_MIN_CHAN0) / (VOLTAGE_MAX_CHAN0 - VOLTAGE_MIN_CHAN0) * (CHAN0_MAX - CHAN0_MIN) + CHAN0_MIN

    return chan0_concentration

# Read CHAN0
chan0_concentration = read_chan0_concentration()

# Adjust the CHAN0 concentration vaule by adding - or +
##chan0_concentration += 100

# Write CHAN0 to InfluxDB
chan0_data = [
    {
        'measurement': CHAN0_MEASUREMENT,
        'fields': {
            'chan0_concentration': chan0_concentration
        }
    }
]
chan0_client.write_points(chan0_data)

# Display the written data in the terminal
print("Data written to InfluxDB:")
print("CHAN0 Concentration: {:.0f} ppm".format(chan0_concentration))


# Clean up ADC
adc.stop_adc()
