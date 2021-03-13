class Cache:
    """A naive in-memory cache implementation to store registered devices.
    Data is not persisted.
    """

    def __init__(self):
        self.data = {}

    def set(self, key, payload):
        self.data[key] = payload

    def get(self, key):
        return self.data.get(key, None)

    def clear(self):
        self.data = {}


cache = Cache()
