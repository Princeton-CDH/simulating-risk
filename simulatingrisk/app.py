import os.path

import solara

from simulatingrisk.hawkdove.app import page as hawkdove_page
from simulatingrisk.hawkdovemulti.app import page as hawkdove_multi_page
from simulatingrisk.risky_bet.app import page as riskybet_page
from simulatingrisk.risky_food.app import page as riskyfood_page


@solara.component
def Home():
    # load about markdown file in the same directory
    with open(os.path.join(os.path.dirname(__file__), "about_app.md")) as readmefile:
        return solara.Markdown("\n".join(readmefile.readlines()))


@solara.component
def hawkdove():
    return hawkdove_page


@solara.component
def hawkdove_multi():
    return hawkdove_multi_page


@solara.component
def riskybet():
    return riskybet_page


@solara.component
def riskyfood():
    return riskyfood_page


routes = [
    solara.Route(path="/", component=Home, label="Simulating Risk"),
    solara.Route(
        path="hawkdove-single", component=hawkdove, label="Hawk/Dove (single r)"
    ),
    solara.Route(
        path="hawkdove-multiple",
        component=hawkdove_multi,
        label="Hawk/Dove (multiple r)",
    ),
    solara.Route(path="riskybet", component=riskybet, label="Risky Bet"),
    solara.Route(path="riskyfood", component=riskyfood, label="Risky Food"),
]
