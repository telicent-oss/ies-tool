import datetime as dt
import logging


def validate_datetime_string(func):
    """Decorator to validate ISO8601 datetime strings using the class's logger.

    Args:
        func (Callable): Function that receives a datetime string.
    """
    def wrapper(self, time_string, *args, **kwargs):
        try:
            # Adjusts for UTC 'Z' to '+00:00'
            dt.datetime.fromisoformat(time_string.replace('Z', '+00:00'))
        except ValueError as exc:
            # Using the logger from the class instance 'self'
            if hasattr(self, 'logger'):
                self.logger.error(f'invalid ISO8601 datetime string: {time_string}')
            raise RuntimeError(f'invalid ISO8601 datetime string: {time_string}') from exc
        return func(self, time_string, *args, **kwargs)
    return wrapper


def log_warning(message, category, filename, lineno, file=None, line=None):
    log = logging.getLogger("py.warnings")
    log.warning('%s:%s: %s:%s', filename, lineno, category.__name__, message)
