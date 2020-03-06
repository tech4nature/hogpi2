from threading import Thread
from logging import getLogger
from time import time
import json
from typing import Dict
from json_minify import json_minify
from pathlib import Path
import subprocess
import os

from . import pir, post, rfid, sftp, thermo, weight

config: Dict = json.loads(json_minify(
    open(Path.home() / 'data' / 'config.json', 'r+').read()))['hedge']
logger = getLogger(__name__)

pir_sensor = pir.sensor(11)
rfid_sensor = rfid.sensor(45)
thermo_sensor = thermo.sensor()
weight_sensor = weight.sensor()

def dispatch_thread(target, args = (), timeout = 120):
    thread = Thread(target=target, args=args)
    thread.start()
    thread.join(timeout=timeout)
    return thread

def run_weight(hog_id):
    data = weight_sensor.read()
    weight_sensor.avrg(data)
    post.weight(hog_id)


def run_video(hog_id):
    subprocess.run([Path.home() / '.pyenv' / 'versions' / '3.8.2' / 'bin' / 'python', Path.home() / 'app' / 'video.py'])
    post.video(hog_id)

def run_thermo():
    thermo_sensor.read()

def pull_videos():
    for ip in range(config['ip_min'], config['ip_max']):
        response = os.system("ping -c 5 " + config['ip_root'] + str(ip))
        if response == 0:
            sftp.pull_videos(config['ip_root'] + ip)


def main():
    if pir_sensor.read():
        hog_id = rfid_sensor.read()
        dispatch_thread(run_weight, args=(hog_id,))
        dispatch_thread(run_video, args=(hog_id,))

def hourly():
    dispatch_thread(pull_videos())


if __name__ == "__main__":
    last_ran = 0
    temp_last_ran = 0
    while True:
        try:
            main()

            if time() - last_ran > 3600:
                hourly()
                last_ran = time()

            if time() - temp_last_ran > config['temp_time']:
                dispatch_thread(run_thermo)
        except Exception as e:
            logger.error(e)
