class Config:
    def __init__(self):
        self.log_level = 'INFO'
    
    def get(self, key, default=None):
        return default

config = Config()
