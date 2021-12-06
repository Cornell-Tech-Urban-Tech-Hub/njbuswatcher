from datetime import date, datetime
from dateutil.parser import isoparse

from os.path import isfile
import os
from fastapi import FastAPI, Query, Path

from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from argparse import ArgumentParser
import logging
import pathlib
import inspect
from starlette.responses import Response
from starlette.responses import FileResponse

from dotenv import load_dotenv
from libraries.CommonTools import PrettyJSONResponse
from libraries import Database as db


#--------------- API INITIALIZATION ---------------

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="assets/templates")

#--------------- MY INITIALIZATION ---------------

load_dotenv()
api_url_stem="/api/v2/nj/"
api_key = os.getenv("MAPBOX_API_KEY")
db_connect = db.get_engine()

#--------------- HELPER FUNCTIONS ---------------

def unpack_query_results(query):
    return [dict(zip(tuple(query.keys()), i)) for i in query.cursor]

def query_builder(parameters):
    query_suffix = ''
    for field, value in parameters.items():
        if field == 'output':
            continue
        elif field == 'start':
            query_suffix = query_suffix + '{} >= "{}" AND ' \
                .format('timestamp', isoparse(value.replace(" ", "+", 1)))
            # replace is a hack but gets the job done because + was stripped from url replaced by space
            continue
        elif field == 'end':
            query_suffix = query_suffix + '{} < "{}" AND ' \
                .format('timestamp', isoparse(value.replace(" ", "+", 1)))
            continue
        elif field == 'rt':
            query_suffix = query_suffix + '{} = "{}" AND '.format('rt', value)
            continue
        else:
            query_suffix = query_suffix + '{} = "{}" AND '.format(field,value)
    query_suffix=query_suffix[:-4] # strip tailing ' AND'
    return query_suffix

# todo this simple rewrite the result dictionary, not create actual JSON
def results_to_FeatureCollection(results):
    geojson = {'type': 'FeatureCollection', 'features': []}
    for row in results['observations']:
        feature = {'type': 'Feature',
                   'properties': {},
                   'geometry': {'type': 'Point',
                                'coordinates': []}}
        feature['geometry']['coordinates'] = [row['lon'], row['lat']]
        for k, v in row.items():
            if isinstance(v, (datetime, date)):
                v = v.isoformat()
            feature['properties'][k] = v
        geojson['features'].append(feature)
    return geojson

# todo this simple rewrite the result dictionary, not create actual JSON
def make_FeatureCollection(results):
    geojson = {'type': 'FeatureCollection', 'features': []}
    for row in results['observations']:
        feature = {'type': 'Feature',
                   'properties': {},
                   'geometry': {'type': 'Point',
                                'coordinates': []}}
        feature['geometry']['coordinates'] = [row['lon'], row['lat']]
        for k, v in row.items():
            if isinstance(v, (datetime, date)):
                v = v.isoformat()
            feature['properties'][k] = v
        geojson['features'].append(feature)
    return geojson

#todo test debug kepler output
def make_KeplerTable(query):
    results = query['observations']
    fields = [{"name":x} for x in dict.keys(results[0])]

    # make the fields list of dicts
    field_list =[]
    for f in fields:
        fmt='TBD'
        typ=type(f)
        # field_list.append("{name: '{}', format '{}', type:'{}'},".format(f,fmt,typ))
        # field_list.append("{name: '{}'},".format(f))
        field_list.append("{'TBD':'TBD',")
    # make the rows list of lists
    rows = []
    for r in results:
        (a, row)= zip(*r.items())
        rows.append(r)
    kepler_bundle = {"fields": fields, "rows": rows }
    return kepler_bundle


#--------------- API ENDPOINTS ---------------

# POSITIONS BY ROUTE, START + END
@app.get("/api/v2/nj/buses", response_class=PrettyJSONResponse)

# http://127.0.0.1:5000/api/v2/nj/buses?output=geojson&rt=119&start=2021-12-01T00:00:00+00:00&end=2022-01-01T00:00:00+00:00
# http://127.0.0.1:5000/api/v2/nj/buses?output=json&rt=119&start=2021-12-01T00:00:00+00:00&end=2022-01-01T00:00:00+00:00
# http://127.0.0.1:5000/api/v2/nj/buses?output=json&rt=119&start=2021-12-01T00:00:00+00:00&end=2022-01-01T00:00:00+00:00


# http://nj.buswatcher.org/api/v2/nj/buses?output=geojson&rt=119&start=2021-12-01T00:00:00+00:00&end=2021-12-31T00:00:00+00:00


# output=[json, geojson,kepler]
# rt=route number
# start=datetime in ISO8601
# end=datetime in ISO8601

# # todo debug field validation
# async def fetch_buses(*,
#                       rt: str = Path(..., max_length=3),
#                       start:datetime = Path(..., ge=1, le=12),
#                       end:datetime = Path(..., ge=1, le=12),
#                       format: str = Path(..., max_length=20)
#                       ):

#async def fetch_buses(rt: str, start:datetime, end:datetime, format: str):
async def fetch_buses(rt: str, start:str, end:str, output: str):

    # prepare the query
    query_prefix = "SELECT * FROM buses WHERE {}"
    query_suffix = query_builder({'rt': rt,
                                  'start':start,
                                  'end':end,
                                  'output':output
                                  }
                                 )
    query_compound = query_prefix.format(query_suffix )
    print(query_compound)

    # execute query
    conn = db_connect.connect()
    query = conn.execute(query_compound)

    if output == 'json':
        return {'observations': unpack_query_results(query)}
    elif output == 'geojson':
        return make_FeatureCollection(unpack_query_results(query))
    elif output == 'kepler':
        return make_KeplerTable(unpack_query_results(query))


# POSITIONS RIGHT NOW (makes separate request to Clever Devices API)
@app.get("/api/v2/nj/now", response_class=PrettyJSONResponse)

# http://nj.buswatcher.org/api/v2/nj/now
# http://127.0.0.1:5000/api/v2/nj/now

async def fetch_live(rt: str, start:str, end:str, output: str):

    # this should just grab latest postitions and dump it back in GeoJSON

    return



#--------------- MAIN ---------------
if __name__ == '__main__':

    parser = ArgumentParser(description='NJbuswatcher.org v2 API')
    parser.add_argument("-v",
                        "--verbose",
                        help="increase output verbosity",
                        action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    uvicorn.run(app, port=5000, debug=True)
