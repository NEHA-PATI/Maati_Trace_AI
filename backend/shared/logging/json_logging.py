import logging
import sys

from pythonjsonlogger import jsonlogger

from shared.config.settings import settings


def configure_json_logging(service_name: str) -> None:
    root = logging.getLogger()
    root.setLevel(settings.log_level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(service)s"
    )
    handler.setFormatter(formatter)

    root.handlers.clear()
    root.addHandler(handler)

    logging.getLogger(service_name).info(
        "logging_configured",
        extra={"service": service_name},
    )
