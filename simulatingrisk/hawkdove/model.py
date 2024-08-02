from enum import Enum
from collections import deque
import math
import statistics

import mesa

from simulatingrisk.utils import coinflip

Play = Enum("Play", ["HAWK", "DOVE"])
play_choices = [Play.HAWK, Play.DOVE]


# divergent color scheme, ten colors
# from https://colorbrewer2.org/?type=diverging&scheme=RdYlGn&n=10
divergent_colors_10 = [
    "#a50026",
    "#d73027",
    "#f46d43",
    "#fdae61",
    "#fee08b",
    "#d9ef8b",
    "#a6d96a",
    "#66bd63",
    "#1a9850",
    "#006837",
]

# divergent color scheme, five colors
# from https://colorbrewer2.org/?type=diverging&scheme=RdYlGn&n=5
divergent_colors_5 = ["#d7191c", "#fdae61", "#ffffbf", "#a6d96a", "#1a9641"]


class HawkDoveAgent(mesa.Agent):
    """
    An agent with a risk attitude playing Hawk or Dove
    """

    def __init__(self, unique_id, model, hawk_odds=None):
        super().__init__(unique_id, model)

        self.points = 0
        self.choice = self.initial_choice(hawk_odds)
        self.last_choice = None

        # risk level must be set by base class, since initial
        # conditions are specific to single / variable risk games
        self.set_risk_level()

    def set_risk_level(self):
        raise NotImplementedError

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} id={self.unique_id} "
            + f"r={self.risk_level} points={self.points}>"
        )

    def initial_choice(self, hawk_odds=None):
        # first round : choose what to play randomly or based on initial hawk odds
        opts = {}
        if hawk_odds is not None:
            opts["weight"] = hawk_odds
        return coinflip(play_choices, **opts)

    @property
    def choice_label(self):
        return "hawk" if self.choice == Play.HAWK else "dove"

    def get_neighbors(self, size):
        """get all neighbors for a supported neighborhood size"""
        check_neighborhood_size(size)
        # 4 and 8 neighborhood use default radius 1
        # 8 and 24 both use moore neighborhood (includes diagonals)
        opts = {"moore": True}
        if size == 4:
            # use von neumann neighborhood instead of moore (no diagonal)
            opts["moore"] = False

        # for 24 size neighborhood, use radius 2
        if size == 24:
            opts["radius"] = 2

        return self.model.grid.get_neighbors(self.pos, include_center=False, **opts)

    @property
    def play_neighbors(self):
        """neighbors to play against, based on model play neighborhood size"""
        return self.get_neighbors(self.model.play_neighborhood)

    @property
    def observed_neighbors(self):
        """neighbors to look at when deciding what to play;
        based on model observed neighborhood size"""
        return self.get_neighbors(self.model.observed_neighborhood)

    @property
    def num_dove_neighbors(self):
        """count how many neighbors played DOVE on the last round
        (uses `observed_neighborhood` size from model)"""
        return len([n for n in self.observed_neighbors if n.last_choice == Play.DOVE])

    @property
    def proportional_num_dove_neighbors(self):
        """adjust the number of dove neighbors to scale observations
        to a standard range of risk levels."""
        # for convenience and simplicity, we scale the neighborhood so
        # that agent risk levels can always be defined as 0-9 no matter
        # the neighborhood size. (Can also be thought of as always
        # scaling to a neighborhood size of 8.).
        # Agent risk levels are 0-9 but scaling is 1-8, since 0 and 9
        # always play hawk and dove respectively.
        ratio = 8 / self.model.observed_neighborhood
        # always round to an integer
        return round(ratio * self.num_dove_neighbors)

    def choose(self):
        "decide what to play this round"
        # first choice is random since we don't have any information
        # about neighbors' choices
        if self.model.schedule.steps == 0:
            return

        # after the first round, choose based on what neighbors did last time

        # choose based on the number of neighbors who played
        # dove last round and agent risk level

        # agent with r = 0 should always take the risky choice
        #   (any risk is acceptable).
        # agent with r = max should always take the safe option
        #   (no risk is acceptable)
        if self.proportional_num_dove_neighbors >= self.risk_level:
            choice = Play.HAWK
        else:
            choice = Play.DOVE

        # based on model configuration, should agent play randomly instead?
        if self.model.random_play_odds and coinflip(
            [True, False], weight=self.model.random_play_odds
        ):
            # if a random play is selected, flip a coin between hawk and dove
            choice = coinflip([Play.HAWK, Play.DOVE])

        self.choice = choice

    def play(self):
        # play against each neighbor and calculate cumulative payoff
        payoff = 0
        for n in self.play_neighbors:
            payoff += self.payoff(n)
        # update total points based on payoff this round
        self.points += payoff

        # store this round's choice as previous choice
        self.last_choice = self.choice

    def payoff(self, other):
        """
        If I play HAWK and neighbor plays DOVE: 3
        If I play DOVE and neighbor plays DOVE: 2
        If I play DOVE and neighbor plays HAWK: 1
        If I play HAWK and neighbor plays HAWK: 0
        """
        if self.choice == Play.HAWK:
            if other.choice == Play.DOVE:
                return 3
            if other.choice == Play.HAWK:
                return 0
        elif self.choice == Play.DOVE:
            if other.choice == Play.DOVE:
                return 2
            if other.choice == Play.HAWK:
                return 1

    @property
    def points_rank(self):
        if self.points:
            return math.floor(self.points / self.model.max_agent_points * 10)
        return 0


