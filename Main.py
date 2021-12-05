import Query_Parser
import os
from Transaction_Manager import Transaction_Manager


def main(input_path):
    """

    :rtype: None
    """
    # checks if path is a file
    is_file = os.path.isfile(input_path)

    # checks if path is a directory
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
    # print("Hello World!")
    trans_mgr = Transaction_Manager()
    cmmd_waitlist = []
    input_path = input_file_path
    exe_result, in_waitlist = False, False
    waitlist_idx = 0

    # try:
    file_read = open(input_path, "r")
    print("file loaded")
    while True:

        fetched = None
        in_waitlist = False

        if len(cmmd_waitlist) > 0 and waitlist_idx < len(cmmd_waitlist):
            fetched = cmmd_waitlist[waitlist_idx]
            # print("waitlist index {}, command is {}".format(waitlist_idx, fetched))

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
                # qry = qry.strip()
            if qry is not None and qry != '\n' and qry.strip() != "":

                fetched = Query_Parser.parse_query(qry.strip())
            else:
                # break
                continue

        if fetched[0] == 'begin':
            # print("==================================================Transaction T{} begins=======================================".format(int(fetched[1])))
            exe_result = trans_mgr.begin(int(fetched[1]))
        elif fetched[0] == 'beginRO':
            exe_result = trans_mgr.begin_read_only(int(fetched[1]))
        elif fetched[0] == 'R':
            exe_result = trans_mgr.read(int(fetched[1]), int(fetched[2]))
        elif fetched[0] == 'W':
            exe_result = trans_mgr.write(int(fetched[1]), int(fetched[2]), int(fetched[3]))
        elif fetched[0] == 'recover':
            exe_result = trans_mgr.recover(int(fetched[1]))
        elif fetched[0] == 'fail':
            exe_result = trans_mgr.fail(int(fetched[1]))
        elif fetched[0] == 'dump':
            exe_result = trans_mgr.dump()
        elif fetched[0] == 'end':
            exe_result = trans_mgr.end(int(fetched[1]))
            # print(
            #     "==================================================Transaction T{} ends=======================================".format(
            #         int(fetched[1])))

        pre_cmmd_waitlist_len = len(cmmd_waitlist)
        if exe_result == True:
            if in_waitlist == True:
                cmmd_waitlist.remove(cmmd_waitlist[waitlist_idx])
            waitlist_idx = 0
        else:
            if in_waitlist == False:
                cmmd_waitlist.append(fetched)
                print("instruction is waiting: {}".format(fetched))
                waitlist_idx = 0
            else:
                waitlist_idx += 1
        trans_mgr.time_stamp += 1
        deadlock_detection_result = trans_mgr.dead_lock_detect()

        if deadlock_detection_result == -2:
            print("===================================================================================================")
            # pass


if __name__ == "__main__":
    main("testcases.txt")
    # main("testCases")
    # main("testCases/testcase2.txt")
    # t=Transaction_Manager()
    # print(t(1,2,102))
