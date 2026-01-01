# Test for the https://www.waveshare.com/wiki/0.91inch_OLED_Module
# Just a PoC for displaying a QR code with the WiFi AP credentials on the OLED display
# (no real wifi setup made in this file, see the wifi_ssl_test*.py files for that)

from sys import path
from uQR import QRCode
import time
path.append("lib")

# Display Image & text on I2C driven ssd1306 OLED display
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C  # type: ignore

WIDTH = 128  # oled display width
HEIGHT = 32  # oled display height


def display_wifi_ap_info(oled, ssid, password):
    """Display WiFi AP information with QR code and text on OLED display."""
    # Generate QR code for WiFi credentials
    micro_qr = QRCode(version=1)
    micro_qr.add_data('WIFI:S:{};T:WPA;P:{};H:false;;'.format(ssid, password))
    matrix = micro_qr.get_matrix()
    
    # Fill screen with white
    oled.fill(1)
    
    # Place QR code on the left, vertically centered
    qr_size = len(matrix)
    offset_x = 2  # Small margin from left edge
    offset_y = (HEIGHT - qr_size) // 2
    
    for y in range(qr_size):
        for x in range(qr_size):
            value = not matrix[y][x]  # Invert values because black is True in the matrix
            oled.pixel(x + offset_x, y + offset_y, value)
    
    # Add SSID and password text on the right
    text_x = qr_size + 6  # Position text after QR code with small gap
    oled.text("WiFi AP:", text_x, 1, 0)
    oled.text(ssid, text_x, 11, 0)
    oled.text(password, text_x, 21, 0)
    
    oled.show()


# Initialize I2C and OLED display
i2c = I2C(0, scl=Pin(1), sda=Pin(2))
print("I2C Address      : " + hex(i2c.scan()[0]).upper())
print("I2C Configuration: " + str(i2c))

oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)

# Display WiFi AP information
ssid, password = 'esp-ssid', '12345678'
display_wifi_ap_info(oled, ssid, password)

# Keep running until Ctrl-C is pressed
try:
    print("Display running. Press Ctrl-C to exit...")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nKeyboard interrupt received.")
except Exception as e:
    print("Exception occurred:", e)
finally:
    print("Shutting down display...")
    oled.fill(0)  # Clear display to black
    oled.show()
    print("Display off.")
