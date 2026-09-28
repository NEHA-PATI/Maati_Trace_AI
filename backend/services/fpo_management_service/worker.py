from __future__ import annotations

import logging
import time

from services.fpo_management_service.app.config import FpoManagementConfig
from services.fpo_management_service.app.service import process_batch, process_document_scan_batch, fpo_process_report_jobs
from services.fpo_management_service.app.class_b import process_import_jobs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fpo_management_worker")


def main() -> None:
    config = FpoManagementConfig.from_env()
    logger.info("fpo_management_worker_started")
    while True:
        count = process_batch(config.worker_batch_size)
        count += process_import_jobs(config.worker_batch_size)
        count += process_document_scan_batch(config.worker_batch_size)
        count += fpo_process_report_jobs(config.worker_batch_size)
        if count == 0:
            time.sleep(config.worker_poll_seconds)


if __name__ == "__main__":
    main()
