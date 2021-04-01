#todo NUMERO UNO rebuild this whole grabber and parser using the best from NYCbuswatcher
# todo add a bus_dash_2 style front end, or kepler like in the gtfs_fnctiosn notebook?

import argparse
import requests
import os
import glob, shutil
import datetime
import json
import time
import gzip
import collections.abc
import geojson

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

import lib.Database as db
import lib.NJTransitAPI as njt

from config import config


# def get_path_list():
#     path_list = []
#
#     url = njt._gen_command('nj','all_buses')
#
#     try:
#         response = requests.get(url, timeout=30)
#         if response.status_code == 503: # response is bad, so go to exception and load the pickle
#             raise Exception(503, "503 error code fetching route definitions. Clever Devices API probably overloaded.")
#         else: # response is good, so save it to pickle and proceed
#             with open((filepath() + 'routes-for-agency.pickle'), "wb") as pickle_file:
#                 pickle.dump(response,pickle_file)
#     except Exception as e: # response is bad, so load the last good pickle
#         with open((filepath() + 'routes-for-agency.pickle'), "rb") as pickle_file:
#             response = pickle.load(pickle_file)
#         print("Route URLs loaded from pickle cache.")
#     finally:
#         routes = response.json()
#         now=datetime.datetime.now()
#         print('Found {} routes at {}.'.format(len(routes['data']['list']),now.strftime("%Y-%m-%d %H:%M:%S")))
#
#     for route in routes['data']['list']:
#         path_list.append({route['id']:"/api/siri/vehicle-monitoring.json?key={}&VehicleMonitoringDetailLevel=calls&LineRef={}".format(os.getenv("API_KEY"), route['id'])})
#
#     return path_list


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
    return (config.config['dbuser'],
            config.config['dbpassword'],
            dbhost,
            config.config['dbport'],
            config.config['dbname']
            )

def dump_to_file(xml_data):
    timestamp = datetime.datetime.now()
    timestamp_pretty = timestamp.strftime("%Y-%m-%dT_%H:%M:%S.%f")
    buses = njt.parse_xml_getBusesForRouteAll(xml_data)
    dumpfile=(filepath() + 'nj_buses_all_' + timestamp_pretty + '.gz')
    with gzip.open(dumpfile, 'wt', encoding="ascii") as zipfile:
        try:
            zipfile.write(xml_data)
        except:
            pass # if error, dont write and return
    return buses, timestamp


# https://programmersought.com/article/77402568604/
def rotate_files(): #todo rewrite this
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days = 1) # e.g. 2020-10-04
    # print ('today is {}, yesterday was {}'.format(today,yesterday))
    filepath = './data/'
    outfile = '{}daily-{}.gz'.format(filepath, yesterday)
    # print ('bundling minute grabs from {} into {}'.format(yesterday,outfile))
    all_gz_files = glob.glob("{}*.gz".format(filepath))
    yesterday_gz_files = []
    for file in all_gz_files:
        if file[7:17] == str(yesterday): # this should parse the path using os.path.join?
            yesterday_gz_files.append(file)
    # print ('adding {} files'.format(len(yesterday_gz_files)))
    with open(outfile, 'wb') as wfp:
        for fn in yesterday_gz_files:
            with open(fn, 'rb') as rfp:
                shutil.copyfileobj(rfp, wfp)
    for file in yesterday_gz_files:
        os.remove(file)


# def flatten(d, parent_key='', sep='_'):
#     items = []
#     for k, v in d.items():
#         new_key = parent_key + sep + k if parent_key else k
#         if isinstance(v, collections.abc.MutableMapping):
#             items.extend(flatten(v, new_key, sep=sep).items())
#         else:
#             items.append((new_key, v))
#     return dict(items)


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


def dump_to_db(buses):
    db_url=db.get_db_url(*get_db_args())
    db.create_table(db_url)
    session = db.get_session(*get_db_args())
    print('Dumping to {}'.format(db_url))
    num_buses = 0
    # todo want to do something with timestamp?
    for bus in buses:
        session.add(bus)
        num_buses = num_buses + 1
    session.commit()
    return num_buses


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
    buses, timestamp = dump_to_file(xml_data)  # this returns the timestamp
    num_buses = dump_to_db(buses) #this returns the number of buses #todo make sure the db is setup properly
    end = time.time()

    #todo calculate number of routes
    print('Fetched {} buses on {} routes in {:2f} seconds to gzipped archive and mysql database.\n'.format(num_buses,
                                                                                                           len(buses),
                                                                                                           (end - start)))
    return


if __name__ == "__main__":

    print('NJTransit Clever Devices API Scraper v4. March 2021. Anthony Townsend <atownsend@cornell.edu>')
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



