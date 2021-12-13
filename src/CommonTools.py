#todo this can be deprecated soon

import time
from math import cos, asin, sqrt
import os




def timeit(f):
    def timed(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        print ('func:%r took: %2.4f sec' % \
          (f.__name__, te-ts))
        return result
    return timed

def get_config_path():
    if os.getcwd() == "/":  # docker
        prefix = "/buswatcher/buswatcher/"
    elif "Users" in os.getcwd():
        prefix = ""
    else:
        prefix = ""
    path = (prefix + "config/")
    return path

def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p) * (1-cos((lon2-lon1)*p)) / 2
    return 5280 * (7918 * asin(sqrt(a))) # https://stackoverflow.com/questions/27928/calculate-distance-between-two-latitude-longitude-points-haversine-formula/11178145


# memoization https://stackoverflow.com/questions/10879137/how-can-i-memoize-a-class-instantiation-in-python
def get_id_tuple(f, args, kwargs, mark=object()):
    """
    Some quick'n'dirty way to generate a unique key for an specific call.
    """
    l = [id(f)]
    for arg in args:
        l.append(id(arg))
    l.append(id(mark))
    for k, v in kwargs:
        l.append(k)
        l.append(id(v))
    return tuple(l)

_memoized = {}
def memoize(f):
    """
    Some basic memoizer
    """
    def memoized(*args, **kwargs):
        key = get_id_tuple(f, args, kwargs)
        if key not in _memoized:
            _memoized[key] = f(*args, **kwargs)
        return _memoized[key]
    return memoized