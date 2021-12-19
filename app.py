import os
import json
import requests
from dotenv import load_dotenv
from dateutil.parser import isoparse
import datetime as dt

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import streamlit as st
import folium
from streamlit_folium import folium_static
import altair as alt

from src import Database as db

#--------------- MY INITIALIZATION ---------------

load_dotenv()
api_url_stem="/api/v2/nj/"
api_key = os.getenv("MAPBOX_API_KEY")

hostname = '127.0.0.1:5000'#todo update data source dynamic hostname from config
base_url = f'http://{hostname}'
dashboard_url = f'{base_url}/api/v2/nj/dashboard'
positions_url = f'{base_url}/api/v2/nj/now'

def fetch_dashboard():
    return requests.get(dashboard_url, timeout=5).json()

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


with db.get_engine().connect() as conn:

    ################################################################################################################################################
    # map
    ################################################################################################################################################


    map = folium.Map(
        location=[39.833851,-74.871826],
        # tiles='Stamen Toner',
        # tiles='Stamen Terrain',
        # tiles='CartoDB Dark Matter',
        tiles='CartoDB Positron',
        zoom_start=8)
    mapdata = requests.get(positions_url, timeout=5)
    # get bounding box
    points = [(f['geometry']['coordinates'][0], f['geometry']['coordinates'][1]) for f in json.loads(mapdata.content)['features']]
    sw = min(points)[1], min(points)[0]
    ne = max(points)[1], max(points)[0]
    map.fit_bounds([sw, ne])
    # draw map
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
    st.write ("Map indicates last observed positions of all NJTransit buses statewide.")


    ################################################################################################################################################
    # header
    ################################################################################################################################################

    st.title("NJBusWatcher Dashboard")

    st.write("This dashboard provides summary information on the status and contents of the scraper and data warehouse tracking NJTransit bus operations. Data is available through an API at TBD.")

    ################################################################################################################################################
    # last week by hour
    ################################################################################################################################################

    st.subheader("Observations This Week")
    dash_data = fetch_dashboard()
    chart_data = dash_data['observations_by_hour']
    df = pd.DataFrame([r for r in chart_data], columns=['date', 'hour', 'num'])
    df.index = pd.to_datetime(df['date'] + ' ' + df['hour']+':00:00')
    #todo remove legend from plot
    st.bar_chart(df['num'])


    ################################################################################################################################################
    # all time by day and month -- calendar heatmap
    ################################################################################################################################################
    # https://www.pythonprogramming.in/how-to-create-heatmap-calendar-using-numpy-and-matplotlib.html

    st.subheader("Daily Observations — History")

    def heatmap():
        dates, data = generate_data()
        fig, ax = plt.subplots(figsize=(6, 10))
        calendar_heatmap(ax, dates, data)
        st.pyplot(fig)

    def generate_data():
        dashboard_data = fetch_dashboard()['observations_by_date']
        format = '%Y-%m-%d'
        # start = dt.datetime.strptime(data[0], format).date()
        start = dt.datetime.strptime(dashboard_data[0]['date'], format)
        # end = dt.datetime.strptime(data[-1], format).date()
        end = dt.datetime.strptime(dashboard_data[-1]['date'], format)
        # dates = [start + dt.timedelta(days=i) for i in range(num)]
        dates = [start + dt.timedelta(days=x) for x in range(0, (end-start).days)]
        data = [d['num'] for d in dashboard_data]
        return dates, data

    def calendar_array(dates, data):
        i, j = zip(*[d.isocalendar()[1:] for d in dates])
        i = np.array(i) - min(i)
        j = np.array(j) - 1
        ni = max(i) + 1
        calendar = np.nan * np.zeros((ni, 7))
        calendar[i, j] = data
        return i, j, calendar

    def calendar_heatmap(ax, dates, data):
        i, j, calendar = calendar_array(dates, data)
        im = ax.imshow(calendar, interpolation='none', cmap='summer')
        label_days(ax, dates, i, j, calendar)
        label_months(ax, dates, i, j, calendar)
        ax.figure.colorbar(im)

    def label_days(ax, dates, i, j, calendar):
        ni, nj = calendar.shape
        day_of_month = np.nan * np.zeros((ni, 7))
        day_of_month[i, j] = [d.day for d in dates]

        for (i, j), day in np.ndenumerate(day_of_month):
            if np.isfinite(day):
                ax.text(j, i, int(day), ha='center', va='center')

        ax.set(xticks=np.arange(7),
               xticklabels=['M', 'T', 'W', 'R', 'F', 'S', 'S'])
        ax.xaxis.tick_top()

    def label_months(ax, dates, i, j, calendar):
        month_labels = np.array(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
                                 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
        months = np.array([d.month for d in dates])
        uniq_months = sorted(set(months))
        yticks = [i[months == m].mean() for m in uniq_months]
        labels = [month_labels[m - 1] for m in uniq_months]
        ax.set(yticks=yticks)
        ax.set_yticklabels(labels, rotation=90)

    # run the above
    heatmap()


    # ################################################################################################################################################
    # # active routes chart
    # st.subheader("Active Routes")
    # query = "SELECT DATE(timestamp), HOUR(timestamp), COUNT(DISTINCT(rt)) FROM buses GROUP BY DATE(timestamp), HOUR(timestamp);"
    # result = conn.execute(query)
    # df = pd.DataFrame([r for r in result], columns=['date', 'hour', 'num. routes'])
    # # df = df.set_index(['date'])
    # df = df.set_index(['date', 'hour'])
    # df = df.reset_index()
    # # col2.write(df)
    # st.bar_chart(df['num. routes'])


    # ################################################################################################################################################
    # # calendar heatmap with altair
    # # https://developers.google.com/earth-engine/tutorials/community/time-series-visualization-with-altair
    #
    # # dict is one count per day
    # #todo update data source dynamic hostname from config
    # dashboard_url='http://127.0.0.1:5000/api/v2/nj/dashboard'
    # chartdata = json.loads(requests.get(dashboard_url, timeout=5).text)
    #
    # df = pd.DataFrame(chartdata)
    # df['date'] = pd.to_datetime(df['date'], yearfirst=True)
    # df = df.set_index('date', drop=True)
    #
    # #todo update to show each unique year-month, with days on x-axis
    # df['year'] = df.index.year
    # df['month'] = df.index.month
    # df['day'] = df.index.day
    # df['dayofyear'] = df.index.dayofyear
    # st.dataframe(df)
    # d = alt.Chart(df).mark_rect().encode(
    #     y='year:O',
    #     x='month:O',
    #     color='sum(num):Q'
    # )
    # st.altair_chart(d)
    #
    # d2 = alt.Chart(df).mark_rect().encode(
    #     y='year:O',
    #     x='dayofyear:O',
    #     color='sum(num):Q'
    # )
    # st.altair_chart(d2)