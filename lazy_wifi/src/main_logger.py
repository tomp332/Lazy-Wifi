import logging
from pathlib import Path


class MainLogger:
    def __init__(self, context):
        logging.basicConfig(filemode='a',
                            filename=f"{Path(context.logs_directory, 'main_log.log')}",
                            format='%(asctime)s %(message)s',
                            level=context.log_level)
        self.main_logger = logging
