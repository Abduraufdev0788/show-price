import signal
import sys
import time

from config import settings
from database.connection import init_db
from scheduler.locks import ProcessLock
from scheduler.monitor import PriceSchedulerMonitor
from utils.logger import logger


def signal_handler(sig, frame):
    logger.info("Worker process stopping gracefully...")
    sys.exit(0)


def main():
    logger.info("Starting BTC AI Tracker Background Worker...")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Acquire lock
    lock = ProcessLock()
    if not lock.acquire():
        logger.error("Another worker instance is already active. Exiting.")
        sys.exit(1)

    try:
        # Verify database
        try:
            init_db()
            logger.info("Database connection established.")
        except Exception as e:
            logger.warning(f"Database init warning in worker: {e}")

        monitor = PriceSchedulerMonitor()
        monitor.start()
    finally:
        lock.release()
        logger.info("Worker lock released.")


if __name__ == "__main__":
    main()

