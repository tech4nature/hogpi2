from threading import Thread
import logging
import logging.handlers
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
logger = logging.getLogger(__name__)

pir_sensor = pir.sensor(11)
rfid_sensor = rfid.sensor(config['rfid_timeout'])
thermo_sensor = thermo.sensor()
weight_sensor = weight.sensor()

def dispatch_thread(target, args = (), timeout = 120):
    logger.debug(f'Dispatching thread: {target.__name__}')
    thread = Thread(target=target, args=args)
    thread.start()
    logger.info(f'Started thread: {target.__name__}')
    thread.join(timeout=timeout)
    return thread

def run_weight(hog_id):
    logger.info('Running weight')
    weight_sensor.tare_weight()
    data = weight_sensor.read()
    weight_sensor.avrg(data)
    post.weight(hog_id)


def run_video(hog_id): 
    logger.info('Running video')
    os.chdir(Path.home())
    subprocess.run([Path.home() / '.pyenv' / 'versions' / '3.8.2' / 'bin' / 'python', '-m', 'app.video'], timeout=120)
    post.video(hog_id)

def run_thermo():
    logger.info('Running thermo')
    thermo_sensor.read()
    post.thermo()

def pull_videos():
    logger.info('Pulling videos')
    for ip in range(config['ip_min'], config['ip_max']):
        response = os.system("ping -c 5 " + config['ip_root'] + str(ip))
        logger.info(f'Found something at IP: {config["ip_root"] + str(ip)}')
        if response == 0:
            sftp.pull_videos(config['ip_root'] + str(ip))
    post.video("outside")

def main():
    weight_sensor.tare_no_save(config['tare_time'])
    if pir_sensor.read():
        logger.info("PIR Trigerred")
        hog_id = rfid_sensor.read()
        dispatch_thread(run_weight, args=(hog_id,))
        run_video(hog_id)

def hourly():
    logger.info('Running hourly loop')
    weight_sensor.tare_weight()
    dispatch_thread(pull_videos())


if __name__ == "__main__":
    handler = logging.handlers.RotatingFileHandler(
        filename="hedge.log", maxBytes=1024 * 1024 * 5, backupCount=5
    )
    logging.basicConfig(handlers=[handler], level=logging.DEBUG)

    last_ran = 0
    temp_last_ran = 0
    while True:
        try:
            main()

            if time() - last_ran > 3600:
                last_ran = time()
                hourly()

            if time() - temp_last_ran > config['temp_time']:
                temp_last_ran = time()
                dispatch_thread(run_thermo)

        except Exception as e:
            logger.error(e)
