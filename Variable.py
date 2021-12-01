class Variable:
    def __init__(self, value, version):
        self.value = value
        self.version = version

    def get_value(self):
        return self.value

    def get_version(self):
        return self.version
