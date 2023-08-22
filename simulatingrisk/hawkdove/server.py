"""
Configure visualization elements and instantiate a server
"""

from simulatingrisk.hawkdove.model import Play


def agent_portrayal(agent):
    from simulatingrisk.hawkdove.model import divergent_colors_9, divergent_colors_5

    # initial display
    portrayal = {
        # styles for mesa runserver
        "Shape": "circle",
        # "Color": "gray",
        # "Filled": "true",
        "Layer": 0,
        "r": 0.2,
        "risk_level": agent.risk_level,
        "choice": str(agent.choice)
        # styles for solara / jupyterviz
        # "size": 25,
        # "color": "tab:gray",
    }

    # color based on risk level
    if agent.model.include_diagonals:
        colors = divergent_colors_9
    else:
        colors = divergent_colors_5
    portrayal["Color"] = colors[agent.risk_level]
    # copy to lowercase color for solara
    portrayal["color"] = portrayal["Color"]

    # filled for hawks, hollow for doves
    # (shapes would be better...)
    portrayal["Filled"] = agent.choice == Play.HAWK

    # size based on points within current distribution after first round
    if agent.points > 0:
        # # set radius based on relative points, but don't go smaller than 1 radius
        # # or too large to fit in the grid
        portrayal["r"] = (agent.points_rank / 15) + 0.2
        # # size for solara / jupyterviz
        portrayal["size"] = (agent.points_rank / 15) * 50

    return portrayal


grid_size = 10

model_params = {
    "grid_size": grid_size,
}


jupyterviz_params = {
    "grid_size": {
        "type": "SliderInt",
        "value": grid_size,
        "label": "Grid Size",
        "min": 10,
        "max": 100,
        "step": 1,
    },
    # "risk_adjustment": {
    #     "type": "Select",
    #     "value": "adopt",
    #     "values": ["adopt", "average"],
    #     "description": "How agents update their risk level",
    # },
}
