import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import os
import folium
from streamlit_folium import folium_static
import requests
import json

from src import Database as db
# from src.CommonTools import *

#--------------- MY INITIALIZATION ---------------

load_dotenv()
api_url_stem="/api/v2/nj/"
api_key = os.getenv("MAPBOX_API_KEY")


#--------------- STREAMLIT ---------------


# header and footer
# https://discuss.streamlit.io/t/remove-made-with-streamlit-from-bottom-of-app/1370/6
hide_streamlit_style = """
            <style>
                #MainMenu {visibility: hidden;}
                footer {
        
                        visibility: hidden;
                        
                        }
                    footer:after {
                        content:'2021, 2002 Chilltown Labs.'; 
                        visibility: visible;
                        display: block;
                        position: relative;
                        #background-color: red;
                        padding: 5px;
                        top: 2px;
                    }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


st.title("NJBusWatcher Dashboard")

st.write ("Lores mumps dolor sit mate, nominal id xiv. Dec ore offend it man re, est no dolor es explicate, re dicta elect ram demo critic duo. Que mundane dissents ed ea, est virus ab torrent ad, en sea momentum patriot. Erato dolor em omit tam quo no, per leg ere argument um re. Romanesque acclimates investiture.")

with db.get_engine().connect() as conn:


    ####################################################################
    # Statewide Map All Buses Right Now
    positions_url = 'http://127.0.0.1:5000/api/v2/nj/now'

    # Stamen Toner

    st.header("Right Now")

    map = folium.Map(
        location=[39.833851,-74.871826],
        tiles='Stamen Toner',
        zoom_start=8)

    # bug handle errors here better (load a dummy response?)
    mapdata = requests.get(positions_url, timeout=5)

    # get bounding box
    points = [(f['geometry']['coordinates'][0], f['geometry']['coordinates'][1]) for f in json.loads(mapdata.content)['features']]
    sw = min(points)[1], min(points)[0]
    ne = max(points)[1], max(points)[0]
    map.fit_bounds([sw, ne])

    folium.GeoJson(
        json.loads(mapdata.content),
        name="geojson",
        marker = folium.CircleMarker(radius = 3, # Radius in metres
                                     weight = 1, #outline weight
                                     color = '#ffffff',
                                     fill_color = '#efcc00',
                                     fill_opacity = 1),
        tooltip = folium.GeoJsonTooltip(fields = ['rt', 'id', 'fs'],
                                        aliases=['Route: ', 'Bus ID:', 'Headsign:'],
                                        style = ("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"),
                                        sticky = True
                                        )
    ).add_to(map)
    folium_static(map)

    st.header("Today")
    st.subheader("Observations")
    query = "SELECT DATE(timestamp), HOUR(timestamp), COUNT(*) FROM buses GROUP BY DATE(timestamp), HOUR(timestamp);"
    result = conn.execute(query)
    df = pd.DataFrame([r for r in result], columns=['date', 'hour', 'num. observations'])
    # df = df.set_index(['date'])
    df = df.set_index(['date', 'hour'])
    df = df.reset_index()
    # col2.write(df)
    st.bar_chart(df['num. observations'])

    st.subheader("Active Routes")
    query = "SELECT DATE(timestamp), HOUR(timestamp), COUNT(DISTINCT(rt)) FROM buses GROUP BY DATE(timestamp), HOUR(timestamp);"
    result = conn.execute(query)
    df = pd.DataFrame([r for r in result], columns=['date', 'hour', 'num. routes'])
    # df = df.set_index(['date'])
    df = df.set_index(['date', 'hour'])
    df = df.reset_index()
    # col2.write(df)
    st.bar_chart(df['num. routes'])

    # todo some kind of heat map showing days with data and how much data

