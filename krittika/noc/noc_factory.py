from krittika.noc.analytical.astrasim_anoc import AstraSimANoC
from enum import Enum


class SupportedNoCTypes(Enum):
    AstraSimANoC = "AstraSimANoC"


class NoCFactory:

    @staticmethod
    def get_noc(noc_type, NetworkConfig):
        if noc_type == SupportedNoCTypes.AstraSimANoC.value:
            return AstraSimANoC(NetworkConfig)
        else:
            raise ValueError(
                "Unsupported NoC type is being constructed by the NoC factory!"
            )
