from sqlalchemy import create_engine
import argparse
import os, json

from config import config

from src import Database as db
from src import NJTransitAPI as njt

print('Dashboard Dumper v4.0 March 2021. Anthony Townsend <atownsend@cornell.edu>')
print('mode: {}'.format(os.environ['PYTHON_ENV']))

parser = argparse.ArgumentParser(description='NJTransit grabber, fetches and stores current position for buses')
parser.add_argument('-l', action="store_true", dest="localhost", help="force localhost for production mode")
args = parser.parse_args()


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

