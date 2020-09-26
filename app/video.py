import subprocess
from threading import Thread
import logging
import logging.handlers
import json
from json_minify import json_minify
from typing import Dict
from pathlib import Path
import tzlocal
from datetime import datetime
import pytz
import os

from . import led

config: Dict = json.loads(json_minify(
    open(Path.home() / 'data' / 'config.json', 'r+').read()))['video']
logger = logging.getLogger('app.video')

def dispatch_thread(target, args=(), timeout=120, join=True):
    logger.debug(f'Dispatching thread: {target.__name__}')
    thread = Thread(target=target, args=args)
    thread.start()
    if join:
        thread.join()
    logger.info(f'Started thread: {target.__name__}')
    return thread

def record_audio():
    arecord = subprocess.run([
        "/usr/bin/arecord",
        "-D",
        "mic_mono",
        "-d",
        str(config['record_time']),
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
        str(Path.home() / 'data' / 'videos' / 'audio'),
    ],capture_output=True)

    #logging.debug(f'Arecord STDOUT: {arecord.stdout.decode()}')
    #logging.debug(f'Arecord STDERR: {arecord.stderr.decode()}')

def record_video():
    ffmpeg = subprocess.run([
        '/usr/bin/ffmpeg',
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
        '-i',
        '/dev/video0',
        '-i',
        str(Path.home() / 'data' / 'videos' / 'audio'),
        '-c:a',
        'mp3',
        '-c:v',
        'copy',
        '-r',
        '25',
        "-timestamp",
        "now",
        "-t",
        str(config['record_time']),
        "-y",
        str(Path.home() / 'data' / 'videos' / str(config['file1_name']))
    ],capture_output=True)

    #logging.debug(f'ffmpeg STDOUT: {ffmpeg.stdout.decode()}')
    #logging.debug(f'ffmpeg STDERR: {ffmpeg.stderr.decode()}')

def main():
    light = led.sensor(17)

    light.on()

    dispatch_thread(record_audio, join=False)
    dispatch_thread(record_video)

    light.off()

    output = subprocess.run(
    [
        "/usr/bin/ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format_tags=creation_time",
        "-of",
        "default=nw=1:nk=1",
        "-i",
        str(Path.home() / 'data' / 'videos' / str(config['file1_name']))
    ],
    capture_output=True
    ).stdout.decode()

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
    output_file1 = Path.home() / 'data' / 'videos' / str(config['file1_name'])
    output_file2 = Path.home() / 'data' / 'videos' / config['file2_name']

    ffmpeg2 = subprocess.run(
        [
            "/usr/bin/ffmpeg",
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
        ],
        capture_output=True
    )
    
    #logging.debug(f'ffmpeg2 STDOUT: {ffmpeg2.stdout.decode()}')
    #logging.debug(f'ffmpeg2 STDERR: {ffmpeg2.stderr.decode()}')

    # ffmpeg 3rd pass to add BITC and flip video !
    output_file3 = (
        Path.home() / 'data' / 'videos' / ( filename + '_int.mp4' )
    )  # added _int to demark internal camera
    filter = (
        ('hflip, ' if config['hflip'] else '')
        + ('vflip, ' if config['vflip'] else '')
        + "drawtext=fontfile=" + config['font_path'] + ":fontsize="
        + str(config['font_size']) + ":text='%{pts\:localtime\:"
        + str(offset)
        + "\\:%Y %m %d %H %M %S}': fontcolor="
        + config['font_colour'] + "@1: x=10: y=10"
    )
    logger.debug("Using ffmpeg filter %s", filter)
    ffmpeg3 = subprocess.run(
        [
            "/usr/bin/ffmpeg",
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
        ],
        capture_output=True
    )

    #logging.debug(f'ffmpeg3 STDOUT: {ffmpeg3.stdout.decode()}')
    #logging.debug(f'ffmpeg3 STDERR: {ffmpeg3.stderr.decode()}')

    if ffmpeg3.returncode == 0:
        os.remove(output_file1)
        os.remove(output_file2)
        os.remove(Path.home() / 'data' / 'videos' / 'audio')

if __name__ == "__main__":
    main()
