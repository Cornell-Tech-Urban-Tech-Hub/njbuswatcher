import logging
import dash


from lib.Layout import *
from config import config


app = dash.Dash( __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],external_stylesheets=[dbc.themes.PULSE, '/assets/styles.css'])
server = app.server
app.config['suppress_callback_exceptions'] = True # # suppress callback warnings

# layout scaffold
app.layout = create_layout(app, config.source, config.routes)


################################################
# MAIN SCRIPT
################################################

if __name__ == "__main__":
    app.run_server(host='0.0.0.0', debug=True)

# after https://medium.com/@trstringer/logging-flask-and-gunicorn-the-manageable-way-2e6f0b8beb2f
if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


