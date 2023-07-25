import mesa

from simulatingrisk.risky_food.model import RiskyFoodModel


chart = mesa.visualization.ChartModule(
    [
        {"Label": "prob_notcontaminated", "Color": "blue"},
        {"Label": "contaminated", "Color": "red"},
    ],
    data_collector_name="datacollector",
    canvas_height=100,  # default height is 200
)
risk_chart = mesa.visualization.ChartModule(
    [
        {"Label": "average_risk_level", "Color": "blue"},
        {"Label": "min_risk_level", "Color": "green"},
        {"Label": "max_risk_level", "Color": "orange"},
    ],
    data_collector_name="datacollector",
    canvas_height=100,
)

total_agent_chart = mesa.visualization.ChartModule(
    [
        {"Label": "num_agents", "Color": "gray"},
    ],
    data_collector_name="datacollector",
    canvas_height=100,
)

server = mesa.visualization.ModularServer(
    RiskyFoodModel,
    # [chart, risk_chart, agent_risk_chart, total_agent_chart],
    [chart, risk_chart, total_agent_chart],
    "Risky Food",
    {"n": 20, "mode": "types"},
)
server.port = 8521  # The default
server.launch()
