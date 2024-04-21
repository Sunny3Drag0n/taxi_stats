from taxi_stats.server import Server


if __name__ == "__main__":
    server = Server()
    server.run(host="localhost", port=13337)
