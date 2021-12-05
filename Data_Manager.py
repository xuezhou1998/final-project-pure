from Site import Site

import Constant


class Data_Manager:
    def __init__(self) -> None:
        self.site_dict = {}
        self.site_failures = {}
        self.site_failure_times = {}
        for i in range(Constant.NUMBER_OF_SITES):
            site_instance = Site(i + 1)
            self.site_dict[i + 1] = site_instance
            self.site_failures[i + 1] = False
            self.site_failure_times[i + 1] = []
            self.site_failure_times[i + 1].append(-1)

    def is_site_failed(self, site_id):
        return self.site_failures[site_id]

    def get_site_instance(self, site_id):
        return self.site_dict[site_id]

    def read_only_non_replicated_read(self, variable_id, time_stamp, site_id):
        curr_site = self.get_site_instance(site_id)
        history = curr_site.vartable[variable_id]
        for i in reversed(range(len(history))):

            if history[i].version <= time_stamp:
                return history[i].value
        return -1

    def read_only_replicated_read(self, variable_id, time_stamp, site_id):
        curr_site = self.get_site_instance(site_id)
        history = curr_site.vartable[variable_id]
        for i in reversed(range(len(history))):

            if history[i].version > time_stamp:
                continue
            last_cmmt_time_bf_start = history[i].version
            if self.is_always_up(last_cmmt_time_bf_start, time_stamp, site_id):
                return history[i].value
            break
        return -1

    def is_always_up(self, last_cmmt_time_bf_start, start_time, site_id):
        failed_time = self.site_failure_times[site_id]

        for i in range(len(failed_time)):

            crr_time = failed_time[i]
            if start_time > crr_time > last_cmmt_time_bf_start:
                return False
        return True

    def get_last_fail_time(self, site_id):
        failure_time_size = len(self.site_failure_times[site_id])
        self.data_mgr_db()  #############################################
        return self.site_failure_times[site_id][failure_time_size - 1]

    def write(self, variable_id, value, site_id, time_stamp):
        curr_site = self.site_dict[site_id]
        curr_site.write(variable_id, value, time_stamp)
        return 0

    def make_fail(self, site_id, time_stamp):
        curr_site = self.get_site_instance(site_id)
        curr_site.site_fail()
        self.site_failures[site_id] = True
        self.site_failure_times[site_id].append(time_stamp)
        return 0

    def recover_site(self, site_id, time_stamp):
        curr_site = self.get_site_instance(site_id)
        # failure_time_size = len(self.site_failure_times[site_id])
        # curr_site.site_recover(time_stamp, self.site_failure_times[site_id][failure_time_size - 1])
        curr_site.site_recover(time_stamp, self.site_failure_times[site_id][-1])
        self.site_failures[site_id] = False
        return 0

    def get_site_variable_value(self, site_id, variable_id):
        curr_site = self.get_site_instance(site_id)
        return curr_site.get_value(variable_id)

    def get_recovery_time(self, site_id):
        self.data_mgr_db()  #############################################
        return self.get_site_instance(site_id).recover_time

    def release_site_locks(self, transaction_id, site_id):
        if self.is_site_failed(site_id) != True:
            curr_site = self.get_site_instance(site_id)
            curr_site.release_lock(transaction_id)
            curr_site.site_db()  #########################################
        else:
            pass
        return 0

    def data_mgr_db(self, site_arg=None):
        if site_arg != None:
            site_arg.recover_time
