import statistics

from simulatingrisk.hawkdove.model import HawkDoveModel, HawkDoveAgent


class HawkDoveVariableRiskAgent(HawkDoveAgent):
    """
    An agent with random risk attitude playing Hawk or Dove. Optionally
    adjusts risks based on most successful neighbor, depending on model
    configuration.
    """

    def set_risk_level(self):
        # risk level is based partially on neighborhood size,
        #  which is configurable at the model level
        num_neighbors = 8 if self.model.include_diagonals else 4
        # generate a random risk level
        self.risk_level = self.random.randint(0, num_neighbors)

    def play(self):
        super().play()
        # when enabled by the model, periodically adjust risk level
        if self.model.adjustment_round:
            self.adjust_risk()

    @property
    def most_successful_neighbor(self):
        """identify and return the neighbor with the most points"""
        # sort neighbors by points, highest points first
        # adapted from risky bet wealthiest neighbor
        return sorted(self.neighbors, key=lambda x: x.points, reverse=True)[0]

    def adjust_risk(self):
        # look at neighbors
        # if anyone has more points
        # either adopt their risk attitude or average theirs with yours

        best = self.most_successful_neighbor
        # if most successful neighbor has more points and a different
        # risk attitude, adjust
        if best.points > self.points and best.risk_level != self.risk_level:
            # adjust risk based on model configuration
            if self.model.risk_adjustment == "adopt":
                # adopt neighbor's risk level
                self.risk_level = best.risk_level
            elif self.model.risk_adjustment == "average":
                # average theirs with mine, then round to a whole number
                # since this model uses discrete risk levels
                self.risk_level = round(
                    statistics.mean([self.risk_level, best.risk_level])
                )


class HawkDoveVariableRiskModel(HawkDoveModel):
    """
    Model for hawk/dove game with variable risk attitudes.

    :param grid_size: number for square grid size (creates n*n agents)
    :param include_diagonals: whether agents should include diagonals
        or not when considering neighbors (default: True)
    :param hawk_odds: odds for playing hawk on the first round (default: 0.5)
    :param risk_adjustment: strategy agents should use for adjusting risk;
        None (default), adopt, or average
    :param adjust_every: when risk adjustment is enabled, adjust every
        N rounds (default: 10)
    """

    risk_attitudes = "variable"
    agent_class = HawkDoveVariableRiskAgent

    supported_risk_adjustments = (None, "adopt", "average")

    def __init__(
        self,
        grid_size,
        include_diagonals=True,
        hawk_odds=0.5,
        risk_adjustment=None,
        adjust_every=10,
    ):
        super().__init__(
            grid_size, include_diagonals=include_diagonals, hawk_odds=hawk_odds
        )
        # convert string input from solara app parameters to None
        if risk_adjustment == "none":
            risk_adjustment = None
        # make sure risk adjustment is valid
        if risk_adjustment not in self.supported_risk_adjustments:
            risk_adjust_opts = ", ".join(
                [opt or "none" for opt in self.supported_risk_adjustments]
            )
            raise ValueError(
                f"Unsupported risk adjustment '{risk_adjustment}'; "
                + f"must be one of {risk_adjust_opts}"
            )

        self.risk_adjustment = risk_adjustment
        self.adjust_round_n = adjust_every

    @property
    def adjustment_round(self) -> bool:
        """is the current round an adjustment round?"""
        # check if the current step is an adjustment round
        # when risk adjustment is enabled, agents should adjust their risk
        # strategy every N rounds;
        return (
            self.risk_adjustment
            and self.schedule.steps > 0
            and self.schedule.steps % self.adjust_round_n == 0
        )
