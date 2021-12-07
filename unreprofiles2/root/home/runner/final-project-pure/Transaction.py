

















class Transaction:
    def __init__(self, start_time, read_only) -> None:
        self.blocked = False
        self.start_time = start_time
        self.aborted = False
        self.read_only = read_only
        self.snapshot = None
        if self.read_only == True:
            self.snapshot = {}

        self.sites_accessed = set()
        self.sites_accessed_table = {}
        self.cache = {}

        self.sites = {}
        self.waiting_for_trans_id = -1
