from configparser import ConfigParser


class NetworkConfig:
    def __init__(self):

        # Default class members
        self.SUPPORTED_TOPOLOGIES = ["RING", "FULLYCONNECTED", "SWITCH"]

    def read_network_config(self, filename):
        cfg = ConfigParser()
        cfg.read(filename)

        # TODO5REE: Define the different sections

    def write_default_config(self):
        # TODO5REE: Define this default config
        pass


if __name__ == "__main__":
    obj = NetworkConfig()
    obj.write_default_config()
