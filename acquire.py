import argparse, os, time
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from libraries import Archives as ar
from libraries import Database as db
from libraries import NJTransitAPI as njt
from config import config


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
    xml_data, timestamp = njt.get_xml_data('nj','all_buses')
    raw_buses = ar.dump_to_file(xml_data, timestamp)  # this returns the timestamp
    num_buses = db.dump_to_db(raw_buses, args, config, timestamp) #this returns the number of buses
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



