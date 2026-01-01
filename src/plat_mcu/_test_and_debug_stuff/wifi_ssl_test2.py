# This version uses the microdot web framework to create a simple HTTPS server
# that already has a background task to update a NeoPixel LED color and another async task
# to handle incoming HTTPS requests to change the LED color.

import network
import ssl
import asyncio
from machine import Pin
from microdot import Microdot
from neopixel import NeoPixel


led_pin = Pin(14, Pin.OUT)  # set GPIO0 to output to drive NeoPixels
np = NeoPixel(led_pin, 64)  # create NeoPixel driver on GPIO0 for 2 pixels

# Brightness limit (5% to prevent LEDs from being too bright)
BRIGHTNESS = 0.05

# LED color state (shared between tasks) - NeoPixels use GRB ordering
led_color = [0, int(255 * BRIGHTNESS), 0]  # Default red at 5% brightness (GRB format)


# wlan = network.WLAN()       # create station interface (the default, see below for an access point interface)
# wlan.active(True)           # activate the interface
# wlan.scan()                 # scan for access points
# wlan.isconnected()          # check if the station is connected to an AP
# wlan.connect('ssid', 'key') # connect to an AP
# wlan.config('mac')          # get the interface's MAC address
# wlan.ipconfig('addr4')      # get the interface's IPv4 addresses

# Setup WiFi Access Point
ap = network.WLAN(network.WLAN.IF_AP)  # create access-point interface
ap.config(
    ssid="CH-ESP32-AP", key="12345678", security=3
)  # set the SSID of the access point, 3 means WPA2-PSK
ap.config(max_clients=3)  # set how many clients can connect to the network
ap.active(True)  # activate the interface

print("Connection successful")
print(ap.ifconfig())


# Create Microdot app
app = Microdot()


@app.route("/")
async def index(request):
    with open('lib/static/index.html', 'r') as f:
        html = f.read()
    return html, {"Content-Type": "text/html", "Connection": "close"}


@app.route("/set-color")
async def set_color(request):
    global led_color
    try:
        r = int(request.args.get('r', 0))
        g = int(request.args.get('g', 0))
        b = int(request.args.get('b', 0))
        
        # Update the global color state with brightness applied (GRB format)
        led_color[0] = int(g * BRIGHTNESS)  # Green
        led_color[1] = int(r * BRIGHTNESS)  # Red
        led_color[2] = int(b * BRIGHTNESS)  # Blue
        
        return {'status': 'ok', 'color': [r, g, b]}, {'Content-Type': 'application/json', 'Connection': 'close'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 400, {'Content-Type': 'application/json', 'Connection': 'close'}


# Configure SSL context for HTTPS
# NOTE: MicroPython requires DER format certificates, not PEM!
# Convert your certificates using:
#   openssl x509 -in cert.pem -out cert.der -outform DER
#   openssl rsa -in key.pem -out key.der -outform DER
sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
sslctx.load_cert_chain("lib/tls/cert.der", "lib/tls/key.der")


async def bg_loop():
    """Async task to update LED with current color"""
    while True:
        np.fill((0, 0, 0))
        np.write()
        np[0] = tuple(led_color)  # Set the first pixel to current color
        np.write()
        await asyncio.sleep(0.5)


async def run_webserver():
    """Main async function to run both tasks concurrently"""
    print("Starting HTTPS server on port 443...")
    # Start web server (this will run until stopped)
    await app.start_server(host="0.0.0.0", port=443, ssl=sslctx, debug=True)


async def main():
    """Main async function to run tasks concurrently"""
    # Run both tasks concurrently
    await asyncio.gather(bg_loop(), run_webserver())


# Run the async event loop
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Server stopped")
except Exception as e:
    print("Server error:", e)
