#!/usr/bin/env python3

Reads database AQI under dev and puts all info to be displayed. Added ads1x15 support


import time
from datetime import datetime
from influxdb import InfluxDBClient
import adafruit_ssd1306
import Adafruit_ADS1x15
import board
from PIL import Image, ImageDraw, ImageFont
import subprocess

# Set up the OLED display
WIDTH = 128
HEIGHT = 32
BORDER = 5
I2C_ADDRESS = 0x3C
font = ImageFont.truetype('/usr/share/fonts/truetype/Arial.ttf', 14)
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=I2C_ADDRESS)
image = Image.new('1', (WIDTH, HEIGHT))
draw = ImageDraw.Draw(image)

# Set up the InfluxDB client
HOST = 'localhost'
PORT = 8086
USERNAME = 'user'
PASSWORD = 'pass'
DATABASE = 'AQI'
QUERY = 'SELECT * FROM dev ORDER BY time DESC LIMIT 1'


def calculate_dewpoint(temperature_f, humidity):
    # Calculate the dew point in Fahrenheit
    dew_point = temperature_f - ((100 - humidity) / 5)

    return dew_point


def main():
    # Connect to the InfluxDB server
    client = InfluxDBClient(host=HOST, port=PORT, username=USERNAME, password=PASSWORD, database=DATABASE)

    # Set up the ADS1115 ADC
    import Adafruit_ADS1x15
    adc = Adafruit_ADS1x15.ADS1115()

    while True:
        try:
            # Read the analog channel 0 on the ADS1115
            channel_0 = adc.read_adc(0, gain=1) + 15

            # Query the database
            result = client.query(QUERY)
            points = result.get_points()

            # Parse the data and format it for display
            data = {}
            for point in points:
                temperature_f = point['temp']
                humidity = point['humi']
                air_pressure = point['press']
                iaq = point['iaq']
#                humbaseline = point['humbaseline']

                data['Dew Point'] = str(round(calculate_dewpoint(temperature_f, humidity))) + 'F'
                data['Temp'] = str(round(temperature_f)) + 'F'
                data['Humidity'] = str(round(humidity)) + '%'
                data['Air Pressure'] = str(round(air_pressure)) + 'hPa'
                data['IAQ'] = str(round(iaq))
#                data['HumBaseline'] = str(round(humbaseline)) + '%'

            # Add the result of channel 0 to the data dictionary
            data['M2'] = str(channel_0)

            # Clear the display
            draw.rectangle((0, 0, WIDTH, HEIGHT), outline=0, fill=0)

            # Cycle through the data and display on the OLED
            x = BORDER
            y = BORDER
            for key, value in data.items():
                text = '{}: {}'.format(key, value)
                draw.text((x, y), text, font=font, fill=255)
                y += font.getsize(text)[1] + 4
                if y > HEIGHT - font.getsize(text)[1] - 4:
                    y = BORDER
                    oled.image(image)
                    oled.show()
                    time.sleep(5)
                    draw.rectangle((0, 0, WIDTH, HEIGHT), outline=0, fill=0)

            # Display the data on the OLED
            oled.image(image)
            oled.show()

            # Check if IAQ is below 50
            if iaq < 50:
                # Execute the script
                subprocess.Popen(["python3", "/home/pi/buzz.py"])

            # Wait before refreshing the display
            time.sleep(5)

        except KeyboardInterrupt:
            # Exit the script if the user presses Ctrl-C
            break

    # Clean up the GPIO pins and exit
    oled.fill(0)
    oled.show()
    print('Exiting...')
    client.close()


if __name__ == '__main__':
    main()