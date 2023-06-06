import mesa

from risky_food.model import RiskyFoodModel

chart = mesa.visualization.ChartModule(
    [
        {"Label": "prob_notcontaminated", "Color": "blue"},
        {"Label": "contaminated", "Color": "red"},
    ],
    data_collector_name="datacollector",
)
risk_chart = mesa.visualization.ChartModule(
    [
        {"Label": "average_risk_level", "Color": "blue"},
        {"Label": "min_risk_level", "Color": "green"},
        {"Label": "max_risk_level", "Color": "orange"},
    ],
    data_collector_name="datacollector",
)

agent_chart = mesa.visualization.ChartModule(
    [
        {"Label": "num_agents", "Color": "gray"},
    ],
    data_collector_name="datacollector",
)

server = mesa.visualization.ModularServer(
    RiskyFoodModel, [chart, risk_chart, agent_chart], "Risky Food", {"n": 20}
)
server.port = 8521  # The default
server.launch()
