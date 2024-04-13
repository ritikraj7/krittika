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

            # TODO:
            #   - Setup a py binding that does the setup part

    def post(self, src, dest, data_size) -> int:
        MAGIC_TRACKING_ID = 5

        self.logger.debug(
            f"Posting a txn from {src} to {dest} of size {data_size} with tracking ID {MAGIC_TRACKING_ID}"
        )

        # TODO:
        #   - Setup a pybinding that sends if unaware and schedules an event if aware
        #   - Decide who populates and stores the tracking ID

        return MAGIC_TRACKING_ID

    def deliver_all_txns(self):

        # TODO:
        #   - Setup the pybinding that does the !finished() {proceed()} loop

        self.logger.debug(f"Delivering all txns")

    def get_latency(self, tracking_id) -> int:

        # TODO:
        #   - Setup the pybinding that queries the tracking handler to get latency

        # TODO: Is this clks or ns?
        MAGIC_LATENCY = 42

        self.logger.debug(
            f"Txn with tracking ID {tracking_id} took {MAGIC_LATENCY} clks"
        )

        return MAGIC_LATENCY
