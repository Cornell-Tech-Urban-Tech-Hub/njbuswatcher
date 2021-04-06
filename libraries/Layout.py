# -*- coding: utf-8 -*-

import dash_html_components as html
import dash_bootstrap_components as dbc

from . import NJTransitAPI as api

# from pathlib import Path
# import pandas as pd
# from sklearn.datasets import make_blobs
# import random
# import numpy as np
# from dash.dependencies import Input, Output
# import plotly.graph_objs as go
# import plotly.figure_factory as ff
# from plotly.colors import n_colors
# import plotly.express as px



#######################################################################################
# PAGE LAYOUT
#######################################################################################

def create_layout(app, source, routes):

    return html.Div(
        [
            dbc.Container(
                            [
                                get_navbar(),
                                html.Br([]),
                            ],
                            fluid=True,
                            className='p-0'
            ),

            dbc.Container (

                [

                    # call to action box
                    dbc.Row(
                        [
                            dbc.Col(
                                [

                                    dbc.Jumbotron(
                                        [
                                            dbc.Alert("Dues to a major change in NJTransit's real-time data services during the COVID-19 crisis, we are currently rebuilding our site to serve you better. We will update the site on a rolling basis, so please check back soon.", color="danger"),
                                            html.H1("How Are New Jersey's Buses Doing?", className="display-3"),
                                            html.Br([]),
                                            # get_route_menu(routes_watching, active_route),
                                            html.Hr(className="my-2"),
                                            html.P(
                                                "Residents and businesses depend on NJTransit buses every day. \
                                                But it can be hard to evaluate the quality of bus service.\
                                                We built this site to provide a one-stop shop for bus \
                                                performance information. Here you can see how bus service is operating today \
                                                and get insights on overall performance.", className="lead"
                                            ),
                                            html.P(
                                                "Curently we are tracking routes {}".format(format_route_list(routes)), className="lead"
                                            ),
                                            html.Br([]),
                                            html.H5("Current Service: {}".format(format_route_list(routes)), className="display-5"),
                                            html.Br([]),
                                            get_current_bus_positions_block(source, routes)
                                            # html.P(dbc.Button("Learn more", color="primary"), className="lead"),
                                        ]
                                    )
                                ]

                            )
                        ]
                    ),



                    # # row2
                    # dbc.Row(
                    #     [
                    #         dbc.Col(
                    #
                    #             [
                    #                 html.H5("Current Bus Locations", className="display-5"),
                    #                 html.Br([])
                    #             ]
                    #         )
                    #     ]
                    # ),


                    # # row2
                    # dbc.Row(
                    #     [
                    #         dbc.Col(
                    #
                    #                 [
                    #                     html.H5("How Often Do Buses Arrive?", className="display-5"),
                    #
                    #                     html.P("A pseudo-Latin text used in web design, typography, layout, and printing in \
                    #                             place of English to emphasize design elements over content. It's also called placeholder \
                    #                             (or filler) text. It's a convenient tool for mock-ups."),
                    #
                    #
                    #
                    #                     html.Br([]),
                    #
                    #                 ]
                    #             ),
                    #         dbc.Col(
                    #
                    #             [
                    #                 html.H5("How Reliable Is Travel Time?", className="display-5"),
                    #
                    #                 html.P("A pseudo-Latin text used in web design, typography, layout, and printing in \
                    #                         place of English to emphasize design elements over content."),
                    #
                    #
                    #
                    #                 html.Br([]),
                    #             ]
                    #         )
                    #     ]
                    # ),

                    # # row2
                    # dbc.Row(
                    #     [
                    #         dbc.Col(
                    #
                    #             [
                    #
                    #                 dcc.Graph(
                    #                     figure=make_chart_bar(get_report(active_route, "frequency")),
                    #                     style={'width': '50vh', 'height': '35vh'}
                    #                 ),
                    #
                    #                 html.Br([]),
                    #
                    #             ]
                    #         ),
                    #         dbc.Col(
                    #
                    #             [
                    #
                    #
                    #                 dcc.Graph(
                    #                     figure=make_chart_line(get_report(active_route, "reliability")),
                    #                     style={'width': '50vh', 'height': '35vh'}
                    #                 ),
                    #
                    #                 html.Br([]),
                    #             ]
                    #         )
                    #     ]
                    # ),

                    # # row3 bunching graph
                    # dbc.Row(
                    #     [
                    #         dbc.Col(
                    #             [
                    #                 html.H5("Where Are the Bottlenecks?".format(active_route), className="display-5"),
                    #
                    #                 html.P("Lorem ipsum dolor sit amet, consectetuer adipiscing elit. \
                    #                 Aenean commodo ligula eget dolor. Aenean massa.", ),
                    #
                    #                 dcc.Graph(
                    #                     figure=make_ridgeline_plot(active_route),
                    #                 style={'width': '100vh', 'height': '50vh'}),
                    #
                    #                 html.Br([]),
                    #
                    #
                    #
                    #             ]
                    #         )
                    #     ]
                    # ),



                ]


            )

        ],
        # className="p-5",
        style={'backgroundColor': 'white'}
    )



