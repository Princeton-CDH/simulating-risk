import mesa

from simulatingrisk.hawkdove.model import HawkDoveModel
from simulatingrisk.hawkdove.server import (
    agent_portrayal,
    grid_size,
    model_params,
    # risk_bins,
)
from simulatingrisk.charts.histogram import HistogramModule


risk_histogram = HistogramModule(list(range(9)), 175, 500, "risk levels", "risk_level")
points_histogram = HistogramModule(
    list(range(10)), 45, 200, "cumulative payoff percentile", "points_rank"
)

grid = mesa.visualization.CanvasGrid(agent_portrayal, grid_size, grid_size, 500, 500)


server = mesa.visualization.ModularServer(
    HawkDoveModel,
    # [grid, histogram, world_chart, risk_chart],
    [grid, risk_histogram, points_histogram],
    "Hawk/Dove risk attitude Simulation",
    model_params=model_params,
)
server.port = 8521  # The default
server.launch()

server.launch()
