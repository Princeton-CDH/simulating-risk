from enum import Enum
from functools import cached_property
import statistics

import mesa

from simulatingrisk.utils import coinflip


Bet = Enum("Bet", ["RISKY", "SAFE"])
bet_choices = [Bet.SAFE, Bet.RISKY]

# divergent color scheme, eleven colors
# from https://colorbrewer2.org/?type=diverging&scheme=RdYlGn&n=11
divergent_colors = [
    "#a50026",
    "#d73027",
    "#f46d43",
    "#fdae61",
    "#fee08b",
    "#ffffbf",
    "#d9ef8b",
    "#a6d96a",
    "#66bd63",
    "#1a9850",
    "#006837",
]
# low values = risk inclined (more likely to take a risky bet)
# higher value = risk averse (less likely to the bet)


class Gambler(mesa.Agent):
    def __init__(self, unique_id, model, initial_wealth):
        super().__init__(unique_id, model)
        # starting wealth determined by the model
        self.initial_wealth = initial_wealth  # store initial value
        self.wealth = initial_wealth
        # get a random risk tolerance; returns a value between 0.0 and 1.0
        self.risk_level = self.random.random()
        self.choice = None

    def __repr__(self):
        return (
            f"<Gambler id={self.unique_id} wealth={self.wealth} "
            + f"risk_level={self.risk_level}>"
        )

    def step(self):
        # decide how to bet based on risk tolerance and likelihood
        # that the risky bet will pay off
        if self.model.prob_risky_payoff > self.risk_level:
            self.choice = Bet.RISKY
        else:
            self.choice = Bet.SAFE

        # determine the payoff for this choice
        self.calculate_payoff(self.choice)

        # every ten rounds, agents adjust their risk level
        # make this a model method?
        if self.model.adjustment_round:
            self.adjust_risk()

    def calculate_payoff(self, choice):
        if choice == Bet.RISKY:
            # if the risky bet paid off, multiply current wealth by 1.5
            if self.model.risky_payoff:
                self.wealth = self.wealth * 1.5

            # if it doesn't, multiply by 0.5
            else:
                self.wealth = self.wealth * 0.5

        # otherwise, no change

    @cached_property
    def neighbors(self):
        """Get neighbors for the current agent; uses Von Neumann
        neighborhood (no diagonals), does not include self."""
        # because this simulation doesn't include any movement,
        # neighbors won't change over the run and we can cache
        return self.model.grid.get_neighbors(
            self.pos, moore=False, include_center=False
        )

    @property
    def wealthiest_neighbor(self):
        """identify and return the current wealthiest neighbor"""
        # sort neighbors by wealth, wealthiest neighbor first
        return sorted(self.neighbors, key=lambda x: x.wealth, reverse=True)[0]

    def adjust_risk(self):
        # look at neighbors (4)
        # if anyone has more money,
        # either adopt their risk attitude or average theirs with yours
        # then reset wealth back to initial value

        wealthiest = self.wealthiest_neighbor
        # if wealthiest neighbor is richer, adjust
        if wealthiest.wealth > self.wealth:
            # adjust risk based on model configuration
            if self.model.risk_adjustment == "adopt":
                # adopt wealthiest neighbor's risk level
                self.risk_level = wealthiest.risk_level
            elif self.model.risk_adjustment == "average":
                #  average theirs with mine
                self.risk_level = statistics.mean(
                    [self.risk_level, wealthiest.risk_level]
                )

        # reset wealth back to initial value
        self.wealth = self.initial_wealth


class RiskyBetModel(mesa.Model):
    """
    Model for simulating a risky bet game.

    :param grid_size: number for square grid size (creates n*n agents)
    :param risk_adjustment: strategy agents should use for adjusting risk;
        adopt (default), or average
    """

    initial_wealth = 1000
    running = True  # required for batch run

    def __init__(self, grid_size, risk_adjustment="adopt"):
        super().__init__()
        # assume a fully-populated square grid
        self.num_agents = grid_size * grid_size
        self.risk_adjustment = risk_adjustment
        # initialize a single grid (each square inhabited by a single agent);
        # configure the grid to wrap around so everyone has neighbors
        self.grid = mesa.space.SingleGrid(grid_size, grid_size, True)
        self.schedule = mesa.time.SimultaneousActivation(self)

        # initialize agents and add to grid and scheduler
        for i in range(self.num_agents):
            a = Gambler(i, self, self.initial_wealth)
            self.schedule.add(a)
            # place randomly in an empty spot
            self.grid.move_to_empty(a)

        self.datacollector = mesa.DataCollector(
            model_reporters={
                # state of the world
                "prob_risky_payoff": "prob_risky_payoff",
                "risky_bet": "risky_bet",
                # aggregate information about agents
                "risk_min": "risk_min",
                "risk_q1": "risk_q1",
                "risk_mean": "risk_mean",
                "risk_q3": "risk_q3",
                "risk_max": "risk_max",
            },
            agent_reporters={"risk_level": "risk_level", "choice": "choice"},
        )

    def step(self):
        # run a single round of the game

        # determine the probability of the risky bet paying off this round
        self.prob_risky_payoff = self.random.random()
        # determine whether it actually pays off
        self.risky_payoff = self.call_risky_bet()

        self.schedule.step()
        self.datacollector.collect(self)
        # every ten rounds, agents adjust their risk level

        # delete cached property before the next round
        try:
            del self.agent_risk_levels
        except AttributeError:
            pass

    def call_risky_bet(self):
        # flip a weighted coin to determine if the risky bet pays off,
        # weighted by current round payoff probability
        self.risky_bet = coinflip([True, False], weight=self.prob_risky_payoff)
        return self.risky_bet

    @property
    def adjustment_round(self) -> bool:
        """is the current round an adjustment round?"""
        # agents should adjust their wealth every 10 rounds;
        # check if the current step is an adjustment round
        return self.schedule.steps > 0 and self.schedule.steps % 10 == 0

    @cached_property
    def agent_risk_levels(self) -> [float]:
        # list of all risk levels for all current agents;
        # property is cached but should be cleared in each new round

        # NOTE: occasionally median method is complaining that this is empty
        return [a.risk_level for a in self.schedule.agents]

    @property
    def max_agent_wealth(self):
        # what is the current largest wealth of any agent?
        return max([a.wealth for a in self.schedule.agents])

    @property
    def risk_median(self):
        # calculate median of current agent risk levels
        if self.agent_risk_levels:
            # occasionally this complains about an empty list
            # hopefully only possible in unit tests...
            return statistics.median(self.agent_risk_levels)

    @property
    def risk_mean(self):
        return statistics.mean(self.agent_risk_levels)

    @property
    def risk_min(self):
        return min(self.agent_risk_levels)

    @property
    def risk_max(self):
        return max(self.agent_risk_levels)

    @property
    def risk_q1(self):
        risk_median = self.risk_median
        # first quartile is the median of values less than the median
        submedian_values = [r for r in self.agent_risk_levels if r < risk_median]
        if submedian_values:
            return statistics.median(submedian_values)

    @property
    def risk_q3(self):
        risk_median = self.risk_median
        # third quartile is the median of values greater than the median
        supermedian_values = [r for r in self.agent_risk_levels if r > risk_median]
        if supermedian_values:
            return statistics.median(supermedian_values)
