import logging

from . import pir, rfid, thermo, video, weight

logger = logging.getLogger(__name__)
weight_sensor = weight.sensor()

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
    rfid_sensor = rfid.sensor(45)
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

    main()

if __name__ == "__main__":
    FORMAT = '%(levelname)s %(name)s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)

    main()
