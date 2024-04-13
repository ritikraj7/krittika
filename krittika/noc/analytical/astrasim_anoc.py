import logging

from krittika.noc.krittika_noc import KrittikaNoC


class AstraSimANoC(KrittikaNoC):

    def __init__(self, network_config):
        self.cfg_contents = network_config.get_cpp_config()

        # TODO5REE: Too much repetition, move it to a logger class
        self.logging_level = logging.INFO
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

    def setup():
        # Write self.cfg_contents to a file
        # TODO5REE: Setup py binding to do these:
        #   - const auto network_parser = NetworkParser("../input/Ring.yml");
        #   - const auto topology = construct_topology(network_parser);
        pass

    def send(self, src, dest, chunk_size) -> int:
        # Potential wrapper around the below functions
        # TODO5REE: Decide if this is the best approach
        # For now return a magic number latency
        latency = 42

        # TODO5REE: Is this clks or ns?
        self.logger.info(
            f"Sending {chunk_size} bytes from {src} to {dest} took {latency}"
        )
        return latency

    def send_chunk(self, src, dest, chunk_size) -> int:
        # Send chunk_size data from src to dest
        # Returns latency of this txn
        # Simple for unaware, but aware won't be right unless we post txns
        pass

    def post_txn(self, src, dest, chunk_size) -> int:
        # Posts a chunk_size txn from src to dest
        # Returns a tracking ID for the txn
        # Internally registers this tracking ID with the txn Event to be sent
        pass

    def deliver_all_txns(self):
        # Simulates all the txns that need to be sent so latency can be arrived at
        pass

    def get_latency(self, tracking_id) -> int:
        # After delivery is done, query the latency of a txn using tracking_id
        pass