class HawkDoveModel(mesa.Model):
    """
    Model for hawk/dove game with risk attitudes.

    :param grid_size: number for square grid size (creates n*n agents)
    :param play_neighborhood: size of neighborhood each agent plays
        against; 4, 8, or 24 (default: 8)
    :param observed_neighborhood: size of neighborhood each agent looks
        at when choosing what to play; 4, 8, or 24 (default: 8)
    :param hawk_odds: odds for playing hawk on the first round (default: 0.5)
    """

    #: whether the simulation is running
    running = True  # required for batch run
    #: readable status (running/converged)
    status = "running"

    #: size of deque/fifo for recent values
    rolling_window = 30
    #: minimum size before calculating rolling average
    min_window = 15
    #: class to use when initializing agents
    agent_class = HawkDoveAgent
    #: supported neighborhood sizes
    neighborhood_sizes = {4, 8, 24}
    #: minimum risk level
    min_risk_level = 0
    #: maximum risk level allowed
    max_risk_level = 9

    def __init__(
        self,
        grid_size,
        play_neighborhood=8,
        observed_neighborhood=8,
        hawk_odds=0.5,
        random_play_odds=0.00,
    ):
        super().__init__()
        # check parameters for combinations that aren't allowed together
        if grid_size < 5:
            if play_neighborhood > 8:
                raise ValueError(
                    "Play neighborhood %d is too large for grid size %d",
                    play_neighborhood,
                    grid_size,
                )
            if observed_neighborhood > 8:
                raise ValueError(
                    "Observed neighborhood %d is too large for grid size %d",
                    observed_neighborhood,
                    grid_size,
                )

        # assume a fully-populated square grid
        self.num_agents = grid_size * grid_size
        for nsize in [play_neighborhood, observed_neighborhood]:
            check_neighborhood_size(nsize)

        self.play_neighborhood = play_neighborhood
        self.observed_neighborhood = observed_neighborhood

        # distribution of first choice (50/50 by default)
        self.hawk_odds = hawk_odds
        # how often should agents make a random play
        self.random_play_odds = random_play_odds

        # create fifos to track recent behavior to detect convergence
        self.recent_percent_hawk = deque([], maxlen=self.rolling_window)
        self.recent_rolling_percent_hawk = deque([], maxlen=self.rolling_window)

        # initialize a single grid (each square inhabited by a single agent);
        # configure the grid to wrap around so everyone has neighbors
        self.grid = mesa.space.SingleGrid(grid_size, grid_size, True)
        self.schedule = mesa.time.StagedActivation(self, ["choose", "play"])

        # initialize all agents
        agent_opts = self.new_agent_options()
        for i in range(self.num_agents):
            # add to scheduler and place randomly in an empty spot
            agent = self.agent_class(i, self, **agent_opts)
            self.schedule.add(agent)
            self.grid.move_to_empty(agent)

        self.datacollector = mesa.DataCollector(**self.get_data_collector_options())

    def get_data_collector_options(self):
        # method to return options for data collection,
        # so subclasses can modify
        return {
            "model_reporters": {
                "max_agent_points": "max_agent_points",
                "percent_hawk": "percent_hawk",
                "rolling_percent_hawk": "rolling_percent_hawk",
                "status": "status",
                # explicitly track total agents, instead of inferring from grid size
                "total_agents": "num_agents",
            },
            "agent_reporters": {
                "risk_level": "risk_level",
                "choice": "choice_label",
                "points": "points",
            },
        }

    def new_agent_options(self):
        # generate and return a dictionary with common options
        # for initializing all agents
        return {"hawk_odds": self.hawk_odds}

    def step(self):
        """
        A model step. Used for collecting data and advancing the schedule
        """
        self.schedule.step()
        # check if simulation has converged and should stop running
        if self.converged:
            self.status = "converged"
            self.running = False

        # collect data after status is updated, so data collected
        # for last round will reflect converged status
        self.datacollector.collect(self)

    @property
    def max_agent_points(self):
        # what is the current largest point total of any agent?
        return max([a.points for a in self.schedule.agents])

    @property
    def percent_hawk(self):
        # what percent of agents chose hawk?
        hawks = [a for a in self.schedule.agents if a.choice == Play.HAWK]
        phawk = len(hawks) / self.num_agents
        # add to recent values
        self.recent_percent_hawk.append(phawk)
        return phawk

    @property
    def rolling_percent_hawk(self):
        # make sure we have enough values to check
        if len(self.recent_percent_hawk) > self.min_window:
            rolling_phawk = statistics.mean(self.recent_percent_hawk)
            # add to recent values
            self.recent_rolling_percent_hawk.append(rolling_phawk)
            return rolling_phawk

    @property
    def converged(self):
        # check if the simulation is stable and should stop running
        # calculating based on rolling percent hawk; when this is stable
        # within our rolling window, return true
        # - currently checking for single value;
        #  could allow for a small amount variation if necessary

        # in variable risk with risk adjustment, numbers are not strictly equal
        # but do get close and fairly stable; round to two digits before comparing
        rounded_set = set([round(x, 2) for x in self.recent_rolling_percent_hawk])
        return (
            len(self.recent_rolling_percent_hawk) > self.min_window
            and len(rounded_set) == 1
        )


