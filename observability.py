# observability.py

import json
import logging
from typing import Any

logger = logging.getLogger("ticket_triage")


def log_agent_event(
    event: str,
    ticket_id: str,
    **fields: Any,
) -> None:
    """Write one structured, privacy-conscious log record."""
    record = {
        "event": event,
        "ticket_id": ticket_id,
        **fields,
    }

    logger.info(json.dumps(record, sort_keys=True, default=str))
