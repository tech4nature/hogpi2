import json
from pathlib import Path
from typing import List, Dict
from json_minify import json_minify
import numpy
import os
import glob
from datetime import datetime, timezone
from logging import getLogger

from . import client, data

config: Dict = json.loads(json_minify(
    open(Path.home() / 'data' / 'config.json', 'r+').read()))['post']
logger = getLogger(__name__)


def weight(hog_id):
    logger.info("Posting weight")
    weights_json: Dict = json.load(open(Path.home() / 'data' / 'weights.json', "r"))
    weights: List = data.deserialise_many(weights_json)

    posted = False

    for weight in weights:
        if not numpy.isnan(weight.value[0]) and weight.value[0] > 5:
            client.create_weight(
                config['box_id'], "hog-" +
                hog_id, weight.value[0], weight.timestamp
            )
            posted = True

    if config['only_post_if_weight']:
        json.dump(posted, open(Path.home() / 'data' / 'weight_posted.json', 'w+'))

    json.dump([], open(Path.home() / 'data' / 'weights.json', "w"))


def thermo():
    logger.info("Posting Temp")
    temps_in = data.deserialise_many(json.load(
        open(Path.home() / 'data' / 'temp_in.json', "r")))
    temps_out = data.deserialise_many(json.load(
        open(Path.home() / 'data' / 'temp_out.json', "r")))

    for temp_in in temps_in:
        client.create_inside_temp(
            config['box_id'],
            temp_in.value[0], temp_in.timestamp
        )

    for temp_out in temps_out:
        client.create_outside_temp(
            config['box_id'],
            temp_out.value[0], temp_out.timestamp
        )

    json.dump([], open(Path.home() / 'data' / 'temp_in.json', "w"))
    json.dump([], open(Path.home() / 'data' / 'temp_out.json', "w"))


def video(hog_id):
    logger.info("Posting video")

    os.chdir(Path.home() / 'data' / 'videos')
    videos = [glob.glob(e) for e in ["*.mp4"]]
    weight_posted = json.load(open(Path.home() / 'data' / 'weight_posted.json', 'r'))

    for video in videos[0]:
        if (video != "1stPASS.mp4" and weight_posted) or 'ext' in video:
            strtime = video.split("_")[0]
            time = datetime.strptime(strtime, "%Y-%m-%d-%H-%M-%S-%z")
            time = time.astimezone(timezone.utc)  # timezone correction

            client.upload_video(
                config['box_id'], "hog-" + hog_id, Path.home() /
                'data' / 'videos' / video, time
            )
        else:
            logger.info("Weight wasn't posted, so video wasn't either")

        if config['backup_videos']:
            if not weight_posted and 'int' in video:
                os.rename(
                    Path.home() / 'data' / 'videos' / video,
                    Path.home() / 'data' / 'finishedVideos' / (video.split(".mp4")[0] + "nw.mp4")
                )
            else:
                os.rename(
                    Path.home() / 'data' / 'videos' / video,
                    Path.home() / 'data' / 'finishedVideos' / video
                )
        else:
            os.remove(Path.home() / 'data' / 'videos' / video)
