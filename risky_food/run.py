import mesa

from risky_food.model import RiskyFoodModel

chart = mesa.visualization.ChartModule(
    [
        {"Label": "prob_notcontaminated", "Color": "blue"},
        {"Label": "contaminated", "Color": "red"},
    ],
    data_collector_name="datacollector",
)

server = mesa.visualization.ModularServer(
    RiskyFoodModel, [chart], "Risky Food", {"n": 20}
)
server.port = 8521  # The default
server.launch()
