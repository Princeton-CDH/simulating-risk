import mesa

from simulatingrisk.risky_food.model import RiskyFoodModel
from simulatingrisk.risky_food.server import (
    chart,
    risk_chart,
    total_agent_chart,
    histogram,
)


server = mesa.visualization.ModularServer(
    RiskyFoodModel,
    # [chart, risk_chart, agent_risk_chart, total_agent_chart],
    [chart, risk_chart, total_agent_chart, histogram],
    "Risky Food",
    {"n": 20, "mode": "types"},
)
server.port = 8521  # The default
server.launch()
