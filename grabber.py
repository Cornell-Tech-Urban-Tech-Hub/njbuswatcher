import argparse, os, glob, shutil, datetime, time, gzip
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import lib.Database as db
import lib.NJTransitAPI as njt
from config import config

def filepath():
    path = ("data/")
    check = os.path.isdir(path)
    if not check:
        os.makedirs(path)
        print("created folder : ", path)
    else:
        pass
    return path

def get_db_args():
    if args.localhost is True: #n.b. this ignores what's in config/development.py
        dbhost = 'localhost'
    elif os.environ['PYTHON_ENV'] == "development":
        dbhost = 'localhost'
    else:
        dbhost = config.config['dbhost']
    return (config.config['dbuser'], config.config['dbpassword'], dbhost, config.config['dbport'], config.config[
        'dbname'])

def dump_to_file(xml_data):
    timestamp = datetime.datetime.now()
    timestamp_pretty = timestamp.strftime("%Y-%m-%dT_%H:%M:%S.%f")
    raw_buses = njt.parse_xml_getBusesForRouteAll(xml_data)
    dumpfile=(filepath() + 'nj_buses_all_' + timestamp_pretty + '.gz')
    with gzip.open(dumpfile, 'wt', encoding="ascii") as zipfile:
        try:
            zipfile.write(xml_data)
        except:
            pass # if error, dont write and return
    return raw_buses, timestamp

def rotate_files(): # https://programmersought.com/article/77402568604/
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days = 1) # e.g. 2020-10-04
    # print ('today is {}, yesterday was {}'.format(today,yesterday))
    filepath = './data/'
    outfile = '{}daily-{}.gz'.format(filepath, yesterday)
    # print ('bundling minute grabs from {} into {}'.format(yesterday,outfile))
    all_gz_files = glob.glob("{}*.gz".format(filepath))
    yesterday_gz_files = []
    for file in all_gz_files:
        if file[7:17] == str(yesterday): # bug this should parse the path using os.path.join?
            yesterday_gz_files.append(file)
    with open(outfile, 'wb') as wfp:
        for fn in yesterday_gz_files:
            with open(fn, 'rb') as rfp:
                shutil.copyfileobj(rfp, wfp)
    for file in yesterday_gz_files:
        os.remove(file)

# todo rewrite this? or run the new map off the API using a query that grabs the last minute?
# def dump_to_lastknownpositions(feeds):
#     f_list=[]
#     for route_bundle in feeds:
#         for route_id,route_report in route_bundle.items():
#             route_report = route_report.json()
#             try:
#                 for b in route_report['Siri']['ServiceDelivery']['VehicleMonitoringDelivery'][0]['VehicleActivity']:
#                     p = geojson.Point((b['MonitoredVehicleJourney']['VehicleLocation']['Longitude'],
#                                        b['MonitoredVehicleJourney']['VehicleLocation']['Latitude']))
#
#                     # this creates a gigantic file, need to be more selective with fields
#                     # f = geojson.Feature(geometry=p, properties=flatten(b['MonitoredVehicleJourney']))
#
#                     # this version only shows ones with reported values
#                     # f = geojson.Feature(geometry=p,properties={'occupancy':b['MonitoredVehicleJourney']['Occupancy']})
#
#                     # this should work
#                     try:
#                         occupancy={'occupancy':b['MonitoredVehicleJourney']['Occupancy']}
#                     except KeyError:
#                         occupancy = {'occupancy': 'empty'}
#
#                     try:
#                         passengers={'passengers': str(b['MonitoredVehicleJourney']['MonitoredCall']['Extensions'][
#                             'Capacities']['EstimatedPassengerCount'])}
#                     except KeyError:
#                         passengers = {'passengers': '0'}
#
#                     f = geojson.Feature(geometry=p, properties=[occupancy,passengers])
#
#                     f_list.append(f)
#             except KeyError: # no VehicleActivity?
#                 pass
#     fc = geojson.feature.FeatureCollection(f_list)
#
#     with open('./api-www/static/lastknownpositions.geojson', 'w') as outfile:
#         geojson.dump(fc, outfile)
#
#     return

def dump_to_db(raw_buses):

    bus_observations = Bus_to_BusObservation(raw_buses)
    db_url=db.get_db_url(*get_db_args())
    db.create_table(db_url)
    session = db.get_session(*get_db_args())
    print('Dumping to {}'.format(db_url))
    num_buses = 0
    # todo want to do something with timestamp?
    for bus in bus_observations:
        session.add(bus)
        num_buses = num_buses + 1
    session.commit()
    return num_buses

def Bus_to_BusObservation(raw_Buses):
    bus_observations = []
    for bus in raw_Buses:
        _insert = db.BusObservation()
        # todo iterate over properties in bus and match for properties in busobservation
        bus_observations.append(_insert)
    return bus_observations

def grab_and_store(**kwargs):
    start = time.time()
    # path_list = get_path_list()
    # feeds = []
    url = njt._gen_command('nj','all_buses')
    try:
        response = requests.get(url, timeout=kwargs.get("interval"))
    except:
        print('something happened')
    # data = response.read().decode("utf-8")
    xml_data = njt.get_xml_data('nj','all_buses')
    raw_buses, timestamp = dump_to_file(xml_data)  # this returns the timestamp
    num_buses = dump_to_db(raw_buses) #this returns the number of buses #todo make sure the db is setup properly
    end = time.time()
    #todo calculate number of routes
    print('Fetched {} buses on {} routes in {:2f} seconds to gzipped archive and mysql database.\n'.format(num_buses,
                                                                                                           len(
                                                                                                               raw_buses),
                                                                                                           (end - start)))
    return


if __name__ == "__main__":

    print('NJTransit Clever Devices API Scraper v4.0 March 2021. Anthony Townsend <atownsend@cornell.edu>')
    print('mode: {}'.format(os.environ['PYTHON_ENV']))

    parser = argparse.ArgumentParser(description='NJTransit grabber, fetches and stores current position for buses')
    parser.add_argument('-l', action="store_true", dest="localhost", help="force localhost for production mode")
    args = parser.parse_args()

    load_dotenv()

    # PRODUCTION = start main loop
    if os.environ['PYTHON_ENV'] == "production":
        interval = 60
        print('Scanning on {}-second interval.'.format(interval))
        scheduler = BackgroundScheduler()
        scheduler.add_job(grab_and_store, 'interval', seconds=interval, max_instances=2, misfire_grace_time=15)
        scheduler.add_job(rotate_files,'cron', hour='1') #run at 1 am daily
        scheduler.start()
        try:
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()

    # DEVELOPMENT = run once and quit
    elif os.environ['PYTHON_ENV'] == "development":
        grab_and_store(interval=60)



