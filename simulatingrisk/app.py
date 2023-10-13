import solara

from simulatingrisk.hawkdove.app import page as hawkdove_page
from simulatingrisk.risky_bet.app import page as riskybet_page
from simulatingrisk.risky_food.app import page as riskyfood_page


@solara.component
def Home():
    with open("simulatingrisk/about_app.md") as readmefile:
        return solara.Markdown("\n".join(readmefile.readlines()))


@solara.component
def hawkdove():
    return hawkdove_page


@solara.component
def riskybet():
    return riskybet_page


@solara.component
def riskyfood():
    return riskyfood_page


routes = [
    solara.Route(path="/", component=Home, label="Simulating Risk"),
    solara.Route(path="hawkdove", component=hawkdove, label="Hawk/Dove"),
    solara.Route(path="riskybet", component=riskybet, label="Risky Bet"),
    solara.Route(path="riskyfood", component=riskyfood, label="Risky Food"),
]
