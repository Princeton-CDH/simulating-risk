import statistics
from collections import Counter
from enum import IntEnum

from simulatingrisk.hawkdove.model import HawkDoveModel, HawkDoveAgent


class HawkDoveMultipleRiskAgent(HawkDoveAgent):
    """
    An agent with random risk attitude playing Hawk or Dove. Optionally
    adjusts risks based on most successful neighbor, depending on model
    configuration.
    """

    def set_risk_level(self):
        # risk level is based partially on neighborhood size,
        #  which is configurable at the model level

        # generate a random risk level between zero and 8
        # (using same range for all neighborhood sizes)
        self.risk_level = self.random.randint(
            self.model.min_risk_level, self.model.max_risk_level
        )

    def play(self):
        super().play()
        # when enabled by the model, periodically adjust risk level
        if self.model.adjustment_round:
            self.adjust_risk()

    @property
    def adjust_neighbors(self):
        """neighbors to look at when adjusting risk attitude; uses
        model adjust_neighborhood size"""
        return self.get_neighbors(self.model.adjust_neighborhood)

    @property
    def most_successful_neighbor(self):
        """identify and return the neighbor with the most points"""
        # sort neighbors by points, highest points first
        # adapted from risky bet wealthiest neighbor
        return sorted(self.adjust_neighbors, key=lambda x: x.points, reverse=True)[0]

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


class RiskState(IntEnum):
    """Categorization of population risk states"""

    # majority risk inclined
    c1 = 1
    c2 = 2
    c3 = 3
    c4 = 4

    # majority risk moderate
    c5 = 5
    c6 = 6
    c7 = 7
    c8 = 8

    # majority risk avoidant
    c9 = 9
    c10 = 10
    c11 = 11
    c12 = 12

    # no clear majority
    c13 = 13

    @classmethod
    def category(cls, val):
        # handle both integer and risk state enum value
        if isinstance(val, RiskState):
            val = val.value
        if val in {1, 2, 3, 4}:
            return "majority risk inclined"
        if val in {5, 6, 7, 8}:
            return "majority risk moderate"
        if val in {9, 10, 11, 12}:
            return "majority risk avoidant"
        return "no majority"


class HawkDoveMultipleRiskModel(HawkDoveModel):
    """
    Model for hawk/dove game with variable risk attitudes.  Supports
    all parameters in :class:`~simulatingrisk.hawkdove.model.HawkDoveModel`
    and adds several parmeters to control if and how agents adjust
    their risk attitudes (strategy, frequency, and neighborhood size).

    :param risk_adjustment: strategy agents should use for adjusting risk;
        None (default), adopt, or average
    :param adjust_every: when risk adjustment is enabled, adjust every
        N rounds (default: 10)
    :param adjust_neighborhood: size of neighborhood to look at when
        adjusting risk attitudes; 4, 8, or 24 (default: play_neighborhood)
    """

    risk_attitudes = "variable"
    agent_class = HawkDoveMultipleRiskAgent

    supported_risk_adjustments = (None, "adopt", "average")

    def __init__(
        self,
        grid_size,
        risk_adjustment=None,
        adjust_every=10,
        adjust_neighborhood=None,
        *args,
        **kwargs,
    ):
        super().__init__(grid_size, *args, **kwargs)
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
        # if adjust neighborhood is not specified, then use the same size
        # as play neighborhood
        self.adjust_neighborhood = adjust_neighborhood or self.play_neighborhood

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

    def get_data_collector_options(self):
        # in addition to common hawk/dove data points,
        # we want to include population risk category
        opts = super().get_data_collector_options()
        opts["model_reporters"]["population_risk_category"] = "population_risk_category"
        return opts

    @property
    def population_risk_category(self):
        # calculate a category of risk distribution for the population
        # based on the proportion of agents in different risk categories
        # (categorization scheme defined by LB)

        # tally the number of agents with each risk level
        risk_counts = Counter([a.risk_level for a in self.schedule.agents])
        # count the number of agents in three groups:
        #  Risk-inclined (RI) : r = 0, 1, 2
        #  Risk-moderate (RM): r = 3, 4, 5
        #  Risk-avoidant (RA): r = 6, 7, 8
        total = {
            "risk_inclined": risk_counts[0] + risk_counts[1] + risk_counts[2],
            "risk_moderate": risk_counts[3] + risk_counts[4] + risk_counts[5],
            "risk_avoidant": risk_counts[6] + risk_counts[7] + risk_counts[8],
        }
        # for each group, calculate percent of agents in that category
        total_agents = len(self.schedule.agents)
        percent = {key: val / total_agents for key, val in total.items()}

        # majority risk inclined (> 50%)
        if percent["risk_inclined"] > 0.5:
            # If < 10% are RM & < 10% are RA: let c = 1
            if percent["risk_moderate"] < 0.1 and percent["risk_avoidant"] < 0.1:
                return RiskState.c1
            # If > 10% are RM & < 10% are RA: let c = 2
            if percent["risk_moderate"] > 0.1 and percent["risk_avoidant"] < 0.1:
                return RiskState.c2
            # If > 10% are RM & > 10% are RA: let c = 3
            if percent["risk_moderate"] > 0.1 and percent["risk_avoidant"] > 0.1:
                return RiskState.c3
            # If < 10% are RM & > 10% are RA: let c = 4
            if percent["risk_moderate"] < 0.1 and percent["risk_avoidant"] > 0.1:
                return RiskState.c4

        # majority risk moderate
        if percent["risk_moderate"] > 0.5:
            # If < 10% are RI & < 10% are RA: let c = 7
            if percent["risk_inclined"] < 0.1 and percent["risk_avoidant"] < 0.1:
                return RiskState.c7
            # If > 10% are RI & < 10% are RA: let c = 5
            if percent["risk_inclined"] > 0.1 and percent["risk_avoidant"] < 0.1:
                return RiskState.c5
            # If > 10% are RI & > 10% are RA: let c = 6
            if percent["risk_inclined"] > 0.1 and percent["risk_avoidant"] > 0.1:
                return RiskState.c6
            # If < 10% are RI & > 10% are RA: let c = 8
            if percent["risk_inclined"] < 0.1 and percent["risk_avoidant"] > 0.1:
                return RiskState.c8

        # majority risk avoidant
        if percent["risk_avoidant"] > 0.5:
            # If < 10% are RM & < 10% are RI: let c = 12
            if percent["risk_moderate"] < 0.1 and percent["risk_inclined"] < 0.1:
                return RiskState.c12
            # If > 10% are RM & < 10% are RI: let c = 11
            if percent["risk_moderate"] > 0.1 and percent["risk_inclined"] < 0.1:
                return RiskState.c11
            # If > 10% are RM & > 10% are RI: let c = 10
            if percent["risk_moderate"] > 0.1 and percent["risk_inclined"] > 0.1:
                return RiskState.c10
            # If < 10% are RM & > 10% are RI: let c = 9
            if percent["risk_moderate"] < 0.1 and percent["risk_inclined"] > 0.1:
                return RiskState.c9

        return RiskState.c13
