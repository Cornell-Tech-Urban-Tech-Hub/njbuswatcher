import datetime
import time

from lib.CommonTools import distance

from cachetools import cached, TTLCache
cache = TTLCache(maxsize=100, ttl=300)

from config import config
import lib.NJTransitAPI as api
from lib.DataBases import SQLAlchemyDBConnection, BusPosition

def make_BusPosition(bus,route):

    position = BusPosition()

    position.lat = float(bus.lat)
    position.lon = float(bus.lon)
    position.cars = bus.cars
    position.consist = bus.consist
    position.d = bus.d
    position.dn = bus.dn
    position.fs = bus.fs
    position.id = bus.id
    position.m = bus.m
    position.op = bus.op
    position.pd = bus.pd
    position.pdrtpifeedname = bus.pdRtpiFeedName
    position.pid = bus.pid
    position.rt = bus.rt
    position.rtrtpifeedname = bus.rtRtpiFeedName
    position.rtdd = bus.rtdd
    position.rtpifeedname = bus.rtpiFeedName
    position.run = bus.run
    position.wid1 = bus.wid1
    position.wid2 = bus.wid2
    position.timestamp = datetime.datetime.now()

    position.waypoint_lat, position.waypoint_lon, position.waypoint_distance = get_nearest_waypoint(bus, route)

    return position



def get_nearest_waypoint(bus, route):

    bus.lat = float(bus.lat)
    bus.lon = float(bus.lon)

    # fetch the route geometry
    paths = get_route_paths(bus, route)

    # # find the right path and extract waypoints
    # for path in paths:
    #     if bus.dd == path.d:
    #         for point in path.points:
    #             waypoints = []
    #             for point in path.points:
    #                 waypoints.append(point)

    # find the right path and extract waypoints
    for path in paths:
        if bus.dd == path.d:
            waypoints = []
            for point in path.points:
                waypoints.append(point)

    # find the nearest neighbor using haversine
    # https://stackoverflow.com/questions/41336756/find-the-closest-latitude-and-longitude

    closest_waypoint = closest(waypoints,bus)
    distance_to_closest_waypoint = distance(bus.lat, bus.lon, closest_waypoint.lat, closest_waypoint.lon)

    return closest_waypoint.lat, closest_waypoint.lon, distance_to_closest_waypoint



def closest(waypoints, bus):
    closest_waypoint = min(waypoints, key=lambda p: distance(bus.lat, bus.lon, p.lat, p.lon))
    return closest_waypoint


@cached(cache)
def get_route_paths(bus, route):
    route_paths=api.parse_xml_getRoutePoints(api.get_xml_data(source, 'route_points', route=route))[0].paths
    return route_paths



# MAIN PROGRAM ----------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    run_frequency = 60 # seconds
    time_start=time.monotonic()

    while True:

        # initialize
        source = config.source
        db = SQLAlchemyDBConnection()

        with db:

            routelist = [k for k,v in config.routes.items()]
            print (routelist)

            for route in routelist:
                response = api.get_xml_data(source, 'buses_for_route', route=route)
                buses = api.parse_xml_getBusesForRoute(response)
                # print ('fetched {} buses on route {}'.format(len(buses),route))
                for bus in buses:
                    bus_position = make_BusPosition(bus,route)
                    print (bus_position)
                    db.session.add(bus_position)

            db.session.commit()


        time.sleep(run_frequency - ((time.monotonic() - time_start) % 60.0))  # sleep remainder of the 60 second loop




