import os
import json
import requests
import argparse
from dotenv import load_dotenv
from dateutil.parser import isoparse
import datetime as dt
from config import config
from sqlalchemy import create_engine
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import streamlit as st
import folium
from streamlit_folium import folium_static
import altair as alt

from src import Database as db

#--------------- MY INITIALIZATION ---------------
parser = argparse.ArgumentParser(description='NJTransit dashboard')
parser.add_argument('-l', action="store_true", dest="localhost", help="force localhost for production mode")
args = parser.parse_args()

load_dotenv()
api_url_stem="/api/v2/nj/"
api_key = os.getenv("MAPBOX_API_KEY")

# hostname = '127.0.0.1:5000'
base_url = config.config['api_base_url']
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

with create_engine(db.get_db_url(*db.get_db_args(args,config))).connect() as conn: #todo this should be easier to get from db
#with db.get_engine().connect() as conn:


    ################################################################################################################################################
    # header
    ################################################################################################################################################

    st.title("NJBusWatcher Dashboard")

    st.write("This dashboard provides summary information on the status and contents of the scraper and data warehouse tracking NJTransit bus operations.")




    # ################################################################################################################################################
    # # map
    # ################################################################################################################################################
    #
    #
    # st.subheader("Right Now")
    # st.write ("Map indicates last observed positions of all NJTransit buses statewide.")
    #
    #
    #
    # map = folium.Map(
    #     location=[39.833851,-74.871826],
    #     # tiles='Stamen Toner',
    #     # tiles='Stamen Terrain',
    #     # tiles='CartoDB Dark Matter',
    #     tiles='CartoDB Positron',
    #     zoom_start=8)
    # mapdata = requests.get(positions_url, timeout=5)
    # # get bounding box
    # points = [(f['geometry']['coordinates'][0], f['geometry']['coordinates'][1]) for f in json.loads(mapdata.content)['features']]
    # sw = min(points)[1], min(points)[0]
    # ne = max(points)[1], max(points)[0]
    # map.fit_bounds([sw, ne])
    # # draw map
    # folium.GeoJson(
    #     json.loads(mapdata.content),
    #     name="geojson",
    #     marker = folium.CircleMarker(radius = 3, # Radius in metres
    #                                  weight = 1, #outline weight
    #                                  color = '#ffffff',
    #                                  fill_color = '#efcc00',
    #                                  fill_opacity = 1),
    #     tooltip = folium.GeoJsonTooltip(fields = ['rt', 'id', 'fs'],
    #                                     aliases=['Route: ', 'Bus ID:', 'Headsign:'],
    #                                     style = ("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"),
    #                                     sticky = True
    #                                     )
    # ).add_to(map)
    # folium_static(map)


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
    # https://gist.github.com/bendichter/d7dccacf55c7d95aec05c6e7bcf4e66e

    # MIT LICENSE

    st.subheader("History")

    from plotly import subplots
    import datetime
    import plotly.graph_objs as go

    def display_year(z,
                     year: int = None,
                     month_lines: bool = True,
                     fig=None,
                     row: int = None):

        if year is None:
            year = datetime.datetime.now().year

        data = np.ones(365) * np.nan
        data[:len(z)] = z


        d1 = datetime.date(year, 1, 1)
        d2 = datetime.date(year, 12, 31)

        delta = d2 - d1

        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        month_days =   [31,    28,    31,     30,    31,     30,    31,    31,    30,    31,    30,    31]
        month_positions = (np.cumsum(month_days) - 15)/7

        dates_in_year = [d1 + datetime.timedelta(i) for i in range(delta.days+1)] #gives me a list with datetimes for each day a year
        weekdays_in_year = [i.weekday() for i in dates_in_year] #gives [0,1,2,3,4,5,6,0,1,2,3,4,5,6,…] (ticktext in xaxis dict translates this to weekdays

        weeknumber_of_dates = [int(i.strftime("%V")) if not (int(i.strftime("%V")) == 1 and i.month == 12) else 53
                               for i in dates_in_year] #gives [1,1,1,1,1,1,1,2,2,2,2,2,2,2,…] name is self-explanatory
        text = [str(i) for i in dates_in_year] #gives something like list of strings like ‘2018-01-25’ for each date. Used in data trace to make good hovertext.
        #4cc417 green #347c17 dark green
        colorscale=[[False, '#eeeeee'], [True, '#76cf63']]

        # handle end of year


        data = [
            go.Heatmap(
                x=weeknumber_of_dates,
                y=weekdays_in_year,
                z=data,
                text=text,
                hoverinfo='text',
                xgap=3, # this
                ygap=3, # and this is used to make the grid-like apperance
                showscale=False,
                colorscale=colorscale
            )
        ]


        if month_lines:
            kwargs = dict(
                mode='lines',
                line=dict(
                    color='#9e9e9e',
                    width=1
                ),
                hoverinfo='skip'

            )
            for date, dow, wkn in zip(dates_in_year,
                                      weekdays_in_year,
                                      weeknumber_of_dates):
                if date.day == 1:
                    data += [
                        go.Scatter(
                            x=[wkn-.5, wkn-.5],
                            y=[dow-.5, 6.5],
                            **kwargs
                        )
                    ]
                    if dow:
                        data += [
                            go.Scatter(
                                x=[wkn-.5, wkn+.5],
                                y=[dow-.5, dow - .5],
                                **kwargs
                            ),
                            go.Scatter(
                                x=[wkn+.5, wkn+.5],
                                y=[dow-.5, -.5],
                                **kwargs
                            )
                        ]


        layout = go.Layout(
            # title='Daily Observations—history',
            height=250,
            yaxis=dict(
                showline=False, showgrid=False, zeroline=False,
                tickmode='array',
                ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                tickvals=[0, 1, 2, 3, 4, 5, 6],
                autorange="reversed"
            ),
            xaxis=dict(
                showline=False, showgrid=False, zeroline=False,
                tickmode='array',
                ticktext=month_names,
                tickvals=month_positions
            ),
            font={'size':10, 'color':'#9e9e9e'},
            plot_bgcolor=('#fff'),
            margin = dict(t=40),
            showlegend=False
        )

        if fig is None:
            fig = go.Figure(data=data, layout=layout)
        else:
            fig.add_traces(data, rows=[(row+1)]*len(data), cols=[1]*len(data))
            fig.update_layout(layout)
            fig.update_xaxes(layout['xaxis'])
            fig.update_yaxes(layout['yaxis'])


        return fig


    def display_years(z, years):
        fig = subplots.make_subplots(rows=len(years), cols=1, subplot_titles=years)
        for i, year in enumerate(years):
            data = z[i*365 : (i+1)*365]
            display_year(data, year=year, fig=fig, row=i)
            fig.update_layout(height=250*len(years))
        return fig


    def generate_data():
        heatmap_data = dash_data['observations_by_date']
        format = '%Y-%m-%d'
        start = dt.datetime.strptime(heatmap_data[0]['date'], format)
        num_dates = len(heatmap_data)
        dates = [start + dt.timedelta(days=x) for x in range(0, num_dates)]
        data = [d['num'] for d in heatmap_data]
        # return dates, data
        return (start.year, dates[-1].year), data

    years, data = generate_data()
    if len(years) == 1:
        years = (years[0],)
    elif len(years) > 1:
        span = int(years[-1]) == int(years[0])
        if span == 1:
            years = (years[0],)
        elif span > 1:
            years = ([y for y in years])
    st.plotly_chart(display_years(data, years))




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
