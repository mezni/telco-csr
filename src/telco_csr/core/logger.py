import logging
import time
from functools import wraps

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("telco_csr.intent_router")


def log_intent_metrics(func):
    """Decorator to log telemetry metrics for Node A execution."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        state = args[0] if args else kwargs.get("state", {})
        query = state.get("latest_user_message", "")

        logger.info(f"Incoming query for classification: '{query}'")

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            logger.info(
                f"Intent classified successfully | "
                f"Intent: {result.get('current_intent')} | "
                f"Confidence: {result.get('router_confidence', 0.0):.2f} | "
                f"Latency: {duration:.3f}s"
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Intent classification failed after {duration:.3f}s | Error: {str(e)}"
            )
            raise e

    return wrapper
