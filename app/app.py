import sys
from flask import Flask
from solara.server.flask import blueprint
from solara.server.app import apps, AppScript

sys.path.insert(0, "..")

# start flask app
app = Flask(__name__)

# get first blueprint?

apps["__default__"] = AppScript("../simulatingrisk/app.py")
app.register_blueprint(blueprint, url_prefix="/simulatingrisk/")

application = app
