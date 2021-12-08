class Variable:
    def __init__(self, version, value ):

        self.version = version

        self.value = value
    def get_value(self):
        return self.value

    def get_version(self):
        return self.version
