# Copilot Instructions for MicroPython Step Sequencer

## Project Overview

This is a **MicroPython** project (NOT regular Python). The code runs on an ESP32-S3 microcontroller (Waveshare ESP32-S3-Matrix).

## Key Points

- **Language**: MicroPython - NOT CPython/regular Python
- **Target MCU**: ESP32-S3
- **Architecture**: Platform-independent business logic with Hardware Abstraction Layer (HAL)

## Running Tests

Tests are run using the **micropython** interpreter, NOT python:

```bash
# Using mise task runner (recommended)
mise test

# Or directly with micropython
micropython test/run_tests.py

# Run a specific test
micropython test/run_tests.py test_mylib.TestMyLib.test_add
```

**NEVER use `python` or `python3` to run tests** - always use `micropython`.

## Project Structure

- `src/lib/` - Platform-independent library code (chord_machine, mylib)
- `src/plat_mcu/` - MicroPython MCU-specific code (HAL implementation, boot.py, main.py)
- `src/plat_web/` - PyScript web implementation
- `src/plat_computer/` - Desktop Python implementation
- `lib/` - Third-party MicroPython libraries (deployed to MCU)
- `lib-dev/` - Development libraries (unittest for MicroPython, NOT deployed to MCU)
- `test/` - Test files (run with micropython)
- `docs/` - Documentation

## MicroPython Limitations

When writing code, remember MicroPython limitations:
- No `unittest.TestLoader` - use simple test runner pattern
- No `str.title()` method
- Limited standard library
- Memory constraints on MCU

## Deployment

```bash
# Deploy all files to MCU
mise deploy_all

# Deploy just libraries
mise deploy_lib

# Run a file on the MCU
mpremote run src/plat_mcu/main.py
```

## Hardware

- **8x8 NeoPixel Matrix**: Pin 14 (64 LEDs for chord visualization)
- **Touch Strip LED (WS2812)**: Pin 38 (25 LEDs above touch strip)
- **MPR121 Touch Strip**: I2C address 0x5A (12 capacitive touch pads)
- **MCP23017 I/O Expander**: I2C address 0x20 (buttons, encoder)
- **SSD1306 OLED Display**: 128x32 pixels
- **MIDI**: UART1 (TX pin 39, RX pin 40)
