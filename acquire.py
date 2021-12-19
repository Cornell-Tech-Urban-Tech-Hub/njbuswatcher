import argparse, os, time
import json
import requests
from sqlalchemy import create_engine
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from src import Database as db
from src import NJTransitAPI as njt
from config import config


def grab_and_store():
    start = time.time()
    xml_data, timestamp = njt.get_xml_data('nj','all_buses')
    raw_buses = db.dump_to_file(args.localhost, xml_data, timestamp)  # this returns the timestamp
    num_buses = db.dump_to_db(raw_buses, args, config, timestamp) #this returns the number of buses properly
    end = time.time()
    print('Fetched {} buses on {} routes in {:2f} seconds to gzipped archive and mysql database.\n'.format(num_buses, len(raw_buses),(end - start)))
    return

def dump_dashboard():
    with create_engine(db.get_db_url(*db.get_db_args(args,config))).connect() as conn: #todo this should be easier to get from db

        # observations by date all time
        query1 = "SELECT date(timestamp) as date, count(*) as observations FROM buses GROUP BY date ORDER BY date"
        results = njt.unpack_query_results(conn.execute(query1))
        dump1 = []
        for row in results:
            dump1.append(
                { 'date': str(row['date']),
                  'num':row['observations']
                  }
            )

        # observations by hour, last 7 days
        query2 = "SELECT date(timestamp) as date, hour(timestamp) as hour, COUNT(*) as observations FROM buses WHERE date(timestamp) BETWEEN (NOW() - INTERVAL 7 DAY) AND NOW() GROUP BY date, hour;"
        results = njt.unpack_query_results(conn.execute(query2))
        dump2 = []
        for row in results:
            dump2.append(
                { 'date': str(row['date']),
                  'hour': str(row['hour']),
                  'num': row['observations']
                  }
            )

    # dump to disk
    with open('data/dashboard.json', 'w') as f:
        output = {'observations_by_date': dump1,
                  'observations_by_hour': dump2}
        print ('dumping dashboard to disk')
        print (output)
        json.dump(output, f)

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
        scheduler.add_job(dump_dashboard,'cron', hour='*') #run every hour
        scheduler.add_job(db.rotate_files,'cron', hour='1') #run at 1 am daily
        scheduler.start()
        try:
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()

    # DEVELOPMENT = run once and quit
    elif os.environ['PYTHON_ENV'] == "development":
        grab_and_store(interval=60)