#######################################################################################
# LAYOUT COMPONENTS
#######################################################################################

def get_navbar():

    navbar = dbc.NavbarSimple(
                                children=[
                                    dbc.NavItem(dbc.NavLink("What is this?", href="/about")),
                                    dbc.DropdownMenu(
                                        children=[
                                            dbc.DropdownMenuItem("More pages", header=True),
                                            dbc.DropdownMenuItem("Page 2", href="#"),
                                            dbc.DropdownMenuItem("Page 3", href="#"),
                                        ],
                                        nav=True,
                                        in_navbar=True,
                                        label="More",
                                    ),
                                ],
                                brand="NJBusWatcher",
                                brand_href="#",
                                color="primary",
                                dark=True,
                            )
    return navbar


def format_route_list(routes):
    routes=[route for route, routedata in routes.items()]
    formatted_route_list = ""
    print (type(routes))
    for route in routes[:-1]:
        formatted_route_list=formatted_route_list+(route+', ')
    formatted_route_list = formatted_route_list + 'and '+ routes[-1] + '.'

    # formatted_route_list = formatted_route_list[-1] + ('and '+routes[:-1])

    return formatted_route_list





def get_current_bus_positions_block(source, routes):

    table_header = [html.Thead(html.Tr(
        [html.Th("route"), html.Th("v_id"), html.Th("op_id"), html.Th("lat"), html.Th("lon"), html.Th("run"),
         html.Th("pid"), html.Th("destination")]))]

    table_rows = []
    for route in routes:
        response = api.get_xml_data(source,'buses_for_route',route=route)
        buses = api.parse_xml_getBusesForRoute(response)

        for bus in buses:
            html_row = []
            # manually add fields from bus object
            html_row.append(html.Td(bus.rt))
            html_row.append(html.Td(bus.id))
            html_row.append(html.Td(bus.op))
            html_row.append(html.Td("{:.4f}".format(float(bus.lat))))
            html_row.append(html.Td("{:.4f}".format(float(bus.lon))))
            html_row.append(html.Td(bus.run))
            html_row.append(html.Td(bus.pid))
            html_row.append(html.Td(bus.dd))

            table_rows.append(html.Tr(html_row))

    table_body = [html.Tbody(table_rows)]

    return dbc.Table(table_header + table_body, bordered=False)




    # # if want to have maps too, make 2 columns inside, with the map in the left column
    # dummy_row = dbc.Row(
    #                         [
    #                           dbc.Col(
    #                                    [
    #                                      html.H5("Dummy Column ina Dummy Row", className="display-5"),
    #                                      html.P("Dummy text in a dummy row. Oh so dummy.", className="lead"),
    #                                      html.Br([])
    #                                     ]
    #                                 )
    #                         ]
    #                     )
    #
    #
    # # take this out of a container, just return the list of rows?
    # placeholder = dbc.Container (
    #                     [ dummy_row,
    #                       dummy_row
    #                       ]
    #                 )


    return dbc.Container (rows)


def make_table_from_df(df):
    """ Return a dash definition of an HTML table for a Pandas dataframe """
    table = []
    for index, row in df.iterrows():
        html_row = []
        for i in range(len(row)):
            html_row.append(html.Td([row[i]]))
        table.append(html.Tr(html_row))
    return table




