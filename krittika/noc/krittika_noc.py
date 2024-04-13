from abc import ABC, abstractmethod


class KrittikaNoC(ABC):

    @abstractmethod
    def __init__(self, NetworkConfig):
        pass

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def send_chunk(self, src, dest, chunk_size) -> int:
        # Send chunk_size data from src to dest
        # Returns latency of this txn
        # Simple for unaware, but aware won't be right unless we post txns
        pass

    @abstractmethod
    def post_txn(self, src, dest, chunk_size) -> int:
        # Posts a chunk_size txn from src to dest
        # Returns a tracking ID for the txn
        # Internally registers this tracking ID with the txn Event to be sent
        pass

    @abstractmethod
    def deliver_all_txns(self):
        # Simulates all the txns that need to be sent so latency can be arrived at
        pass

    @abstractmethod
    def get_latency(self, tracking_id) -> int:
        # After delivery is done, query the latency of a txn using tracking_id
        pass
