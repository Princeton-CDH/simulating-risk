import sys
from flask import Flask
from solara.server.flask import blueprint
from solara.server.app import apps, AppScript

sys.path.insert(0, "..")

# start flask app
app = Flask(__name__)

# get first blueprint?

apps["__default__"] = AppScript("../simulatingrisk/risky_bet/app.py")
app.register_blueprint(blueprint, url_prefix="/risky_bet/")

# get second blueprint?
# apps["__default__"] = AppScript("../simulatingrisk/hawkdove/app.py")
# app.register_blueprint(blueprint, url_prefix="/hawkdove/", name="hawkdove")


# boiler plate
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
