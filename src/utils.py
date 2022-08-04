import logging
from typing import Any


class DisableLogger:
    def __enter__(self):
        logging.disable(logging.CRITICAL)

    def __exit__(self, exception_type: Any, exception_value: Any, traceback: Any):
        logging.disable(logging.NOTSET)


class EmptyDebugLogger:
    def debug(self):
        pass
