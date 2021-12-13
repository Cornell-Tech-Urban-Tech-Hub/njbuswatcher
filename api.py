from datetime import date, datetime
from dateutil.parser import isoparse

from argparse import ArgumentParser
import logging
import os

from fastapi import FastAPI, Query, Path
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src import Database as db
from src import NJTransitAPI as njt

from dotenv import load_dotenv

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


#--------------- API ENDPOINTS ---------------

@app.get("/api/v2/nj/buses", response_class=njt.PrettyJSONResponse)
# POSITIONS BY ROUTE, START + END
# http://127.0.0.1:5000/api/v2/nj/buses?output=geojson&rt=119&start=2021-12-01T00:00:00+00:00&end=2022-01-01T00:00:00+00:00
# http://127.0.0.1:5000/api/v2/nj/buses?output=json&rt=119&start=2021-12-01T00:00:00+00:00&end=2022-01-01T00:00:00+00:00
# http://127.0.0.1:5000/api/v2/nj/buses?output=json&rt=119&start=2021-12-01T00:00:00+00:00&end=2022-01-01T00:00:00+00:00
# http://0.0.0.0/api/v2/nj/buses?output=json&rt=119&start=2021-12-01T00:00:00+00:00&end=2022-01-01T00:00:00+00:00
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
# async def fetch_buses(rt: str, start:str, end:str, output: str):
async def fetch_buses(rt: str, start:str, end:str):

    # prepare the query
    query_prefix = "SELECT * FROM buses WHERE {}"
    query_suffix = njt.query_builder({'rt': rt,
                                  'start':start,
                                  'end':end
                                  }
                                 )
    query_compound = query_prefix.format(query_suffix )
    print(query_compound)

    # execute query
    with db.get_engine().connect() as conn:
        query = conn.execute(query_compound)
        return njt.results_to_FeatureCollection(njt.unpack_query_results(query))
        #
        # if output == 'json':
        #     return {'observations': unpack_query_results(query)}
        # elif output == 'geojson':
        #     return results_to_FeatureCollection(unpack_query_results(query))
        # elif output == 'kepler':
        #     return make_KeplerTable(unpack_query_results(query))



@app.get("/api/v2/nj/now", response_class=njt.PrettyJSONResponse)
# POSITIONS RIGHT NOW (makes separate request to Clever Devices API)
# http://nj.buswatcher.org/api/v2/nj/now
# http://127.0.0.1:5000/api/v2/nj/now

async def fetch_live():

    # this should just grab latest postitions and dump it back in GeoJSON
    xml_data, timestamp = njt.get_xml_data('nj','all_buses')
    raw_buses = njt.parse_xml_getBusesForRouteAll(xml_data)
    bus_observations = db.Bus_to_BusObservation(raw_buses,timestamp)

    # return bus_observations
    return njt.results_to_FeatureCollection([b.__dict__ for b in bus_observations])



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
