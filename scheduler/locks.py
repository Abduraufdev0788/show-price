import fcntl
import os
from typing import Optional
from utils.logger import logger


class ProcessLock:
    def __init__(self, lock_file_path: str = "/tmp/btc_tracker_worker.lock"):
        self.lock_file_path = lock_file_path
        self._file: Optional[int] = None

    def acquire(self) -> bool:
        """Acquire exclusive process lock to prevent duplicate worker jobs."""
        try:
            self._file = os.open(self.lock_file_path, os.O_CREAT | os.O_RDWR)
            fcntl.flock(self._file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, BlockingIOError):
            logger.warning(f"Could not acquire lock on {self.lock_file_path}. Another worker is running.")
            return False

    def release(self) -> None:
        if self._file is not None:
            try:
                fcntl.flock(self._file, fcntl.LOCK_UN)
                os.close(self._file)
            except Exception as e:
                logger.error(f"Error releasing lock: {e}")
            self._file = None

