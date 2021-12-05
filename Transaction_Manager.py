# import typing_extensions
# from Data_Manager import Data_Manager
from Transaction import Transaction
from Site import Site
from Variable import Variable
import Constant


class Transaction_Manager:
    def __init__(self) -> None:
        self.time_stamp = 0
        # self.data_mgr = Data_Manager()
        self.trans_map = {}  ##integer: transaction
        self.site_failure_hist = {}
        self.site_instances = {}
        self.curr_failed_sites = {}
        for i in range(1, Constant.NUMBER_OF_SITES + 1):
            # self.site_failure_hist["Site{}".format(i)] = []
            self.site_instances[i] = Site(i)

    def get(self, trans_id):
        if trans_id not in self.trans_map.keys():
            raise Exception("The transaction %d does not exist" % trans_id)
        else:
            return self.trans_map[trans_id]  ############################

    def begin(self, trans_id):
        self.trans_init_checker(trans_id)
        curr_transaction = Transaction(self.time_stamp, False)
        self.trans_map[trans_id] = curr_transaction
        return True  ############################

    def begin_read_only(self, trans_id):
        self.trans_init_checker(trans_id)
        curr_transaction = Transaction(self.time_stamp, True)
        self.trans_map[trans_id] = curr_transaction
        return True  ############################

    def read(self, trans_id, variable_id):
        if not self.alive_checker(trans_id):
            return True
        else:
            curr_transaction = self.get(trans_id)
            if curr_transaction.blocked:
                return False
            if curr_transaction.aborted:
                return True
        if curr_transaction.read_only:
            for curr_site in self.site_instances.values():
                if not curr_site.fail:
                    if self.is_replicated_variable(variable_id) and (not curr_site.just_recovery):
                        curr_site.add_version_variable(self.time_stamp, variable_id)
                        var_value = curr_site.vartable[variable_id][-1]
                        print("Read out the variable : x{} = {}".format(variable_id, var_value))
                        curr_transaction.sites_accessed.add(curr_site)
                        return True
                    elif not self.is_replicated_variable(variable_id):
                        var_value = curr_site.vartable[variable_id][-1]
                        print("Read out the variable : x{} = {}".format(variable_id, var_value))
                        curr_site.add_version_variable(self.time_stamp, variable_id)
                        curr_transaction.sites_accessed.add(curr_site)
                        return True
        else:
            for curr_site in self.site_instances.values():
                if not curr_site.fail:
                    if self.is_replicated_variable(variable_id) and (not curr_site.just_recovery):
                        if curr_site.can_get_read_lock(trans_id, variable_id):
                            curr_site.add_read_lock(trans_id, variable_id, self.time_stamp)
                            var_value = curr_site.vartable[variable_id][-1]
                            print("Read out the variable : x{} = {}".format(variable_id, var_value))
                            curr_transaction.sites_accessed.add(curr_site)
                            # curr_site.add_version_variable(self.time_stamp, variable_id)
                            return True

                    elif not self.is_replicated_variable(variable_id):
                        if curr_site.can_get_read_lock(trans_id, variable_id):
                            curr_site.add_read_lock(trans_id, variable_id, self.time_stamp)
                            var_value = curr_site.vartable[variable_id][-1]
                            print("Read out the variable : x{} = {}".format(variable_id, var_value))
                            curr_transaction.sites_accessed.add(curr_site)
                            # curr_site.add_version_variable(self.time_stamp, variable_id)
                            return True
        self.block_trans(trans_id)
        print("Transaction T{} is blocked due to no sites available for read", trans_id)
        return False  #########################################

    def write(self, trans_id, variable_id, variable_value):
        if not self.alive_checker(trans_id):
            return True
        else:
            curr_transaction = self.get(trans_id)
            if curr_transaction.blocked:
                return False
            if curr_transaction.aborted:
                return True
        result = False
        for curr_site in self.site_instances.values():
            if not curr_site.fail:
                if curr_site.can_get_write_lock(trans_id, variable_id):
                    result = True
                    curr_site.add_write_lock(trans_id, variable_id, self.time_stamp)
                    curr_transaction.cache[variable_id] = variable_value
                    curr_transaction.sites_accessed.add(curr_site)

                    # curr_site.write(variable_id, variable_value, self.time_stamp)
                    ############ write to cache of trans ###############
        if not result:
            self.block_trans(trans_id)
            print("Transaction T{} is blocked due to no sites available for write", trans_id)
        return result  #########################

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
            return True
        else:
            for curr_site in list(curr_transaction.sites_accessed):
                # self.release_locks(trans_id, curr_site)
                if not curr_site.fail and (curr_site.last_fail_time < curr_site.recover_time < self.time_stamp):
                    curr_site.release_lock(trans_id)
                else:
                    return False
            for i in curr_transaction.cache.keys():
                variable_id = i
                variable_value = curr_transaction.cache[i]
                site_list = curr_transaction.sites[variable_id]
                for curr_site in site_list:
                    curr_site.write(variable_id, variable_value, self.time_stamp)

            self.unblock_trans(trans_id)
            self.trans_map.pop(trans_id)
        print("Transaction T%d committed." % trans_id)
        return True

    def dump(self):
        my_string = ""
        for i in range(1, Constant.NUMBER_OF_SITES + 1):
            curr_site = self.site_instances[i]
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

    # def get_read_lock(self, trans_id, variable_id, site_id):
    #     curr_site = self.site_instances[site_id]
    #     if curr_site.fail:
    #         return False
    #     # curr_site = self.data_mgr.get_site_instance(site_id)
    #     # if self.is_replicated_variable(variable_id) and curr_site.just_recovery:
    #     #     if curr_site.get_var_last_commited_time(variable_id) < self.data_mgr.get_last_fail_time(site_id):
    #     #         return False
    #     if curr_site.can_get_read_lock(trans_id, variable_id):
    #         curr_site.add_read_lock(trans_id, variable_id, self.time_stamp)
    #         return True
    #     else:
    #         curr_transaction = self.trans_map[trans_id]
    #         wait_id = curr_site.get_waiting_id(variable_id, trans_id)
    #         curr_transaction.waiting_for_trans_id = wait_id
    #         curr_transaction.blocked = True
    #     return False

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


