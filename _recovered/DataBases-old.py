from sqlalchemy import create_engine, ForeignKeyConstraint, Index, Date, Column, Integer, DateTime, Float, String, Text, Boolean, ForeignKey, JSON
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from . import DBconfig

# Base = declarative_base()


class SQLAlchemyDBConnection(object):

    def __init__(self):
        # self.connection_string = 'sqlite:///jc_buswatcher.db'  # TESTING, WORKS
        self.connection_string = DBconfig.connection_string # replaces 'localhost' with 'db' for development

    def __enter__(self):
        engine = create_engine(self.connection_string)
        Session = sessionmaker()

        self.session = Session(bind=engine)

        while True:
            try:
                Base.metadata.create_all(bind=engine)
            except OperationalError:
                print ('lib.DataBases Cant connect to db,retrying...')
                continue
            break

        return self

    def __relax__(self):
        self.session.execute('SET FOREIGN_KEY_CHECKS = 0;')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.execute('SET FOREIGN_KEY_CHECKS = 1;')
        self.session.close()



# class BusPosition(Base):
#     #####################################################
#     # CLASS BusPosition
#     #####################################################
#
#     __tablename__ ='positions'
#
#     pkey = Column(Integer(), primary_key=True)
#     lat = Column(Float)
#     lon = Column(Float)
#     cars = Column(String(20))
#     consist = Column(String(20))
#     d = Column(String(20))
#     # dip = Column(String(20))
#     dn = Column(String(20))
#     fs = Column(String(127))
#     id = Column(String(20))
#     # id = Column(String(20), index=True)
#     m = Column(String(20))
#     op = Column(String(20))
#     pd = Column(String(255))
#     pdrtpifeedname = Column(String(255))
#     pid = Column(String(20))
#     rt = Column(String(20))
#     rtrtpifeedname = Column(String(20))
#     rtdd = Column(String(20))
#     rtpifeedname = Column(String(20))
#     run = Column(String(8))
#     wid1 = Column(String(20))
#     wid2 = Column(String(20))
#     timestamp = Column(DateTime())
#
#     waypoint_distance = Column(Float())
#     waypoint_lat = Column(Float())
#     waypoint_lon = Column(Float())
#
#
#     def __repr__(self):
#         return '[BusPosition: \trt {}\ttimestamp {}\tlat {}\tlon {}\twaypoint_d {}\twaypoint_lat {}\twaypoint_lon {} ]'.format(self.rt, self.timestamp, self.lat, self.lon, self.waypoint_distance,self.waypoint_lat,self.waypoint_lon)
