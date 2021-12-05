# import typing_extensions
from Data_Manager import Data_Manager
from Transaction import Transaction
from Site import Site
import Constant


class Transaction_Manager:
    def __init__(self) -> None:
        self.time_stamp = 0
        self.data_mgr = Data_Manager()
        self.trans_map = {}  ##integer: transaction
        self.site_instance = {}
        self.site_failure_hist = {}
        for i in range(1, Constant.NUMBER_OF_SITES + 1):
            self.site_instance[i] = Site(i)

    def get_site(self, site_id):
        return self.site_instance[site_id]

    def get_site_variable_value(self, site_id, variable_id):
        return self.get_site(site_id).get_value(variable_id)

    def get_last_failure_time(self, site_id):
        return self.get_site(site_id).last_fail_time

    def set_last_failure_time(self, site_id, time_stamp):
        self.get_site(site_id).last_fail_time = time_stamp

    def is_site_failed(self, site_id):
        return self.get_site(site_id).fail

    def get_transaction(self, trans_id):
        if trans_id not in self.trans_map.keys():
            raise Exception("The transaction %d does not exist" % trans_id)
        else:
            return self.trans_map[trans_id]

    def write_site(self, variable_id, variable_value, site_id):
        self.get_site(site_id).write(variable_id, variable_value, self.time_stamp)

    def release_site_locks(self, trans_id, site_id):
        self.get_site(site_id).release_lock(trans_id)

    def begin(self, trans_id):
        self.trans_init_checker(trans_id)
        curr_transaction = Transaction(self.time_stamp, False)
        self.trans_map[trans_id] = curr_transaction
        return True

    def begin_read_only(self, trans_id):
        self.trans_init_checker(trans_id)
        curr_transaction = Transaction(self.time_stamp, True)
        self.trans_map[trans_id] = curr_transaction
        return True

    def read(self, trans_id, variable_id):

        if (not self.alive_checker(trans_id)):
            return True
        curr_transaction = self.get_transaction(trans_id)
        if curr_transaction.aborted:
            return True
        if curr_transaction.blocked:
            return False
        if curr_transaction.read_only:
            return self.read_read_only(curr_transaction, variable_id)
        if variable_id in curr_transaction.cache.keys():
            variable_value = curr_transaction.cache[variable_id]
            print("X %s : %s" % (str(variable_id), str(variable_value)))
            return True
        if not self.is_replicated_variable(variable_id):
            site_id = variable_id % Constant.NUMBER_OF_SITES + 1
            if self.get_read_lock(trans_id, variable_id, site_id):
                # if site_id not in curr_transaction.sites_accessed:
                curr_transaction.sites_accessed.add(site_id)
                variable_value = self.get_site_variable_value(site_id, variable_id)
                print("X %s : %s" % (str(variable_id), str(variable_value)))
                return True
        else:
            # may need to add the restriction that just recovered site cannot read

            for i in range(1, Constant.NUMBER_OF_SITES + 1):
                # first check the restriction of just recovered site
                curr_site = self.get_site(i)
                if self.is_replicated_variable(variable_id) and curr_site.just_recovery:
                    if curr_site.get_var_last_commited_time(variable_id) < self.get_last_failure_time(i):
                        continue
                if self.get_read_lock(trans_id, variable_id, i):
                    curr_transaction.sites_accessed.add(i)
                    variable_value = self.get_site_variable_value(i, variable_id)
                    print("X %s : %s" % (str(variable_id), str(variable_value)))
                    return True
        return False

    def read_read_only(self, curr_transaction, variable_id):
        if self.is_replicated_variable(variable_id) == False:
            site_id = variable_id % Constant.NUMBER_OF_SITES + 1

            if self.is_site_failed(site_id) == True:
                return False
            else:
                variable_value = self.data_mgr.read_only_non_replicated_read(variable_id, curr_transaction.start_time,
                                                                             site_id)
                print("X %s : %s" % (str(variable_id), str(variable_value)))
                return True
        else:
            for i in range(1, Constant.NUMBER_OF_SITES + 1):
                if self.is_site_failed(i) == True:
                    continue
                curr_site = self.get_site(i)
                variable_value = self.data_mgr.read_only_replicated_read(variable_id, curr_transaction.start_time, i)
                if variable_value == -1:
                    continue
                else:
                    print("X %s : %s" % (str(variable_id), str(variable_value)))
                    return True
        return False

    def write(self, trans_id, variable_id, variable_value):

        if (not self.alive_checker(trans_id)):
            return True
        curr_transaction = self.get_transaction(trans_id)  ###########################
        if curr_transaction.aborted:
            return True
        if curr_transaction.blocked:
            return False

        if not self.is_replicated_variable(variable_id):
            site_id = variable_id % Constant.NUMBER_OF_SITES + 1
            if self.is_site_failed(site_id):
                return False
            curr_site = self.get_site(site_id)
            if curr_site.can_get_write_lock(trans_id, variable_id):
                curr_site.add_write_lock(trans_id, variable_id, self.time_stamp)
                curr_site.clear_wait_lock(trans_id, variable_id)
                curr_transaction.sites_accessed.add(site_id)
                curr_transaction.cache[variable_id] = variable_value
                curr_transaction.sites[variable_id] = [site_id]
                return True
            else:
                curr_site.add_write_lock(trans_id, variable_id, self.time_stamp)
                wait_id = curr_site.get_waiting_id(variable_id, trans_id)
                curr_transaction.waiting_for_trans_id = wait_id
                curr_transaction.blocked = True
                return False
        else:
            id_list = []
            should_be_blocked = False
            wait_id = -1
            for i in range(1, Constant.NUMBER_OF_SITES + 1):
                if self.is_site_failed(i):
                    continue
                curr_site = self.get_site(i)
                if not curr_site.can_get_write_lock(trans_id, variable_id):
                    should_be_blocked = True
                    wait_id = curr_site.get_waiting_id(variable_id, trans_id)
                id_list.append(i)
            if should_be_blocked:
                for id_item in id_list:
                    curr_site = self.get_site(id_item)
                    curr_site.add_wait_lock(trans_id, variable_id, self.time_stamp)
                curr_transaction.waiting_for_trans_id = wait_id
                curr_transaction.blocked = True
                return False
            else:
                for id_item in id_list:
                    curr_site = self.get_site(id_item)
                    curr_site.add_write_lock(trans_id, variable_id, self.time_stamp)
                    curr_transaction.sites_accessed.add(id_item)
                    curr_site.clear_wait_lock(trans_id, variable_id)
                curr_transaction.cache[variable_id] = variable_value
                curr_transaction.sites[variable_id] = id_list
                return True

    def block_trans(self, trans_id):
        curr_transaction = self.trans_map[trans_id]
        curr_transaction.blocked = True

    def end(self, trans_id):
        curr_transaction = self.trans_map[trans_id]
        if curr_transaction.blocked:
            return False
        if curr_transaction.aborted:
            print("Transaction T%d has been aborted." % trans_id)
            self.trans_map.pop(trans_id)
        else:
            print("Transaction T%d committed." % trans_id)
            for i in curr_transaction.cache.keys():
                variable_id = i
                variable_value = curr_transaction.cache[i]
                site_list = curr_transaction.sites[variable_id]
                for site_id_item in site_list:
                    self.write_site(variable_id, variable_value, site_id_item)
            for accessed_site_item in list(curr_transaction.sites_accessed):
                self.release_site_locks(trans_id, accessed_site_item)
            self.unblock_trans(trans_id)
            self.trans_map.pop(trans_id)
        return True

    def dump(self):
        my_string = ""
        for i in range(1, Constant.NUMBER_OF_SITES + 1):
            curr_site = self.get_site(i)
            my_string += str("site {} - ".format(i))
            table_keys = list(sorted(curr_site.vartable.keys()))
            for table_idx in range(len(table_keys)):
                variable_list = curr_site.vartable[table_keys[table_idx]]
                if variable_list[-1].get_version() == -1:
                    continue

                my_string += str(
                    "x{}: {}, ".format(str(table_keys[table_idx]), str(variable_list[-1].get_value())))
            my_string = my_string[:len(my_string) - 2]
            my_string += "\n"
        print(my_string)
        return True

    def get_read_lock(self, trans_id, variable_id, site_id):
        if self.is_site_failed(site_id):
            return False
        curr_site = self.get_site(site_id)
        # if self.is_replicated_variable(variable_id) and curr_site.just_recovery:
        #     if curr_site.get_var_last_commited_time(variable_id) < self.data_mgr.get_last_fail_time(site_id):
        #         return False
        if curr_site.can_get_read_lock(trans_id, variable_id):
            curr_site.add_read_lock(trans_id, variable_id, self.time_stamp)
            return True
        else:
            curr_transaction = self.trans_map[trans_id]
            wait_id = curr_site.get_waiting_id(variable_id, trans_id)
            curr_transaction.waiting_for_trans_id = wait_id
            curr_transaction.blocked = True
        return False

    def dead_lock_detect(self):

        trans_list = []
        if len(self.trans_map.keys()) == 0:
            print("No transactions now")
            return -2
        for i in self.trans_map.keys():
            trans_id_temp = i
            if trans_id_temp in trans_list:
                continue
            trans_list.clear()
            trans_list.append(trans_id_temp)
            curr_transaction = self.trans_map[trans_id_temp]
            while curr_transaction.waiting_for_trans_id != -1:
                if curr_transaction.waiting_for_trans_id in trans_list:
                    print("There is a deadlock.")
                    youngest_id = self.find_yongest(trans_list)
                    print("Transaction  T{} is aborted.".format(youngest_id))
                    self.abort_trans(youngest_id)
                    self.trans_map.pop(youngest_id)
                    return -1
                trans_list.append(curr_transaction.waiting_for_trans_id)
                curr_transaction = self.trans_map[curr_transaction.waiting_for_trans_id]
                # print("In while loop inside transaction manager, dead lock detection function")
        return 0

    def find_yongest(self, trans_id_list):
        youngest_id = -1
        youngest_time = -1
        for i in trans_id_list:
            curr_transaction = self.trans_map[i]
            if curr_transaction.start_time > youngest_time:
                youngest_id = i
                youngest_time = curr_transaction.start_time
        return youngest_id

    def abort_trans_multi(self, site_id):
        for i in self.trans_map.keys():
            curr_transaction = self.trans_map[i]
            if site_id in curr_transaction.sites_accessed:
                self.abort_trans(i)
        return 0

    def abort_trans(self, trans_id):
        curr_transaction = self.trans_map[trans_id]
        curr_transaction.aborted = True
        self.release_locks(trans_id, curr_transaction.sites_accessed)
        self.unblock_trans(trans_id)
        return 0

    def release_locks(self, trans_id, sites_accessed_set):
        if len(sites_accessed_set) == 0:
            return 0
        for site_item in list(sites_accessed_set):
            self.release_site_locks(trans_id, site_item)
        return 0

    def unblock_trans(self, trans_id):
        for t in self.trans_map.values():
            if t.waiting_for_trans_id == trans_id and t.blocked:
                t.blocked = False
                t.waiting_for_trans_id = -1
        return 0

    def trans_init_checker(self, trans_id):
        if trans_id in self.trans_map.keys():
            print("Transaction initialization successful.")
        return 0

    def alive_checker(self, trans_id):
        if trans_id not in self.trans_map.keys():
            # print("Transaction T{} is not alive.".format(trans_id) )
            return False
        # print("Transaction T{} is alive.".format(trans_id))

        return True

    def recover(self, site_id):
        self.get_site(site_id).site_recover(self.time_stamp, self.get_last_failure_time(site_id))
        print("Recover site %d successful at time stamp %s" % (site_id, str(self.time_stamp)))
        return True

    def fail(self, site_id):
        self.get_site(site_id).site_fail()
        self.set_last_failure_time(site_id, self.time_stamp)
        if site_id not in self.site_failure_hist.keys():
            self.site_failure_hist[site_id]=[self.time_stamp]
        else:
            self.site_failure_hist[site_id].append(self.time_stamp)
        self.abort_trans_multi(site_id)
        print("Has made site %d failed" % site_id)
        return True

    def is_replicated_variable(self, variable_id):
        if variable_id % 2 == 1:
            return False
        else:
            return True

    def trans_mgr_db(self):
        pass

# if __name__ == "__main__":
#     t = Transaction_Manager()
#     print(t.write(1, 2, 102))