#has some problem blow
    def abort_trans_multi(self, site_id):
        curr_site = self.site_instances(site_id)
        for trans_id in self.trans_map.keys():
            curr_transaction = self.trans_map[trans_id]

            if curr_site in curr_transaction.sites_accessed:
                self.abort_trans(trans_id)
        return 0
# read only trans may not need to be aborted when the site fails
######################### has some problem above

    def abort_trans(self, trans_id):
        curr_transaction = self.trans_map[trans_id]
        curr_transaction.aborted = True
        self.release_locks(trans_id, curr_transaction.sites_accessed)
        self.unblock_trans(trans_id)
        return 0

    def release_locks(self, trans_id, sites_accessed_set):
        if len(sites_accessed_set) == 0:
            return 0
        for curr_site in list(sites_accessed_set):
            curr_site.release_lock(trans_id)
        return 0

    def unblock_trans(self, trans_id):
        for curr_transaction in self.trans_map.values():
            if curr_transaction.waiting_for_trans_id == trans_id and curr_transaction.blocked:
                curr_transaction.blocked = False
                curr_transaction.waiting_for_trans_id = -1
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
        # self.data_mgr.recover_site(site_id, self.time_stamp)
        curr_site = self.site_instances(site_id)
        curr_site.site_recover(self.time_stamp, self.site_failure_hist[site_id][-1])
        print("Recover site %d successful at time stamp %s" % (site_id, str(self.time_stamp)))
        return True

    def fail(self, site_id):
        curr_site = self.site_instances(site_id)
        curr_site.site_fail(self.time_stamp)
        if curr_site not in self.site_failure_hist:
            self.site_failure_hist[site_id] = [self.time_stamp]
        else:
            self.site_failure_hist[site_id].append(self.time_stamp)

        self.curr_failed_sites[site_id] = curr_site
        self.abort_trans_multi(site_id)
        print("Site %d has failed" % site_id)
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
