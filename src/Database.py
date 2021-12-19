import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy import Column, Date, DateTime, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

import glob, shutil, datetime, gzip

from . import NJTransitAPI as njt

Base = declarative_base()

from config import config

def get_engine():
    return create_engine(get_db_url(config.config['dbuser'], config.config['dbpassword'], config.config['dbhost'], config.config['dbport'], config.config['dbname']))

def create_table(db_url):
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)

def get_db_args(args,config):
    if args.localhost is True: #n.b. this ignores what's in config/development.py
        dbhost = 'localhost'
    elif os.environ['PYTHON_ENV'] == "development":
        dbhost = 'localhost'
    else:
        dbhost = config.config['dbhost']
    return (config.config['dbuser'], config.config['dbpassword'], dbhost, config.config['dbport'], config.config[
        'dbname'])

def get_db_url(dbuser,dbpassword,dbhost,dbport,dbname):
    return 'mysql+pymysql://{}:{}@{}:{}/{}'.format(dbuser,dbpassword,dbhost,dbport,dbname)

def get_session(dbuser,dbpassword,dbhost,dbport,dbname):
    engine = create_engine(get_db_url(dbuser,dbpassword,dbhost,dbport,dbname), echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def dump_to_db(raw_buses,args,config,timestamp):
    bus_observations = Bus_to_BusObservation(raw_buses,timestamp)
    db_url=get_db_url(*get_db_args(args,config))
    create_table(db_url)
    session = get_session(*get_db_args(args,config))
    print('Dumping to {}'.format(db_url))
    num_buses = 0
    # todo check when the timestamp is being grabbed (time of request for from response itself?)
    for bus in bus_observations:
        session.add(bus)
        num_buses = num_buses + 1
    session.commit()
    return num_buses


def Bus_to_BusObservation(raw_Buses, timestamp): #bug timestamp not getting encoded—need to add it manually from time
    # of grab?
    bus_observations = []
    for bus in raw_Buses:
        _insert = BusObservation()
        for key in bus.__dict__.keys():
            setattr(_insert, key, getattr(bus, key))
        setattr(_insert, 'timestamp', timestamp)
        bus_observations.append(_insert)
    return bus_observations


class BusObservation(Base):

    __tablename__ ='buses'

    pkey = Column(Integer(), primary_key=True)
    lat = Column(Float())
    lon = Column(Float())
    cars = Column(String(20))
    consist = Column(String(20))
    d = Column(String(20))
    # dip = Column(String(20))
    dn = Column(String(20))
    fs = Column(String(127))
    id = Column(String(20), index=True)
    m = Column(String(20))
    op = Column(String(20))
    pd = Column(String(255))
    pdrtpifeedname = Column(String(255))
    pid = Column(String(20))
    rt = Column(String(20), index=True)
    rtrtpifeedname = Column(String(20))
    rtdd = Column(String(20))
    rtpifeedname = Column(String(20))
    run = Column(String(8))
    wid1 = Column(String(20))
    wid2 = Column(String(20))
    # todo index this somehow
    timestamp = Column(DateTime(), index=True)

    # waypoint_distance = Column(Float())
    # waypoint_lat = Column(Float())
    # waypoint_lon = Column(Float())


    def __repr__(self):
        return '[BusPosition: \trt {}\ttimestamp {}\tlat {}\tlon {}\twaypoint_d {}\twaypoint_lat {}\twaypoint_lon {} ]'.format(self.rt, self.timestamp, self.lat, self.lon, self.waypoint_distance,self.waypoint_lat,self.waypoint_lon)



def filepath():
    path = ("data/")
    check = os.path.isdir(path)
    if not check:
        os.makedirs(path)
        print("created folder : ", path)
    else:
        pass
    return path

# future what about compressing and dumping to S3?
def dump_to_file(localhost, xml_data, timestamp):

    timestamp_pretty = timestamp.strftime("%Y-%m-%dT_%H:%M:%S.%f")
    raw_buses = njt.parse_xml_getBusesForRouteAll(xml_data)

    # # dump to files if we are in production mode only
    # if os.environ['PYTHON_ENV'] == "development" or localhost==True:
    #     pass
    # else:
    #     dumpfile=(filepath() + 'nj_buses_all_' + timestamp_pretty + '.gz')
    #     with gzip.open(dumpfile, 'wt', encoding="ascii") as zipfile:
    #         try:
    #             zipfile.write(xml_data)
    #         except:
    #             pass # if error, dont write and return
    return raw_buses


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
        if file[7:17] == str(yesterday): # bug parse the path using os.path.join?
            yesterday_gz_files.append(file)
    with open(outfile, 'wb') as wfp:
        for fn in yesterday_gz_files:
            with open(fn, 'rb') as rfp:
                shutil.copyfileobj(rfp, wfp)
    for file in yesterday_gz_files:
        os.remove(file) #bug this isnt working?
