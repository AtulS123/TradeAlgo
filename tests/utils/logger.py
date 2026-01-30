import logging

class MockLogger:
    def info(self, msg):
        print(f"INFO: {msg}")
    def error(self, msg):
        print(f"ERROR: {msg}")
    def warning(self, msg):
        print(f"WARNING: {msg}")
    def debug(self, msg):
        pass

logger = MockLogger()

def setup_logger(name="test"):
    return logger
