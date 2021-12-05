#-----------------------------------------------------------------------------------------
# sources
#
# api approach adapted from https://www.codementor.io/@sagaragarwal94/building-a-basic-restful-api-in-python-58k02xsiq
# query parameter handling after https://stackoverflow.com/questions/30779584/flask-restful-passing-parameters-to-get-request
#-----------------------------------------------------------------------------------------

import os
from datetime import date, datetime
from dateutil import parser

from flask import Flask, render_template, request, jsonify, abort, send_from_directory
from flask_cors import CORS
from flask_restful import Resource, Api
from marshmallow import Schema, fields
from sqlalchemy import create_engine
from dotenv import load_dotenv

from libraries import Database as db


#--------------- INITIALIZATION ---------------
app = Flask(__name__,template_folder='./api-www/templates',static_url_path='/static',static_folder="api-www/static/")
api = Api(app)
CORS(app)

from config import config
load_dotenv()
api_key = os.getenv("MAPBOX_API_KEY")
api_url_stem="/api/v1/nyc/livemap"
#todo cant we get this and pass it back from lib.Database?
db_connect = create_engine(db.get_db_url(config.config['dbuser'], config.config['dbpassword'], config.config[
    'dbhost'], config.config['dbport'], config.config['dbname']))


#--------------- HELPER FUNCTIONS ---------------

def unpack_query_results(query):
    return [dict(zip(tuple(query.keys()), i)) for i in query.cursor]

# def sparse_unpack_for_livemap(query):
#     unpacked = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
#     sparse_results = []
#     for row in unpacked:
#         sparse_results.append('something')
#     return unpacked

def query_builder(parameters):
    query_suffix = ''
    for field, value in parameters.items():
        if field == 'output':
            continue
        elif field == 'start':
            query_suffix = query_suffix + '{} >= "{}" AND '\
                .format('timestamp',parser.isoparse(value.replace(" ", "+", 1)))
                # replace is a hack but gets the job done because + was stripped from url replaced by space
            continue
        elif field == 'end':
            query_suffix = query_suffix + '{} < "{}" AND '\
                .format('timestamp', parser.isoparse(value.replace(" ", "+", 1)))
            continue
        elif field == 'rt':
            query_suffix = query_suffix + '{} = "{}" AND '.format('rt', value)
            continue
        else:
            query_suffix = query_suffix + '{} = "{}" AND '.format(field,value)
    query_suffix=query_suffix[:-4] # strip tailing ' AND'
    return query_suffix

# todo this should dump with indent=4
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

#todo test debug kepler output
def results_to_KeplerTable(query):
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

class SystemQuerySchema(Schema):
    rt = fields.Str(required=True)
    start = fields.Str(required=False)  # in ISO 8601 e.g. 2020-08-11T14:42:00+00:00
    end = fields.Str(required=False)  # in ISO 8601 e.g. 2020-08-11T15:12:00+00:00
    output = fields.Str(required=True)

system_schema = SystemQuerySchema()

class SystemAPI(Resource):
    def get(self):
        errors = system_schema.validate(request.args)
        if errors:
            abort(400, str(errors))
        conn = db_connect.connect()
        query_prefix = "SELECT * FROM buses WHERE {}"
        query_suffix = query_builder(request.args)
        query_compound = query_prefix.format(query_suffix )
        print (query_compound)
        query = conn.execute(query_compound)
        results = {'observations': unpack_query_results(query)}

        if request.args['output'] == 'geojson':
            return results_to_FeatureCollection(results)
        elif request.args['output'] == 'kepler':
            return results_to_KeplerTable(results)

# http://nj.buswatcher.org/api/v1/nj/buses?output=geojson&rt=119&start=2021-03-28T00:00:00+00:00&end=2021-04-30T00:00:00+00:00
# output=[geojson,kepler]
# rt=route number
# start=datetime in ISO8601
# end=datetime in ISO8601

api.add_resource(SystemAPI, '/api/v1/nj/buses', endpoint='buses')


# todo rebuild this, but pointing at a static file updated with each grab
# #--------------- LEGACY ENDPOINTS ---------------
#
# # is the browser still caching this — wrap this in an http header to expire it?
# @app.route('/api/v1/nj/lastknownpositions')
# def lkp():
#     print (app.static_folder)
#     return send_from_directory(app.static_folder,'lastknownpositions.geojson')
#



#--------------- MAIN ---------------

if __name__ == '__main__':
    app.run(debug=True)
