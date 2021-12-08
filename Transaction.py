


class Transaction:
    def __init__(self, read_only, start_time ) -> None:
        self.blocked = False
        self.start_time = start_time
        self.aborted = False
        self.read_only = read_only
        self.sites_accessed = set()
        self.sites_accessed_table = {}
        self.cache = {}
        self.sites = {}
        self.waiting_for_trans_id = -1
