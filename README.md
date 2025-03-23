# Micro Step Sequencer (WIP)

MCU: https://www.waveshare.com/wiki/ESP32-S3-Matrix


# Micropython Project Template

This is my personal micropython project template. But you are welcome to use and adapt it for your own projects. At the moment this is a work in progress, and although I am doing software development for a long time, I am still quite new to micropython. So I am trying to figure out a project template that fullfills the objectives.

## Objectives

* great developer experience / ease of use
* reproducable environment/builds
* automated testing
* easy deployment to the microcontroller
* easy debugging

## Tech stack and tools I use 

I develop micropython code on my macbook. While the docs reflect the mac specific settings/installation procedures the tools I use are platform independent and should run on Linux and Windows as well. 

### General Tools
I use the following tools for most software development projects (not specifically micropython):

- [uv](https://docs.astral.sh/uv/) for managing "normal" python environments and dependencies (even though we want to code micropython we still need a normal python for some tools)
- [homebrew](https://brew.sh/) for installing micropython and other global software packages on my macbook
- [vscode](https://code.visualstudio.com/) as my code editor
- [mise-en-place](https://mise.jdx.dev/) I use it here for task management only (this tool is highly recommended for ALL software development projects)


### Micropython specific tools

- [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) for copying files to the micropython device and executing files on it
- [micropython-stubs](https://github.com/Josverl/micropython-stubs) for autocompletion and type checking in vscode
- [Micropython unittest](https://github.com/micropython/micropython-lib/blob/master/python-stdlib/unittest/unittest/__init__.py) for testing micropython code in a desktop micropython environment (not as fully fledged as the normal python unittest module but it gets the job done and I am very glad that it exists)
- that's all for the moment, more to come...


## Create a micropython project

We need a project directory (the next steps will basically create a very similar project you see here in this repo). 

```bash
mkdir myproject
cd myproject
```
## Developing micropython

For several tools around micropython development, we also need a normal python installation. I use uv for this. 

```bash
# Install uv globally
brew install uv

# NOTE make sure you are in the project directory if you aren't already
cd myproject

# Creates a new project
uv init 

# Install the virtual python environment so that we don't mess up our system python
uv venv

# In case we have an existing project wich already hase some python dependencies in the pyproject.toml file
# we can install them with
uv sync
```

### Code autocomplete and type checking in vscode

To have nice autocompletion and type checking in vscode we can use the `micropython-unix-stubs` package.

```bash

# Check the version of micropython
$ micropython --version
MicroPython v1.24.1 on 2024-11-29; darwin [GCC 4.2.1] version

# Install the micropython-unix-stubs package
# the version should match with your micropython version
$ uv add --dev micropython-unix-stubs==1.24.1.post2
```

### Code linting and formatting

For code formatting and linting we use `ruff`. 

```bash
# Install the ruff package
uv add --dev ruff

# We can check the code with
ruff check
```



## Unittesting with micropython

This approach should help to build code/libraries for micropython that do not depend on 
specific hardware and can be tested in a desktop environment.

The idea is to use the micropython `unittest` module to test the library in a micropython desktop environment.

1) Install micropython so that it is available in the command line.
2) Create a test file that imports the code to test and defines some test methods.
3) Run the test file with micropython.



### Install micropython on the computer

On macOS we can use homebrew to easily install micropython. 

I don't know how to install it on other systems but you can definitely build it yourself for Linux and Windows if there is no more convenient way. See [text](https://docs.micropython.org/en/latest/develop/gettingstarted.html#building-the-unix-port-of-micropython)

```bash

# NOTE: this is micropython for your laptop to run micropython code without a microcontroler.
# To run the code on your microcontroller you need to install micropython on the microcontroller itself. 
# Docs for this are in the micropython documentation at https://docs.micropython.org/)
# Also, if you don't want to test/run your micropython code "locally" on your computer, 
# you don't need to install micropython on your computer just on the microcontroller.

# Micropython for macOS using homebrew 
brew install micropython
```


### Install the unittest module

Because the unittest module should test the micropython code with the micropython interpreter, we need to install the `unittest` module in the micropython environment and **NOT** in the "normal" python environment with ~~uv add~~.

```bash
# create a directory for the micropython libraries that we don't need on the microcontroller 
# but just locally on our computer for development/testing
mkdir lib-dev

# install the unittest module in the lib-dev directory
micropython -m mip install unittest --target lib-dev
```

### Create some code

Let's create a simple function that we want to test.

```bash
mkdir src
touch src/mycode.py

```python
# src/mycode.py
def add(a, b):
    return a + b
```


### Create the test file

```bash
mkdir test
touch test/test_mycode.py
```

```python
# test/test_mycode.py
import sys
# add the dev libs with the unittest module to the python path
sys.path.append('lib-dev')
# also add our src code to the python path
sys.path.append('src')

import unittest
import mycode

class TestMyCode(unittest.TestCase):
    def test_add(self):
        self.assertEqual(mycode.add(1, 2), 3)

if __name__ == '__main__':
    unittest.main()
```

### Run the tests

```bash
micropython test/test_mycode.py
```


### If we want to only test a specific test case

**NOTE**: This is not working yet when you follow the steps above. But in this repo I have implemented it.

```bash
micropython test/test_mycode.py test_mycode.TestMyCode.test_add
```


## Deploying micropython code to the microcontroller

To be able to work with micropython microcontrollers like copying files to the device or executing files on it
we use the `mpremote` utility (a "normal" python package).

```bash
# Install the mpremote package
uv add --dev mpremote
```

mpremote does the heavy lifting for us. I just wrote a couple of helper tasks with mise to make common tasks easier. If you want to know what is behind those tasks, have a look at the mise.toml and loog for [tasks.<taskname>]. As said mise (https://mise.jdx.dev/) is a great tool for managing typical requirements of software development projects.

NOTE: Most of the deploy related tasks like (deploy_lib, run_local, run_mcu) need a 
microcontroller with micropython flashed connected to the computer.


```bash
$ mise tasks
Name        Description                                                    
clear_mcu   Deletes all files and folder on the connected MCU recursively. 
deploy_all  Deploy boot.py, main.py and libs to the MCU                    
deploy_lib  deploy the library to the device                               
format      Format the code                                                
lint        Lint the code                                                  
run_local   Run locally (computer)                                         
run_mcu     Run on connected microcontroller                               
test        Run the tests   

$ mise task run <taskname>
# e.g.
$ mise task run test

# or if there are no name conflicts the shortcut
$ mise <taskname>
# e.g.
$ mise test

# some tasks accept arguments (e.g. the run_loca and the run_mcu task)
mise run_local src/hello.py

```


## TODO

* create micropython package.json for the `mylib`