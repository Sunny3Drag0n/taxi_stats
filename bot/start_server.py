from taxi_stats.rest_server import Server
import logging, sys, yaml


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.DEBUG,
        stream=sys.stdout,
    )
    config_file = "configs/server.yml"

    with open(config_file, "r") as file:
        config = yaml.safe_load(file)

    server = Server()
    server.run(host=config["rest_server"]["host"], port=config["rest_server"]["port"])
