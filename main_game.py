#!/usr/bin/env python

import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler

from game_board import GameBoard


def dev_logger():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s|%(levelname)s : %(message)s",
        datefmt="%Y-%m-%d|%H:%M:%S",
    )
    logging.getLogger("asyncio").setLevel(logging.INFO)
    logging.getLogger("websockets").setLevel(logging.INFO)


def logger():
    log_name = "/tmp/bomberman.log"
    handler = RotatingFileHandler(log_name, maxBytes=5 * 1024 * 1024, backupCount=1)
    logging.basicConfig(level=logging.INFO,
                        handlers=[handler],
                        format="%(asctime)s|%(levelname)s : %(message)s",
                        datefmt="%Y-%m-%d|%H:%M:%S")


IP = "localhost"
PORT = 5678


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "-d":
        dev_logger()
    else:
        logger()

    loop = asyncio.get_event_loop()
    game_board = GameBoard()
    start_server = game_board.create_server(IP, PORT)
    try:
        logging.info("Start")
        loop.create_task(game_board.game_loop())
        loop.run_until_complete(start_server)
        loop.run_forever()

    except KeyboardInterrupt:
        loop.call_soon_threadsafe(loop.stop)
        logging.warning("Caught keyboard interrupt. Stopping Server...")


if __name__ == "__main__":
    main()
