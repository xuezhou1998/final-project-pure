import Query_Parser
import os
from Transaction_Manager import Transaction_Manager


def main(input_path):

    is_file = os.path.isfile(input_path)


    is_directory = os.path.isdir(input_path)
    if is_file:
        main_file(input_path)
    elif is_directory:
        for filename in sorted(list(os.listdir(input_path))):
            if filename.endswith(".txt"):
                file_path = os.path.join(input_path, filename)
                print(
                    "#################################### {} #######################################".format(filename))
                main_file(file_path)
            else:
                continue


def main_file(input_file_path):

    trans_mgr = Transaction_Manager()
    cmmd_waitlist = []
    input_path = input_file_path
    exe_result, in_waitlist = False, False
    waitlist_idx = 0


    file_read = open(input_path, "r")
    print("file loaded")
    while True:

        fetched = None
        in_waitlist = False

        if len(cmmd_waitlist) > 0 and waitlist_idx < len(cmmd_waitlist):
            fetched = cmmd_waitlist[waitlist_idx]


            in_waitlist = True
        else:

            qry = file_read.readline()
            if 'Test' in qry:
                print(
                    "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%{}%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%".format(
                        qry))
            if len(qry) == 0:
                break
            if not ('(' and ')') in qry:
                continue
            if '//' in qry:
                if 'Test' in qry:
                    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%{}%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%".format(qry))
                qry = qry[:qry.index('//')]

            if qry is not None and qry != '\n' and qry.strip() != "":

                fetched = query_parser(qry)
            else:
                continue

        if fetched['op'] == 'begin':

            exe_result = trans_mgr.begin(int(fetched['trans_id/site_id']))
        elif fetched['op'] == 'beginRO':
            exe_result = trans_mgr.begin_read_only(int(fetched['trans_id/site_id']))
        elif fetched['op'] == 'R':
            exe_result = trans_mgr.read(int(fetched['trans_id/site_id']), int(fetched['variable_id']))
        elif fetched['op'] == 'W':
            exe_result = trans_mgr.write(int(fetched['trans_id/site_id']), int(fetched['variable_id']), int(fetched['variable_value']))
        elif fetched['op'] == 'recover':
            exe_result = trans_mgr.recover(int(fetched['trans_id/site_id']))
        elif fetched['op'] == 'fail':
            exe_result = trans_mgr.fail(int(fetched['trans_id/site_id']))
        elif fetched['op'] == 'dump':
            exe_result = trans_mgr.dump()
        elif fetched['op'] == 'end':
            exe_result = trans_mgr.end(int(fetched['trans_id/site_id']))
        pre_cmmd_waitlist_len = len(cmmd_waitlist)
        if exe_result == True:
            if in_waitlist == True:
                cmmd_waitlist.remove(cmmd_waitlist[waitlist_idx])
            waitlist_idx = 0
        else:
            if in_waitlist == False:
                cmmd_waitlist.append(fetched)
                print("Transaction T{} is waiting due to a lock conflict: {}".format(fetched['trans_id/site_id'], fetched))
                waitlist_idx = 0
            else:
                waitlist_idx += 1
        trans_mgr.time_stamp += 1
        deadlock_detection_result = trans_mgr.dead_lock_detect()

        if deadlock_detection_result == -2:
            print("===================================================================================================")
def query_parser(qry:str):
    qry_real = qry.strip()
    if '//' in qry:
        qry_real = qry[:qry.index('//')].strip()
    parsed = {}
    qouted = None
    qouted_list = []
    if '(' in qry_real and ')' in qry_real:
        qouted = qry_real[qry_real.index('(') + 1:qry_real.index(')')].strip()
        qouted_list = qouted.split(',')
        parsed['op'] = qry_real[:qry_real.index('(')].strip()
    # if qouted_list==[]:
    #     print("parsed dump", parsed)
    #     return parsed
    for i in ['trans_id/site_id','variable_id','variable_value']:
        item = qouted_list.pop(0).strip()
        if item=='':
            break
        if item.isdigit():
            parsed[i] = int(item)
        else:
            parsed[i] = int(item[1:])
        if qouted_list==[]:
            break
    # print(parsed, "parser test")
    return parsed






if __name__ == "__main__":
    main("testCases")



