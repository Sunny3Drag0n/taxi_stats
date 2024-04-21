from taxi_stats.server import Server
import logging, sys


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.DEBUG,
        stream=sys.stdout,
    )
    server = Server()
    server.run(host="localhost", port=13337)
