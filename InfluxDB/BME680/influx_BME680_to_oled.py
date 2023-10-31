from datetime import datetime
from influxdb import InfluxDBClient
import Adafruit_SSD1306
import board
from PIL import Image, ImageDraw, ImageFont
import subprocess
import time
import RPi.GPIO as GPIO

# Set up OLED display
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64
display = Adafruit_SSD1306.SSD1306_128_64(rst=None, i2c_address=0x3C)
display.begin()
display.clear()
display.display()
width = display.width
height = display.height
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)
font = ImageFont.truetype('/usr/share/fonts/truetype/Arial.ttf', 13)

# Set up InfluxDB client
HOST = 'localhost'
PORT = 8086
USERNAME = 'Your_UserName'
PASSWORD = 'Your_password'
DATABASE = 'Your_DB'
MEASUREMENT = 'Your_measurment'
QUERY = 'SELECT * FROM dev ORDER BY time DESC LIMIT 1'


def display_script_name(script_name):
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    text = " {}".format(script_name)
    x = int((width - font.getsize(text)[0]) / 2)
    y = int((height - font.getsize(text)[1]) / 2)
    draw.text((x, y), text, font=font, fill=255)
    display.image(image)
    display.display()
    time.sleep(3)

def main():
    client = InfluxDBClient(host=HOST, port=PORT, username=USERNAME, password=PASSWORD, database=DATABASE)

    while True:
        try:
            # Display script name
            display_script_name("Indoor Status")

            result = client.query(QUERY)
            points = result.get_points()

            data = {}
            for point in points:
                temperature_f = point['temp']
                humidity = point['humi']
                air_pressure = point['press']
                iaq = point.get('iaq', None)
                dew_point = point.get('dew_point', None)
                delta_t = point.get('delta_t', None)

                data['IAQ'] = str(round(float(iaq))) if iaq is not None else 'N/A'
                data['Temp'] = str(round(temperature_f)) + 'F'
                data['Humidity'] = str(round(humidity)) + '%' if humidity is not None else 'N/A'
                data['Air Pressure'] = str(round(air_pressure)) + 'hPa' if air_pressure is not None else 'N/A'
                data['Dew Point'] = str(round(dew_point)) + 'F' if dew_point is not None else 'N/A'
                data['Delta T'] = str(round(delta_t, 2)) + 'F' if delta_t is not None else 'N/A'

            draw.rectangle((0, 0, width, height), outline=0, fill=0)

            x = 5
            y = 5
            for key, value in data.items():
                text = '{}: {}'.format(key, value)
                draw.text((x, y), text, font=font, fill=255)
                y += font.getbbox(text)[3] + 4
                if y > height - font.getbbox(text)[3] - 4:
                    y = 5
                    display.image(image)
                    display.display()
                    time.sleep(10)
                    draw.rectangle((0, 0, width, height), outline=0, fill=0)

            display.image(image)
            display.display()

            # Display air pressure for 8 seconds
            time.sleep(8)

            iaq = float(data['IAQ']) if data['IAQ'] != 'N/A' else None
            temp = float(data['Temp'][:-1]) if data['Temp'] != 'N/A' else None

        except KeyboardInterrupt:
            break

    display.fill(0)
    display.display()
    print('Exiting...')
    client.close()
    GPIO.cleanup()

if __name__ == '__main__':
    main()
