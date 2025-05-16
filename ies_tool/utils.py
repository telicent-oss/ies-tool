import datetime as dt
import logging


def validate_datetime_string(func):
    """Decorator to validate ISO8601 datetime or date strings using the class's logger.
    Accepts full datetime with or without Z suffix for UTC,
    full date (YYYY-MM-DD), year-month (YYYY-MM), or year (YYYY).
    Explicit timezone specifications are not allowed.

    Args:
        func (Callable): Function that receives a datetime or date string.
    """
    def wrapper(self, time_string, *args, **kwargs):
        try:
            # Check for explicit timezone (not allowed)
            if '+' in time_string:
                raise ValueError("Explicit timezone specifications are not allowed - use Z for UTC")

            time_string = time_string.replace(" ", "T").rstrip("Z")
            #  Handle time formats
            if 'T' in time_string:
                dt.datetime.fromisoformat(time_string)
            else:
                # Try different date formats (no time component)
                if len(time_string) == 4:  # YYYY
                    dt.datetime.strptime(time_string, '%Y')
                elif len(time_string) == 7:  # YYYY-MM
                    dt.datetime.strptime(time_string, '%Y-%m')
                else:  # YYYY-MM-DD
                    dt.date.fromisoformat(time_string)
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
