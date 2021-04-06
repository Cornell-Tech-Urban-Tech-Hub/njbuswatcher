import gtfs_functions as gtfs

# gtfs functions docs
# https://github.com/anthonymobile/gtfs_functions

class SystemMap():

    def __init__(self):
        routes, stops, stop_times, trips, shapes = gtfs.import_gtfs(r"../gtfs/bus_data.zip")