# def get_report(active_route, report):
#
#     DATA_PATH = get_data_path()
#
#     if report == "summary":
#
#         # for now, just use this dummy static template
#         start = 'Hoboken Terminal'
#         end = 'Journal Square'
#         description = 'The 87 snakes through The Heights, linking to important rail stations at Journal Square, \
#         the 9th Street Light Rail Station, and Hoboken Terminal. It has the worst bunching problems of all NJTransit \
#         routes in the area due to heavy traffic, railroad grade crossings, and more.'
#         speed = 14.5
#         stop_interval = 750
#         tpm = 2.1
#         grade = 'D'
#
#         summary_template = " The {routenum} runs from {start} to {end}. {description}. Average speed is {speed}, thanks \
#                            to an average of {stop_interval} feet between stops and {tpm} turns per mile. "\
#                             .format(routenum=active_route,start=start,end=end,description=description,\
#                                     speed=speed,stop_interval=stop_interval,tpm=tpm)
#
#
#         # from route_desciptions.json:
#         #       origin, destination, geometry statistics=distance between stops, turns per mile (to build in TransitSystem)
#         # from travel_time? #to build in Generators
#         #       average speed
#         # from a new all-routes-grades.csv file (to build in Generators)
#         #       overall_grade
#
#
#         return summary_template
#
#     else:
#         return pd.read_csv('{}/{}_{}.csv'.format(DATA_PATH, active_route, report), quotechar='"')

#
# def get_route_menu(routes_watching, active_route):
#
#     # future restore the dropdown menu?
#
#     badges = []
#     for route in routes_watching:
#             if route==active_route:
#                 badges.append(dbc.Badge(route, pill=True, color="primary", className="mr-1"))
#             else:
#                 badges.append(dbc.Badge(route, href="/{}".format(route), pill=True, color="secondary", className="mr-1"))
#     route_menu = html.Span(badges)
#
#
#     return route_menu




# def make_chart_line(df):
#

