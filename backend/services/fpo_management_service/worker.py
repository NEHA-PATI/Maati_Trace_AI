from __future__ import annotations

import logging
import time

from services.fpo_management_service.app.config import FpoManagementConfig
from services.fpo_management_service.app.service import process_batch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fpo_management_worker")


def main() -> None:
    config = FpoManagementConfig.from_env()
    logger.info("fpo_management_worker_started")
    while True:
        count = process_batch(config.worker_batch_size)
        if count == 0:
            time.sleep(config.worker_poll_seconds)


if __name__ == "__main__":
    main()
