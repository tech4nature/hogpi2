import logging
from typing import Dict, List
from numpy import ndarray, sort, array, float, isnan
import json
from collections import deque
from pathlib import Path
from datetime import datetime
import time
from json_minify import json_minify

from .hx711 import HX711
from . import data

config: Dict = json.loads(json_minify(
    open(Path.home() / 'data' / 'config.json', 'r+').read()))['weight']
logger = logging.getLogger(__name__)


class sensor:
    def __init__(self):
        # Configure and initialise HX711

        self.hx: HX711 = HX711(5, 6)
        self.hx.set_reading_format("LSB", "MSB")
        self.hx.set_reference_unit(config['reference_unit'])  # TODO: Make Calibration Script
        self.hx.reset()

        self.last_ran = 0

    def tare_weight(self) -> None:
        tares = json.load(open(Path.home() / 'data' / 'tares.json', 'r+'))
        print(tares)
        tares = array(tares)
        print(tares)
        tares = sort(tares)
        print(tares)
        tares = tares[:int(len(tares) / 10 + 1)]
        print(tares)
        tare = tares.mean()
        logger.debug(tare)
        self.hx.OFFSET = tare * self.hx.REFERENCE_UNIT

    def tare_no_save(self, cycle_time) -> None:
        if self.last_ran + cycle_time < time.time():
            self.last_ran = time.time()
            old_offset = self.hx.OFFSET
            self.hx.tare()
            tares = json.load(open(Path.home() / 'data' / 'tares.json', 'r+'))
            tares = deque(tares, int(3600 / cycle_time))
            tares.append(self.hx.OFFSET / self.hx.REFERENCE_UNIT)
            print(tares)
            print(self.hx.OFFSET)
            open(Path.home() / 'tare.log', 'a+').write(
                f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, {self.hx.OFFSET / self.hx.REFERENCE_UNIT}g\n')
            self.hx.OFFSET = old_offset
            json.dump(list(tares), open(Path.home() / 'data' / 'tares.json', 'w'))

    def read(self, times: int = 10) -> data.Data:
        # Read and refine weight

        weights: List = []
        self.tare_weight()

        for i in range(times):
            weight: float = self.hx.get_weight()

            weight: float = float("%.2f" % weight)
            weights.append(weight)

        logger.debug(weights)
        weights: ndarray = array(weights).astype(float)
        weight: data.Data = data.Data("weight", weights)

        return weight

    @staticmethod
    def avrg(weight: data.Data) -> data.Data:
        weights: ndarray = weight.value
        weights: ndarray = sort(weights)

        logger.debug(weights)
        weights: ndarray = weights[
            : int((len(weights) / 100) * (100 - config["spike_cut"]))
        ]
        logger.debug(weights)
        max_value: float = weights[-1]
        min_cut: float = (max_value / 100) * config["min_percentile"]
        weights: ndarray = weights[weights > min_cut]
        logger.debug(weights)

        final_weight = data.Data(
            weight.data_type, [float("%.1f" % weights.mean())], weight.timestamp
        )

        if not isnan(final_weight.value[0]):
            data_as_dict: Dict = data.serialise(final_weight)

            weights_dict: List = json.load(
                open(Path.home() / 'data' / 'weights.json', "r")
            )

            weights_dict.append(data_as_dict)

            json.dump(weights_dict, open(
                Path.home() / 'data' / 'weights.json', "w")
            )

            return final_weight
