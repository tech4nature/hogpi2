import logging

from . import pir, rfid, thermo, video, weight
from pathlib import Path

logger = logging.getLogger(__name__)
weight_sensor = weight.sensor()
rfid_sensor = rfid.sensor()


def test_pir():
    pir_sensor = pir.sensor(11)
    try:
        while True:
            result = pir_sensor.read()
            if result == 1:
                print("PIR TRIGGERED")
                while True:
                    result = pir_sensor.read()
                    if result == 0:
                        print("PIR NOT TRIGGERED")
                        break
    except KeyboardInterrupt:
        main()


def test_rfid():
    logger.info('Please now insert the RFID sensor')
    logger.info(f'Got: {rfid_sensor.read()}')


def test_temp():
    thermo_sensor = thermo.sensor()
    thermo_sensor.read()


def test_video():
    video.main()


def test_tare_weight():
    weight_sensor.tare_weight()


def test_tare_no_save():
    weight_sensor.tare_no_save(300)


def test_weight():
    data = weight_sensor.read()
    weight_sensor.avrg(data)


def wipe_files():
    if input('Are you sure you want to do this, it will delete all log and data files! (yes): ').lower() != 'yes':
        return

    DATA = Path.home() / 'data'

    data_files = [
        DATA / 'tares.json',
        DATA / 'temp_in.json',
        DATA / 'temp_out.json',
        DATA / 'weights.json'
    ]

    for data_file in data_files:
        data_file.write_text('[]')

    for video in (DATA / 'videos').glob('*'):
        video.unlink()

    for video in (DATA / 'finishedVideos').glob('*'):
        video.unlink()

    for log in (DATA / 'logs').glob('*'):
        if log.is_dir():
            for log_file in log.glob('*'):
                log_file.unlink()
            log.rmdir()
        elif log.is_file():
            log.unlink()

    for log in Path.home().glob('*.log*'):
        log.unlink()



def main():
    test = input(
        """
    p=pir
    r=rfid
    t=temp
    tw=tare weight
    tns=tare no save
    v=video
    w=weight
    WIPE=wipe all data and logs
    """
    )

    if test == 'p':
        test_pir()

    elif test == 'r':
        test_rfid()

    elif test == 't':
        test_temp()

    elif test == 'tw':
        test_tare_weight()

    elif test == 'tns':
        test_tare_no_save()

    elif test == 'v':
        test_video()

    elif test == 'w':
        test_weight()

    elif test == 'WIPE':
        wipe_files()

    main()


if __name__ == "__main__":
    try:
        rfid_sensor.ser.write(b'sl0\r\n')

        FORMAT = '%(levelname)s %(name)s %(message)s'
        logging.basicConfig(format=FORMAT, level=logging.DEBUG)

        main()
    except:
        rfid_sensor.ser.write(b'sl4\r\n')
