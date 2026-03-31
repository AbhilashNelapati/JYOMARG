import logging
import sys

def get_sys_logger(name: str):
    """
    Centralized logger for the JYOMARG Hybrid AI backend.
    Enables tracking of Provider fallbacks, JSON failures, and general system health.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(levelname)s] %(asctime)s - %(name)s - %(message)s', 
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# Global instance for easy importing
log = get_sys_logger("JYOMARG-AI")
