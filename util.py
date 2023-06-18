import pickle
from collections.abc import Container, Mapping
from sys import getsizeof


def pickle_to_file(obj, filename):
    with open(filename, "wb") as fp:
        pickle.dump(obj, fp)


def unpickle_file(filename):
    with open(filename, "rb") as fp:
        return pickle.load(fp)


def unpickle_file_at_offset(filename, offset):
    with open(filename, "rb") as fp:
        fp.seek(offset, 0)
        return pickle.load(fp)


# Based on:
# https://code.tutsplus.com/tutorials/understand-how-much-memory-your-python-objects-use--cms-25609
def deep_getsizeof(o, ids=set()):
    """
    Find the memory footprint of a Python object.

    This is a recursive function that drills down a Python object graph
    like a dictionary holding nested dictionaries with lists of lists
    and tuples and sets.

    The sys.getsizeof function does a shallow size of only. It counts each
    object inside a container as pointer only regardless of how big it
    really is.

    :param o: the object
    :param ids:
    :return:
    """
    d = deep_getsizeof
    if id(o) in ids:
        return 0

    r = getsizeof(o)
    ids.add(id(o))

    if isinstance(o, str) or isinstance(0, str):
        return r

    if isinstance(o, Mapping):
        return r + sum(d(k, ids) + d(v, ids) for k, v in o.items())

    if isinstance(o, Container):
        return r + sum(d(x, ids) for x in o)

    return r


# Based on _Serge Ballesta_'s answer:
# https://stackoverflow.com/questions/46408568#46408568
class SizedReader:
    def __init__(self, fd, encoding="utf-8"):
        self.fd = fd
        self.size = 0
        self.encoding = encoding

    def __next__(self):
        line = next(self.fd)
        self.size += len(line)
        return line.decode(self.encoding)

    def __iter__(self):
        return self
