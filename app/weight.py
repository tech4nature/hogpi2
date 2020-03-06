import logging
from typing import Dict, List
from numpy import ndarray, sort, array, float, isnan
import json
from collections import deque
from pathlib import Path
from json_minify import json_minify

from .hx711 import HX711
from . import data

config: Dict = json.loads(json_minify(
    open(Path.home() / 'data' / 'config.json', 'r+').read()))['weight']
logger = logging.getLogger(__name__)


class Sensor:
    def __init__(self):
        # Configure and initialise HX711

        self.hx: HX711 = HX711(5, 6)
        self.hx.set_reading_format("LSB", "MSB")
        self.hx.set_reference_unit(389)  # TODO: Make Calibration Script
        self.hx.reset()

    def tare_weight(self) -> None:
        tares = json.load(open(Path.home() / 'data' / 'tares.json', 'r+'))
        tares = array(tares)
        tares = tares[:int(len(tares) / 10)]
        tare = tares.mean()
        self.hx.OFFSET = tare

    def tare_no_save(self, cycle_time) -> None:
        old_offset = self.hx.OFFSET
        self.hx.tare()
        tares = json.load(open(Path.home() / 'data' / 'tares.json', 'r+'))
        tares = deque(tares, int(3600 / cycle_time))
        tares.append(self.hx.OFFSET)
        self.hx.OFFSET = old_offset
        json.dump(list(tares), open(Path.home() / 'data' / 'tares.json', 'w'))

    def read(self, times: int = 10) -> data.Data:
        # Read and refine weight

        weights: List = []

        for _ in range(times):
            weight: float = self.hx.get_weight()

            if weight < 0:
                weight: float = 0

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
            weights_dict: List = json.load(open(Path.home() / 'data' / 'weights.json', "r"))
            weights_dict.append(data_as_dict)
            json.dump(weights_dict, open(
                Path.home() / 'data' / 'weights.json', "w"))

            return final_weight
