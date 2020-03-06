import subprocess
from datetime import datetime
from time import strftime
import os
import sys
import logging
import pytz
import tzlocal
from pathlib import Path
import json
from json_minify import json_minify
from typing import Dict

from . import led

config: Dict = json.loads(json_minify(
    open(Path.home() / 'data' / 'config.json', 'r+').read()))['video']
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    irled = led.sensor(17)  # Instantiate led class and assign the pin the BCM17

    output_folder = Path.home() / 'data' / 'videos' # output folder
    output_file1 = output_folder / config['file1_name']

    # ffmpeg 1st Pass record
    irled.on()  # Turn led on

    arec = subprocess.Popen(
        [
            "arecord",
            "-D",
            "mic_mono",
            "-c1",
            "-r",
            "48000",
            "-f",
            "S32_LE",
            "-t",
            "wav",
            "-V",
            "mono",
            "-v",
            "audio",
        ],
        stdout=subprocess.PIPE,
    )
    ffmpeg1 = subprocess.Popen(
        [
            "ffmpeg",
            "-f",
            "v4l2",
            "-r",
            "25",
            "-video_size",
            "1280x720",
            "-pixel_format",
            "yuv422p",
            "-input_format",
            "h264",
            "-i",
            "/dev/video0",
            "-i",
            "audio",
            "-c:a",
            "mp3",
            "-c:v",
            "copy",
            "-r",
            "25",
            "-timestamp",
            "now",
            "-t",
            config['record_time'],
            "-y",
            output_file1,
        ],
        stdin=arec.stdout,
    )
    arec.stdout.close()  # pipe is already attached to ffmpeg1, and unneeded in this process
    ffmpeg1.wait()
    arec.terminate()
    irled.off()  # Turn led off

    # ffprobe to extract recording time and date and turn into offset seconds
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format_tags=creation_time",
        "-of",
        "default=nw=1:nk=1",
        "-i",
        output_file1,
    ]
    output = subprocess.check_output(command).decode("utf-8")
    logger.debug("Got output %s", output)

    local_timezone = tzlocal.get_localzone()  # get pytz tzinfo
    d = output[:-9]
    d = d.replace("-", " ").replace("T", " ").replace(":", " ")

    starttime = datetime.strptime(d, "%Y %m %d %H %M %S")
    local_time = starttime.replace(tzinfo=pytz.utc).astimezone(local_timezone)
    offset = local_time.timestamp()
    logger.debug("Computed date offset %s", offset)
    d = local_time.strftime("%Y %m %d %H %M %S %z")
    filename = d.replace(" ", "-")

    # ffmpeg 2nd pass to sync audio and video
    output_file2 = output_folder / config['file2_name']
    ffmpeg2 = subprocess.Popen(
        [
            "ffmpeg",
            "-i",
            output_file1,
            "-itsoffset",
            "00:00:00.4",
            "-i",
            output_file1,
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-map",
            "0:1",
            "-map",
            "1:0",
            "-y",
            output_file2,
        ]
    )
    ffmpeg2.wait()

    # ffmpeg 3rd pass to add BITC and flip video !
    output_file3 = (
        output_folder / (filename + "_int.mp4")
    )  # added _int to demark internal camera
    filter = (
        "drawtext=fontfile=" + config['font_path'] + ":fontsize=" + config['font_size'] + ":text='%{pts\:localtime\:"
        + str(offset)
        + "\\:%Y %m %d %H %M %S}': fontcolor=" + config['font_colour'] + "@1: x=10: y=10"
    )
    logger.debug("Using ffmpeg filter %s", filter)
    ffmpeg3 = subprocess.Popen(
        [
            "ffmpeg",
            "-i",
            output_file2,
            "-vf",
            filter,
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-c:a",
            "copy",
            "-r",
            "25",
            "-y",
            output_file3,
        ]
    )  # tried '-c:v', 'h264_omx', '-profile', '100'
    ffmpeg3.wait()

    # remove 1stPASS.mp4 and 2ndPASS.mp4 if ffmpeg3 is sucessful
    if ffmpeg3.returncode == 0:
        os.remove(output_file1)
        os.remove(output_file2)
        # os.remove("/home/pi/jackTest/audio")

    sys.exit()
