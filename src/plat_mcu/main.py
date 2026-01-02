from sys import path


from time import sleep_ms
from lib.mylib import add

while True:
    print(f"1 + 2 = {add(1, 2)}")
    sleep_ms(1000)
