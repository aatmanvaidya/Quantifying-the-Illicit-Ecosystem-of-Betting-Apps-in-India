import logging

COLORS = {
    'HEADER': '\033[95m',      # Purple/Magenta
    'DEBUG': '\033[96m',       # Cyan
    'INFO': '\033[94m',        # Blue
    'OKGREEN': '\033[92m',     # Green (not a standard level, but you can use it)
    'WARNING': '\033[93m',     # Yellow
    'ERROR': '\033[91m',       # Red
    'CRITICAL': '\033[91m',    # Red (often bold, but here same as ERROR)
    'ENDC': '\033[0m',         # Reset
}

class ColorFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        color = None
        if record.levelname == 'DEBUG':
            color = COLORS['DEBUG']
        elif record.levelname == 'INFO':
            color = COLORS['INFO']
        elif record.levelname == 'WARNING':
            color = COLORS['WARNING']
        elif record.levelname == 'ERROR':
            color = COLORS['ERROR']
        elif record.levelname == 'CRITICAL':
            color = COLORS['CRITICAL']
        # Optional: Handle custom "header" case via extra
        elif hasattr(record, 'color') and record.color == 'header':
            color = COLORS['HEADER']
        if color:
            message = f"{color}{message}{COLORS['ENDC']}"
        return message