import subprocess
from pathlib import Path
import json
from json_minify import json_minify
import os

config = json.loads(json_minify(
    open(Path.home() / 'data' / 'config.json', 'r+').read()))['sftp']

def pull_videos(ip):
    subprocess.run(
        [
            "rsync",
            f"pi@{ip}:/home/pi/data/videos/*",
            "--remove-source-files",
            "-avz",
            Path.home() / 'data' / 'videos'
        ]
    )

    if config['pull_remote_cam_logs']:
        try:
            os.mkdir(Path.home() / 'data' / 'logs' / ip)
        except:
            pass

        subprocess.run(
            [
                "rsync",
                f"pi@{ip}:/home/pi/remoteCam.log",
                "-avz",
                Path.home() / 'data' / 'logs' / ip
            ]
        )
