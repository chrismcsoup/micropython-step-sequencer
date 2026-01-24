"""MPR121 diagnostic script to debug non-responsive channels"""
from machine import Pin, I2C
from lib.mpr121 import MPR121
import time

i2c = I2C(scl=Pin(39), sda=Pin(40))
mpr = MPR121(i2c, 0x5A)

# Optional: Try lower (more sensitive) thresholds for problem channels
# Uncomment to test with more sensitive settings for channels 6 and 7:
# mpr.set_thresholds(8, 4, electrode=6)
# mpr.set_thresholds(8, 4, electrode=7)

print("MPR121 Diagnostic - watching channels 6 & 7")
print("=" * 60)
print("Touch each pad and watch the filtered vs baseline values")
print("Touch is detected when filtered < baseline - touch_threshold")
print("Default thresholds: touch=15, release=7")
print("=" * 60)

while True:
    touched = mpr.touched()
    
    # Show all channels status
    touch_str = ""
    for i in range(12):
        if touched & (1 << i):
            touch_str += f"[{i:2d}]"
        else:
            touch_str += f" {i:2d} "
    
    print(f"Touch: {touch_str}")
    print("Ch  Filtered  Baseline  Delta  Status")
    print("-" * 42)
    
    for i in range(12):
        f = mpr.filtered_data(i)
        b = mpr.baseline_data(i)
        delta = b - f
        status = "TOUCH" if touched & (1 << i) else ""
        warning = " !! BAD" if b == 0 else ""
        print(f"{i:2d}    {f:4d}      {b:4d}    {delta:4d}   {status}{warning}")
    
    print("\n")
    time.sleep_ms(500)
