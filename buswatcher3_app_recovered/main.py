
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from lib.Layout import *
from config import config

app = dash.Dash( __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],external_stylesheets=[dbc.themes.PULSE, '/assets/styles.css'])
server = app.server
app.config['suppress_callback_exceptions'] = True # # suppress callback warnings

# layout scaffold
app.layout = create_layout(app, config.source, config.routes)
# app.layout = html.Div([dcc.Location(id="url", refresh=False),html.Div(id="page-content")])
#
# # callback
# @app.callback(
#         Output("page-content", "children"),
#         [Input("url", "pathname")])
# def display_page(pathname):
#
#     if pathname is None:
#         return 'Loading...'
#     elif pathname == '/':
#         active_route='87'
#         return create_layout(app, routes_watching, active_route)
#     else:
#         active_route=(pathname[1:])
#         return create_layout(app, routes_watching, active_route)



#######################################################################################
# __MAIN__
#######################################################################################
if __name__ == "__main__":
    app.run_server(debug=True)
