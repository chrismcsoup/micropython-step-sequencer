# this is a simple HTTPS server example for an ESP32 running MicroPython

import network
import socket
import ssl

# wlan = network.WLAN()       # create station interface (the default, see below for an access point interface)
# wlan.active(True)           # activate the interface
# wlan.scan()                 # scan for access points
# wlan.isconnected()          # check if the station is connected to an AP
# wlan.connect('ssid', 'key') # connect to an AP
# wlan.config('mac')          # get the interface's MAC address
# wlan.ipconfig('addr4')      # get the interface's IPv4 addresses

ap = network.WLAN(network.WLAN.IF_AP) # create access-point interface
ap.config(ssid='CH-ESP32-AP', key="12345678", security=3)              # set the SSID of the access point, 3 means WPA2-PSK
ap.config(max_clients=3)             # set how many clients can connect to the network
ap.active(True)                       # activate the interface

print('Connection successful')
print(ap.ifconfig())


def web_page():
  html = """<html><head><meta name="viewport" content="width=device-width, initial-scale=1"</head><body><h1>Hello, World!</h1></body></html>"""
  return html

with open('lib/tls/key.der', 'rb') as f:
    key = f.read()
with open('lib/tls/cert.der', 'rb') as f:
    cert = f.read()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 443))
s.listen(5)

while True:
  conn, addr = s.accept()
  print('Got a connection from %s' % str(addr))
  try:
    conn = ssl.wrap_socket(conn, server_side=True, key=key, cert=cert)
    request = conn.recv(1024)
    print('Content = %s' % str(request))
    response = web_page()
    conn.send(response)
  except OSError as e:
    print('Connection error:', e)
  finally:
    conn.close()
