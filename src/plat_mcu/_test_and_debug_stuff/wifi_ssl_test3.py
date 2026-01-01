# This is using websockets via https to control a NeoPixel LED on an ESP32 running MicroPython.
# It is a lot more responsive than the previous version using simple HTTP requests.

import network
import ssl
import asyncio
from machine import Pin
from microdot import Microdot
from microdot.websocket import with_websocket
from neopixel import NeoPixel
import json


led_pin = Pin(14, Pin.OUT)  # set GPIO0 to output to drive NeoPixels
np = NeoPixel(led_pin, 64)  # create NeoPixel driver on GPIO0 for 2 pixels

# Brightness limit (5% to prevent LEDs from being too bright)
BRIGHTNESS = 0.05

# LED color state (shared between tasks) - NeoPixels use GRB ordering
led_color = [0, int(255 * BRIGHTNESS), 0]  # Default red at 5% brightness (GRB format)
led_count = 1  # Number of LEDs to light up
blink_interval = 0.1 # Blink interval in seconds


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
    with open('lib/static/index_ws.html', 'r') as f:
        html = f.read()
    return html, {"Content-Type": "text/html; charset=utf-8", "Connection": "close"}


@app.route("/ws")
@with_websocket
async def ws_handler(request, ws):
    """WebSocket handler for real-time LED color updates"""
    global led_color, led_count, blink_interval
    try:
        while True:
            message = await ws.receive()
            try:
                data = json.loads(message)
                
                # Handle LED Blink interval update
                if 'blinkInterval' in data:
                    blink_interval = max(0.0, min(1.0, float(data['blinkInterval'])))
                    print('Updated blink interval to', blink_interval)
                    await ws.send(json.dumps({'status': 'ok', 'blinkInterval': blink_interval}))

                # Handle LED count update
                if 'ledCount' in data:
                    led_count = max(0, min(64, int(data['ledCount'])))
                    await ws.send(json.dumps({'status': 'ok', 'ledCount': led_count}))
                
                # Handle color update: {"r": 255, "g": 128, "b": 0}
                elif 'r' in data or 'g' in data or 'b' in data:
                    r = int(data.get('r', 0))
                    g = int(data.get('g', 0))
                    b = int(data.get('b', 0))
                    
                    # Update the global color state with brightness applied (GRB format)
                    led_color[0] = int(g * BRIGHTNESS)  # Green
                    led_color[1] = int(r * BRIGHTNESS)  # Red
                    led_color[2] = int(b * BRIGHTNESS)  # Blue
                    
                    await ws.send(json.dumps({'status': 'ok', 'color': [r, g, b]}))
                    
            except (ValueError, KeyError) as e:
                await ws.send(json.dumps({'status': 'error', 'message': str(e)}))
    except asyncio.CancelledError:
        print('WebSocket client disconnected')


# Configure SSL context for HTTPS
# NOTE: MicroPython requires DER format certificates, not PEM!
# Convert your certificates using:
#   openssl x509 -in cert.pem -out cert.der -outform DER
#   openssl rsa -in key.pem -out key.der -outform DER
sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
sslctx.load_cert_chain("lib/tls/cert.der", "lib/tls/key.der")


async def bg_loop():
    """Async task to update LED with current color"""
    last_count = led_count
    while True:
        # remove fast flickering when blink interval is 0
        if led_count != last_count or blink_interval > 0.0:
            np.fill((0, 0, 0))
            np.write()
            last_count = led_count
            
        await asyncio.sleep(blink_interval)
        # Set the specified number of pixels to current color
        for i in range(led_count):
            np[i] = tuple(led_color)
        np.write()
        await asyncio.sleep(blink_interval+0.01)


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
