from configparser import ConfigParser
from enum import Enum
import logging
import os


class SupportedTopologies(Enum):
    RING = "Ring"
    FULLYCONNECTED = "FullyConnected"
    SWITCH = "Switch"


class NetworkConfig:
    def __init__(self):

        self.logging_level = logging.CRITICAL
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.logger.setLevel(self.logging_level)

        # To avoid adding multiple handlers
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(self.logging_level)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        # Init every param to empty lists to support multiple dims
        self.topology = []
        self.npus_count = []
        self.bandwidth = []
        self.latency = []

        self.congestion_aware = None

    def read_network_config(self, filename):

        self.logger.debug(f"Reading from cfg file at {os.path.abspath(filename)}")
        cfg = ConfigParser()
        cfg.read(filename)

        self.logger.debug(f"Sections found in cfg: {cfg.sections()}")

        # Populate the different sections
        self.topology = [
            item.strip()
            for item in cfg.get("Network Configuration", "topology").split(",")
        ]
        self.logger.debug(f"Topology read from cfg file is: {self.topology}")

        self.npus_count = [
            int(item.strip())
            for item in cfg.get("Network Configuration", "npus_count").split(",")
        ]
        self.logger.debug(f"NPUs Count read from cfg file is: {self.npus_count}")

        self.bandwidth = [
            float(item.strip())
            for item in cfg.get("Network Configuration", "bandwidth").split(",")
        ]
        self.logger.debug(f"Bandwidth read from cfg file is: {self.bandwidth}")

        self.latency = [
            float(item.strip())
            for item in cfg.get("Network Configuration", "latency").split(",")
        ]
        self.logger.debug(f"Latency read from cfg file is: {self.latency}")

        self.congestion_aware = cfg.getboolean(
            "Network Configuration", "congestion_aware"
        )
        self.logger.debug(
            f"Congestion Aware read from cfg file is: {self.congestion_aware}"
        )

        # Validate entries
        # TODO5REE: Add more validation checks
        for topo in self.topology:
            valid_topologies = {topology.value for topology in SupportedTopologies}
            if topo not in valid_topologies:
                self.logger.error(f"Invalid topology has been parsed: {topo}")
                self.logger.error(f"Valid options are: {valid_topologies}")
                raise ValueError(f"Invalid topology {topo}")