#     # https://plotly.com/python/line-charts/#filled-lines
#
#     fig = px.line(df, x="hour", y=" minutes", title='End-to-End Travel time')
#
#     fig.update_layout(autosize=True,
#                       title="",
#                       font={"family": "Raleway", "size": 10},
#                       # height=200,
#                       # width=340,
#                       hovermode="closest",
#                       margin={
#                           "r": 20,
#                           "t": 20,
#                           "b": 40,
#                           "l": 50,
#                       },
#                       showlegend=False,
#                       xaxis={
#                           "autorange": True,
#                           "linecolor": "rgb(0, 0, 0)",
#                           "linewidth": 1,
#                           "range": [6, 16],
#                           "showgrid": False,
#                           "showline": True,
#                           "title": "",
#                           "type": "linear",
#                       },
#                       yaxis={
#                           "autorange": False,
#                           "gridcolor": "rgba(127, 127, 127, 0.2)",
#                           "mirror": False,
#                           "nticks": 4,
#                           "range": [0, 150],
#                           "showgrid": True,
#                           "showline": True,
#                           "ticklen": 10,
#                           "ticks": "outside",
#                           "title": "minutes",
#                           "type": "linear",
#                           "zeroline": False,
#                           "zerolinewidth": 4,
#                       },
#                       )
#
#     fig.update_xaxes(
#         ticktext=["6am", "12pm", "6pm"],
#         tickvals=['6', '12', '18'],
#     )
#
#     return fig
#
#
# def make_chart_bar(df):
#     fig = px.bar(df, x="hour", y=" minutes", title='End-to-End Travel time')
#
#     fig.update_layout(autosize=True,
#                       title="",
#                       font={"family": "Raleway", "size": 10},
#                       # height=200,
#                       # width=340,
#                       hovermode="closest",
#                       margin={
#                           "r": 20,
#                           "t": 20,
#                           "b": 40,
#                           "l": 50,
#                       },
#                       showlegend=False,
#                       xaxis={
#                           "autorange": True,
#                           "linecolor": "rgb(0, 0, 0)",
#                           "linewidth": 1,
#                           "range": [6, 16],
#                           "showgrid": False,
#                           "showline": True,
#                           "title": "",
#                           "type": "linear",
#                       },
#                       yaxis={
#                           "autorange": False,
#                           "gridcolor": "rgba(127, 127, 127, 0.2)",
#                           "mirror": False,
#                           "nticks": 4,
#                           "range": [0, 150],
#                           "showgrid": True,
#                           "showline": True,
#                           "ticklen": 10,
#                           "ticks": "outside",
#                           "title": "minutes",
#                           "type": "linear",
#                           "zeroline": False,
#                           "zerolinewidth": 4,
#                       },
#                       )
#
#     fig.update_xaxes(
#         ticktext=["6am", "12pm", "6pm"],
#         tickvals=['6', '12', '18'],
#     )
#
#     return fig
#
#
# def make_curve_and_rug_plot(route):
#     # TEST DUMMY CURVE
#     # https://plotly.com/python/distplot/
#     # assumes that data is distance of each bunching incident on the route from the start
#
#     periods, data, colors = get_bunching_sample_data(route)
#
#     fig = ff.create_distplot(data, periods, show_hist=False, colors=colors)
#
#     fig.update_layout(
#         autosize=False,
#         # width=700,
#         # height=200,
#         margin=dict(
#             l=10,
#             r=10,
#             b=10,
#             t=10,
#             pad=4
#         ),
#         paper_bgcolor="White",
#         font=dict(
#             family="Garamond",
#             size=12,
#             color="#000000"
#         )
#     )
#
#
#
#     # Set custom x-axis labels
#     fig.update_xaxes(
#         ticktext=["Journal Square", "Palisade Av + Franklin Av", "Hoboken Terminal"],
#         tickvals=['0', '12500', '25000'],
#     )
#     #
#     # fig.update_xaxes(
#     #     ticktext=["a", "b", "c","d","e"],
#     #     tickvals=['0','5000','10000','12500','25000'],
#     # )
#
#     fig.update_yaxes(showticklabels=False)
#
#     return fig
#
#
# def make_ridgeline_plot(route):
#     periods, data, colors = get_bunching_sample_data(route)
#
#     fig = go.Figure()
#
#     for data_line, color, period in zip(data, colors, periods):
#         fig.add_trace(go.Violin(x=data_line, line_color=color, name=period))
#
#     fig.update_traces(orientation='h', side='positive', width=3, points=False)
#     fig.update_layout(xaxis_showgrid=False, xaxis_zeroline=False)
#
#     # Set custom x-axis labels
#     fig.update_xaxes(
#         ticktext=["Journal Square", "Palisade Av + Franklin Av", "Hoboken Terminal"],
#         tickvals=['0', '12500', '25000'],
#     )
#
#     # fig.update_xaxes(showticklabels=False)
#     fig.update_yaxes(showticklabels=False)
#
#     fig.update_layout(
#         # legend_orientation="h",
#         autosize=True,
#         # width=720,
#         # height=400,
#         margin=dict(
#             l=0,
#             r=0,
#             b=0,
#             t=0,
#             pad=0
#         ),
#         paper_bgcolor="White",
#         font=dict(
#             family="Garamond",
#             size=12,
#             color="#000000"
#         )
#     )
#
#     fig.update_layout(
#         legend=dict(
#             traceorder="reversed"
#         )
#     )
#
#     fig.update_xaxes(range=[0, 25000])
#
#     return fig


# #######################################################################################
# # HELPERS
# #######################################################################################
#
# def get_data_path():
#     PATH = Path(__file__).parent
#     return PATH.joinpath("../data").resolve()
#
#
# def get_bunching_sample_data(route):
#
#     DATA_PATH = get_data_path()
#
#     periods = ['am', 'midday', 'pm', 'late', 'weekends']
#     data = []
#     for period in periods:
#         ## load data from CSV
#         # data.append(np.loadtxt('{}/{}_{}_{}.csv'.format(DATA_PATH, route, "bunching", period), skiprows=1))
#
#         ## OR generate random data
#         n_centers = 50  # no of bunching points
#         bunches, y = make_blobs(n_samples=random.randint(1, 501), centers=n_centers, n_features=1,
#                                 center_box=(0.0, 25000))
#         data.append(bunches.flatten())
#
#     colors = n_colors('rgb(5, 200, 200)', 'rgb(200, 10, 10)', 5, colortype='rgb')
#     return periods, data, colors
#
