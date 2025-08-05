import statistics
from collections import Counter, deque
from enum import IntEnum
from functools import cached_property

from simulatingrisk.hawkdove.model import HawkDoveAgent, HawkDoveModel


class HawkDoveMultipleRiskAgent(HawkDoveAgent):
    """
    An agent with random risk attitude playing Hawk or Dove. Optionally
    adjusts risks based on most successful neighbor, depending on model
    configuration.
    """

    #: points since last adjustment round; starts at 0
    recent_points = 0

    #: whether or not risk level changed on the last adjustment round
    risk_level_changed = False

    def set_risk_level(self):
        # get risk attitude from model based on configured distribution
        self.risk_level = self.model.get_risk_attitude()

    def play(self):
        # save total points before playing so we only need to calculate
        # current round payoff once
        prev_points = self.points
        super().play()
        # when enabled by the model, periodically adjust risk level

        # add payoff from current round to recent points
        self.recent_points += self.points - prev_points

        if self.model.adjustment_round:
            self.adjust_risk()
            # reset to zero to track points until next adjustment round
            self.recent_points = 0

    @property
    def adjust_neighbors(self):
        """neighbors to look at when adjusting risk attitude; uses
        model adjust_neighborhood size"""
        return self.get_neighbors(self.model.adjust_neighborhood)

    @cached_property
    def compare_payoff_field(self):
        """determine which payoff to compare depending on model option:
        (cumulative/total or points since last adjustment round)"""
        return "recent_points" if self.model.adjust_payoff == "recent" else "points"

    @property
    def compare_payoff(self):
        """payoff value to use for adjustment comparison
        (depends on model configuration)"""
        return getattr(self, self.compare_payoff_field)

    @property
    def most_successful_neighbor(self):
        """identify and return the neighbor with the most points"""
        # sort neighbors by points, highest points first
        # adapted from risky bet wealthiest neighbor

        return sorted(
            self.adjust_neighbors,
            key=lambda x: getattr(x, self.compare_payoff_field),
            reverse=True,
        )[0]

    def adjust_risk(self):
        # look at neighbors
        # if anyone has more points
        # either adopt their risk attitude or average theirs with yours

        best = self.most_successful_neighbor

        # if most successful neighbor has more points and a different
        # risk attitude, adjust
        if (
            best.compare_payoff > self.compare_payoff
            and best.risk_level != self.risk_level
        ):
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

            # track that risk attitude has been updated
            self.risk_level_changed = True
        else:
            # track that risk attitude was not changed
            self.risk_level_changed = False


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

    def __str__(self):
        # override string method to return just the numeric value,
        # for better serialization of collected data
        return str(self.value)


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
    :param adjust_payoff: when comparing neighbors points for risk adjustment,
        consider cumulative payoff (`total`) or payoff since the
        last adjustment round (`recent`) (default: recent)
    """

    risk_attitudes = "variable"
    agent_class = HawkDoveMultipleRiskAgent

    supported_risk_adjustments = (None, "adopt", "average")
    supported_adjust_payoffs = ("recent", "total")
    risk_distribution_options = (
        "uniform",
        "normal",
        "skewed left",
        "skewed right",
        "bimodal",
    )

    def __init__(
        self,
        grid_size,
        risk_adjustment="adopt",
        risk_distribution="uniform",
        adjust_every=10,
        adjust_neighborhood=None,
        adjust_payoff="recent",
        *args,
        **kwargs,
    ):
        # convert string input from solara app parameters to None
        if risk_adjustment == "none":
            risk_adjustment = None

        # check parameters
        if risk_distribution not in self.risk_distribution_options:
            raise ValueError(
                f"Unsupported risk distribution '{risk_distribution}'; "
                + f"must be one of {', '.join(self.risk_distribution_options)}"
            )

        # make sure risk adjustment is valid
        if risk_adjustment not in self.supported_risk_adjustments:
            risk_adjust_opts = ", ".join(
                [opt or "none" for opt in self.supported_risk_adjustments]
            )
            raise ValueError(
                f"Unsupported risk adjustment '{risk_adjustment}'; "
                + f"must be one of {risk_adjust_opts}"
            )
        if adjust_payoff not in self.supported_adjust_payoffs:
            adjust_payoffs_opts = ", ".join(self.supported_adjust_payoffs)
            raise ValueError(
                f"Unsupported adjust payoff option '{adjust_payoff}'; "
                + f"must be one of {adjust_payoffs_opts}"
            )

        # initialize a risk attitude generator based on configured distrbution
        # must be set before calling super for agent init
        self.risk_distribution = risk_distribution
        self.risk_attitude_generator = self.get_risk_attitude_generator()

        super().__init__(grid_size, *args, **kwargs)

        self.risk_adjustment = risk_adjustment
        self.adjust_round_n = adjust_every
        # if adjust neighborhood is not specified, then use the same size
        # as play neighborhood
        self.adjust_neighborhood = adjust_neighborhood or self.play_neighborhood
        # store whether to compare cumulative payoff or since last adjustment round
        self.adjust_payoff = adjust_payoff

        self.recent_total_per_risk_level = deque([], maxlen=2)

    def _risk_level_in_bounds(self, value):
        # check if a generated risk level is within bounds
        return self.min_risk_level <= value <= self.max_risk_level

    def get_risk_attitude_generator(self):
        """return a generator that will return risk attitudes for individual
        agents based on the configured distribution."""
        if self.risk_distribution == "uniform":
            # uniform/random: generate random integer within risk level range
            while True:
                yield self.random.randint(self.min_risk_level, self.max_risk_level)
        if self.risk_distribution == "normal":
            # return values from a normal distribution centered around 4.5
            while True:
                yield round(self.random.gauss(4.5, 1.5))
        elif self.risk_distribution == "skewed left":
            # return values from a triangler distribution centered around 0
            while True:
                yield round(
                    self.random.triangular(self.min_risk_level, self.max_risk_level, 0)
                )
        elif self.risk_distribution == "skewed right":
            # return values from a triangular distribution centered around 9
            while True:
                yield round(
                    self.random.triangular(self.min_risk_level, self.max_risk_level, 9)
                )
        elif self.risk_distribution == "bimodal":
            # to generate a bimodal distribution, alternately generate
            # values from two different normal distributions centered
            # around the beginning and end of our risk attitude range
            while True:
                yield round(self.random.gauss(0, 1.5))
                yield round(self.random.gauss(9, 1.5))
                # NOTE: on smaller grids, using 0/9 makes it extremely
                # unlikely to get mid-range risk values (4/5)

    def get_risk_attitude(self):
        """return the next value from risk attitude generator, based on
        configured distribution."""
        val = next(self.risk_attitude_generator)

        # for bimodal distribution, clamp values to range
        if self.risk_distribution == "bimodal":
            return max(self.min_risk_level, min(self.max_risk_level, val))

        # for all other distributions:
        # occasionally generators will return values that are out of range.
        # rather than capping to the min/max and messing up the distribution,
        # just get the next value
        while not self._risk_level_in_bounds(val):
            val = next(self.risk_attitude_generator)
        return val

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
        model_reporters = {
            "population_risk_category": "population_risk_category",
            "num_agents_risk_changed": "num_agents_risk_changed",
            "sum_risk_level_changes": "sum_risk_level_changes",
        }
        for risk_level in range(self.min_risk_level, self.max_risk_level + 1):
            field = f"total_r{risk_level}"
            model_reporters[field] = field

        opts["model_reporters"].update(model_reporters)
        opts["agent_reporters"].update({"risk_level_changed": "risk_level_changed"})
        return opts

    def step(self):
        # delete cached property before the next round begins,
        # so we recalcate values for current round before collecting data
        try:
            # store risk level total for previous round
            if hasattr(self, "total_per_risk_level"):
                if (
                    not self.recent_total_per_risk_level
                    or self.total_per_risk_level != self.recent_total_per_risk_level[-1]
                ):
                    # add to recent values if changed or new
                    self.recent_total_per_risk_level.append(self.total_per_risk_level)
            # else:
            #     self.recent_total_per_risk_level.append(self.total_per_risk_level)
            del self.total_per_risk_level
            del self.sum_risk_level_changes
        except AttributeError:
            # property hasn't been set yet on the first round, ok to ignore
            pass
        super().step()

    @property
    def num_agents_risk_changed(self):
        return len([a for a in self.schedule.agents if a.risk_level_changed])

    @property
    def converged(self):
        # check if the simulation is stable and should stop running
        # based on the number of agents changing their risk level

        # checking whether agents risk level changed only works
        # when adjustment is enabled; if it is not, fallback
        # do base model logic, which is based on rolling avg % hawk
        if not self.risk_adjustment:
            return super().converged

        # this simulation typically takes around 1000 rounds to converge,
        # so don't even bother checking until at least 50 rounds
        return self.schedule.steps > max(self.adjust_round_n, 50) and (
            self.num_agents_risk_changed == 0
            # NOTE: could adjust the threshold here
            or self.sum_risk_level_changes <= len(self.schedule.agents) * 0.07
        )

    @cached_property
    def total_per_risk_level(self):
        # tally the number of agents for each risk level
        return Counter([a.risk_level for a in self.schedule.agents])

    @cached_property
    def sum_risk_level_changes(self):
        # calculate the total in absolute changes across all risk levels
        # since most recent adjustment round

        # requires at two sets of totals to compare
        if len(self.recent_total_per_risk_level) != 2:
            return

        a = self.recent_total_per_risk_level[0]
        b = self.recent_total_per_risk_level[1]
        changes = {}
        # for each risk level, calculate the absolute difference
        for rlevel, total in a.items():
            changes[rlevel] = abs(total - b[rlevel])

        return sum([val for val in changes.values()])

    def __getattr__(self, attr):
        # support dynamic properties for data collection on total by risk level
        if attr.startswith("total_r"):
            try:
                r = int(attr.replace("total_r", ""))
                # only handle risk levels that are in bounds
                if r > self.max_risk_level or r < self.min_risk_level:
                    raise AttributeError
                return self.total_per_risk_level[r]
            except ValueError:
                # ignore and throw attribute error
                pass

        raise AttributeError

    @property
    def population_risk_category(self):
        # calculate a category of risk distribution for the population
        # based on the proportion of agents in different risk categories
        # (categorization scheme defined by LB)

        # count the number of agents in three groups:
        risk_counts = self.total_per_risk_level
        # TODO: define these on the class for reuse in analysis?
        total = {
            "risk_inclined": risk_counts[0] + risk_counts[1] + risk_counts[2],
            "risk_moderate": risk_counts[3]
            + risk_counts[4]
            + risk_counts[5]
            + risk_counts[6],
            "risk_avoidant": risk_counts[7] + risk_counts[8] + risk_counts[9],
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
