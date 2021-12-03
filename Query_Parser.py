from typing import List


def get_argument(input_query: str) -> List:
    left = input_query.index("(")
    right = input_query.index(")")
    args_raw = input_query[left + 1: right].split(",")
    args = []
    for i in args_raw:
        i = i.strip()
        if i != "" and i.isdigit() == False:
            i = i[1:]
        args.append(i)
    return args


def parse_query(input_query: str) -> List:
    res = []
    # print("debug")

    commd = input_query[:input_query.index("(")]
    res.append(commd)
    res += get_argument(input_query)
    # print("parsed command is : {}".format(str(res)) )
    return res
