import logging
import tempfile

from krittika.noc.krittika_noc import KrittikaNoC
from dependencies.AstraSimANoCModel import sample_wrapper


class AstraSimANoC(KrittikaNoC):

    def __init__(self, network_config):
        self.cfg_contents = network_config.get_cpp_config()

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

        self.logger.debug(
            f"Contents of generated cpp cfg file are: \n{self.cfg_contents}"
        )

    def setup(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(self.cfg_contents)
            self.logger.debug(f"Cpp config file written to {f.name}")

            # FIXME:
            #   - Getting parsing errors when using generated topology
            file_path_str = f.name.encode("utf-8")
            file_path_str = "/home/hice1/mmanchali3/hml_proj_kritiika_final/commit_tree/krittika_hml_proj/dependencies/AstraSimANoCModel/input/Ring.yml".encode(
                "utf-8"
            )

            sample_wrapper.py_noc_setup(file_path_str)

    def post(self, clk, src, dest, data_size) -> int:
        t_id = sample_wrapper.py_add_to_EQ(clk, src, dest, data_size)

        self.logger.debug(
            f"Posting a txn from {src} to {dest} of size {data_size} with tracking ID {t_id}"
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
