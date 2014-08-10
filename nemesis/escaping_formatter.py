
import logging

class EscapingFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super(EscapingFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        msg = super(EscapingFormatter, self).format(record)
        # Newlines are the only thing known to have caused issues thus far
        escaped = msg.replace('\n', '\\n')
        return escaped
