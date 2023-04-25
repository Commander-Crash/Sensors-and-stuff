#!/usr/bin/env python

import time
import sys
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
import bme680

def get_dew_point(temperature, humidity):
        dew_point = (temperature - ((100 - humidity) / 5))
        dew_point_f = ((dew_point * 9/5) + 32)
        return dew_point_f
    
# Raspberry Pi pin configuration:
RST = 24
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

# Be sure to use the correct format for your LCD
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, i2c_address=0x3C)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Load nice silkscreen font
font = ImageFont.truetype('/usr/share/fonts/truetype/Arial.ttf', 12)

# BME680 Sensor
bme680_sensor = bme680.BME680(i2c_addr=0x77)


# Main loop
while True:
    # Read all the sensor data
    bme680_sensor.get_sensor_data()

    # Get the temperature and humidity
    temperature = bme680_sensor.data.temperature
    temperature_f = ((temperature * 9/5) + 32)
    humidity = bme680_sensor.data.humidity

    # Get the air pressure
    air_pressure = bme680_sensor.data.pressure

    # Calculate the dew point
    dew_point = get_dew_point(temperature, humidity)


    # Draw the text
    draw.text((x, top+1),    "Dew Point: " + str(round(dew_point)) + "F",  font=font, fill=200)
    draw.text((x, top+11),  "Temp: " + str(round(temperature_f)) + "F", font=font, fill=255)
    draw.text((x, top+24), "Humidity: " + str(round(humidity)) + "%", font=font, fill=255)
    draw.text((x, top+34), "Air Pressure: " + str(round(air_pressure)) + "hPa", font=font, fill=255)

    # Display image.
    disp.image(image)
    disp.display()
    time.sleep(3)

    # Clear the image
    draw.rectangle((0,0,width,height), outline=0, fill=0)

    time.sleep(1)