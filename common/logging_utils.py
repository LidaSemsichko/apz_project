import logging
import sys


def configure_logging(service_name: str, instance_name: str | None = None) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s service=%(name)s %(message)s",
        stream=sys.stdout,
    )
    logger = logging.getLogger(service_name)
    if instance_name:
        logger = logging.LoggerAdapter(logger, {"instance_name": instance_name})
    return logger
