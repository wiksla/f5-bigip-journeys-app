import itertools

from parser.fsm import parse


def obtain_guests_data(bigip_conf):
    guests = {}
    with open(bigip_conf) as file_:
        for cmd, body in parse(config=file_):
            if len(set(cmd.split()).intersection({"vcmp", "guest"})) == 2:
                guests[cmd.split()[-1]] = parse_guest_data(body)
        return guests


def parse_guest_data(quest_data):
    out = []
    cache = [out]
    element = ""
    for char in quest_data:
        if char in (" ", "\t", "\r", "\n"):
            element = _add_element(cache, element)
        elif char == "{":
            a = []
            cache[-1].append(a)
            cache.append(a)
        elif char == "}":
            element = _add_element(cache, element)
            cache.pop()
        else:
            element += char
    return _convert_to_dict(out)


def _convert_to_dict(l):
    return dict(itertools.zip_longest(l[::2], l[1::2], fillvalue=""))


def _add_element(cache, element):
    if element != "":
        cache[-1].append(element)
    return ""
