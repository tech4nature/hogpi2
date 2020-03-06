from datetime import datetime, timedelta
from datetime import timezone
from time import sleep, strftime
import numpy
import os
import glob
import logging
import json
from json_minify import json_minify
from typing import Dict
from pathlib import Path

from .data import Data, serialise

config: Dict = json.loads(json_minify(
    open(Path.home() / 'data' / 'config.json', 'r+').read()))['thermo']
logger = logging.getLogger(__name__)


class sensor:
    def __init__(self):
        # Sets up thermostat
        os.system("modprobe w1-gpio")
        os.system("modprobe w1-therm")

        global base_dir
        global temp_sensors
        global num_t_sensor
        temp_sensors = []
        base_dir = "/sys/bus/w1/devices/"
        for i in glob.glob(base_dir + "28*"):
            temp_sensors.append(i + "/w1_slave")
        num_t_sensor = len(temp_sensors)
        if num_t_sensor == 0:
            raise Exception

    def get_time(self):
        d = datetime.now(timezone.utc)
        x = d.strftime("%Y %m %d %H %M %S")
        logger.debug("Raw time: %s", d)
        logger.debug("Refined time: %s", x)
        return x

    def read_temp_raw(self, sensor):
        # Gets raw data off the thermostat
        f = open(sensor, "r")
        lines = f.readlines()
        f.close()
        return lines

    def read(self):
        # Refines the raw data to something readable
        a = []
        i = 0
        if config['invert_in_out']:
            i = 3
        for temp_sensor in temp_sensors:
            if config['invert_in_out']:
                i -= 2 # Decrease by 2 to make up for the increase
            i += 1
            lines = self.read_temp_raw(temp_sensor)
            t = self.get_time()
            while lines[0].strip()[-3:] != "YES":
                sleep(0.2)
                lines = self.read_temp_raw(temp_sensor)
            equals_pos = lines[1].find("t=")
            if equals_pos != -1:
                temp_string = lines[1][equals_pos + 2 :]
                temp_c = float(temp_string) / 1000.0
                logger.debug("Time: %s", t)
                if i == 1:
                    data_type = "temp_in"
                if i == 2:
                    data_type = "temp_out"
                data = Data(data_type, temp_c, t)
                json.dump(serialise(data), open(Path.home() / 'data' / (data_type + '.json')))
                a.append(data)
        return a
