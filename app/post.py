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
        if not numpy.isnan(weight.value[0]) and weight.value[0] > 100:
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

    weight_posted = json.load(open(Path.home() / 'data' / 'weight_posted.json', 'r'))

    os.chdir(Path.home() / 'data' / 'videos')
    new_videos = glob.glob("*.mp4")

    for new_video in new_videos:
        if (new_video != "1stPASS.mp4" and weight_posted) or 'ext' in new_video:
            logger.debug("Video moved to be posted")
            os.rename(
                Path.home() / 'data' / 'videos' / new_video,
                Path.home() / 'data' / 'toBePosted' / new_video
            )
        else:
            logger.info("Weight too low, video deleted")

            if config['backup_videos']:
                os.rename(
                    Path.home() / 'data' / 'videos' / new_video,
                    Path.home() / 'data' / 'finishedVideos' / (new_video.split(".mp4")[0] + "nw.mp4")
                )
            else:
                os.remove(Path.home() / 'data' / 'toBePosted' / new_video)

    os.chdir(Path.home() / 'data' / 'toBePosted')
    videos = glob.glob("*.mp4")

    for video in videos:
        strtime = video.split("_")[0]
        time = datetime.strptime(strtime, "%Y-%m-%d-%H-%M-%S-%z")
        time = time.astimezone(timezone.utc)  # timezone correction

        client.upload_video(
            config['box_id'], "hog-" + hog_id, Path.home() /
                              'data' / 'videos' / video, time
        )

        if config['backup_videos']:
            os.rename(
                Path.home() / 'data' / 'toBePosted' / video,
                Path.home() / 'data' / 'finishedVideos' / video
            )
        else:
            os.remove(Path.home() / 'data' / 'toBePosted' / video)
