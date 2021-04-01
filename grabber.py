import argparse, os, time
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

import lib.Archives as ar
import lib.Database as db
import lib.NJTransitAPI as njt
from config import config


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
    raw_buses, timestamp = ar.dump_to_file(xml_data)  # this returns the timestamp
    num_buses = db.dump_to_db(raw_buses,args,config) #this returns the number of buses
    # properly
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
        scheduler.add_job(ar.rotate_files,'cron', hour='1') #run at 1 am daily
        scheduler.start()
        try:
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()

    # DEVELOPMENT = run once and quit
    elif os.environ['PYTHON_ENV'] == "development":
        grab_and_store(interval=60)



