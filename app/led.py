from gpiozero import PWMLED


class sensor:
    def __init__(self, pin):
        self.led = PWMLED(pin)
        return

    def on(self, value=1):
        self.led.value = value  # Full brightness unless told otherwise
        return

    def off(self):
        self.led.value = 0  # Off
        return
