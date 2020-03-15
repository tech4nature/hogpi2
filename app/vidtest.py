from subprocess import run
from os import chdir
from pathlib import Path

if __name__ == "__main__":
    chdir(Path.home())
    run([Path.home() / '.pyenv' / 'versions' / '3.8.2' / 'bin' / 'python', '-m', 'app.video'])