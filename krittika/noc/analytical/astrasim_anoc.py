import logging
import os

from krittika.noc.krittika_noc import KrittikaNoC
from dependencies.AstraSimANoCModel import sample_wrapper


class AstraSimANoC(KrittikaNoC):

    def __init__(self, network_config):
        self.cfg_contents = network_config.get_cpp_config()
        self.mapping_en = network_config.get_mapping_en()
        self.mapping_dict = network_config.get_logical_to_physical_mapping()

        # TODO5REE: Too much repetition, move it to a logger class
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

        self.logger.debug(f"Logical to Physical mapping enabled : {self.mapping_en} \n")
        if self.mapping_en:
            self.logger.debug(f"Logical to Physical mapping is : \n")
            for key, value in self.mapping_dict.items():
                self.logger.debug(f"Logical Core: {key} -> Physical Core : {value}\n")

        self.logger.debug(
            f"Contents of generated cpp cfg file are: \n{self.cfg_contents}"
        )

    def setup(self):
        file_name = os.path.abspath("krittika_anoc_cfg.yml")
        with open(file_name, "w") as f:
            f.write(self.cfg_contents)
            self.logger.debug(f"Cpp cconfig file contents are {self.cfg_contents}")
            self.logger.debug(f"Cpp config file written to {file_name}")

        file_path_str = file_name.encode("utf-8")
        sample_wrapper.py_noc_setup(file_path_str)

    def post(self, clk, src, dest, data_size) -> int:

        if self.mapping_en:
            physical_src = self.mapping_dict[src]
            physical_dest = self.mapping_dict[dest]
        else:
            physical_src = src
            physical_dest = dest

        t_id = sample_wrapper.py_add_to_EQ(clk, physical_src, physical_dest, data_size)
        self.logger.debug(
            f"Posting a txn from physical core {physical_src} to physical core {physical_dest} of size {data_size} with tracking ID {t_id}"
        )

        return t_id

    def deliver_all_txns(self):
        sample_wrapper.py_simulate_events()
        self.logger.debug(f"Delivering all txns")

    def get_latency(self, tracking_id) -> int:
        # TODO: Is this clks or ns?
        latency = sample_wrapper.py_get_latency(tracking_id)

        self.logger.debug(f"Txn with tracking ID {tracking_id} took {latency} clks")

        return latency

    def get_static_latency(self, src, dest, size) -> int:
        if self.mapping_en:
            physical_src = self.mapping_dict[src]
            physical_dest = self.mapping_dict[dest]
        else:
            physical_src = src
            physical_dest = dest
        
        return sample_wrapper.py_get_static_latency(physical_src, physical_dest, size)