def check_neighborhood_size(size):
    # neighborhood size check, shared by model and agent
    if size not in HawkDoveModel.neighborhood_sizes:
        raise ValueError(
            f"{size} is not a supported neighborhood size; "
            + f"must be one of {HawkDoveModel.neighborhood_sizes}"
        )


class HawkDoveSingleRiskAgent(HawkDoveAgent):
    """
    An agent with a risk attitude playing Hawk or Dove; must be initialized
    with a risk level
    """

    def set_risk_level(self):
        self.risk_level = self.model.agent_risk_level


class HawkDoveSingleRiskModel(HawkDoveModel):
    """hawk/dove simulation where all agents have the same risk atttitude.
    Adds a required `agent_risk_level` parameter; supports all
    parameters in :class:`HawkDoveModel`.
    """

    #: class to use when initializing agents
    agent_class = HawkDoveSingleRiskAgent

    risk_attitudes = "single"

    def __init__(self, grid_size, agent_risk_level, *args, **kwargs):
        if (
            agent_risk_level > self.max_risk_level
            or agent_risk_level < self.min_risk_level
        ):
            raise ValueError(
                f"Agent risk level {agent_risk_level} is out of range; must be between "
                + f"{self.min_risk_level} - {self.max_risk_level}"
            )

        # store agent risk level
        self.agent_risk_level = agent_risk_level

        # pass through options and initialize base class
        super().__init__(grid_size, *args, **kwargs)
