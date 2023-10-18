from simulatingrisk.hawkdove.model import HawkDoveModel, HawkDoveAgent


class HawkDoveVariableRiskAgent(HawkDoveAgent):
    """
    An agent with random risk attitude playing Hawk or Dove
    """

    def set_risk_level(self):
        # risk level is based partially on neighborhood size,
        #  which is configurable at the model level
        num_neighbors = 8 if self.model.include_diagonals else 4
        # generate a random risk level
        self.risk_level = self.random.randint(0, num_neighbors)


class HawkDoveVariableRiskModel(HawkDoveModel):
    risk_attitudes = "variable"
    agent_class = HawkDoveVariableRiskAgent

    def __init__(
        self,
        grid_size,
        include_diagonals=True,
        hawk_odds=0.5,
    ):
        super().__init__(
            grid_size, include_diagonals=include_diagonals, hawk_odds=hawk_odds
        )
        # no custom logic or params yet, but will be adding risk updating logic
