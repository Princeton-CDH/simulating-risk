from enum import Enum
import math

import mesa

from simulatingrisk.utils import coinflip

Play = Enum("Play", ["HAWK", "DOVE"])
play_choices = [Play.HAWK, Play.DOVE]


# divergent color scheme, nine colors
# from https://colorbrewer2.org/?type=diverging&scheme=RdYlGn&n=9
divergent_colors_9 = [
    "#d73027",
    "#f46d43",
    "#fdae61",
    "#fee08b",
    "#ffffbf",
    "#d9ef8b",
    "#a6d96a",
    "#66bd63",
    "#1a9850",
]

# divergent color scheme, ficolors
# from https://colorbrewer2.org/?type=diverging&scheme=RdYlGn&n=5
divergent_colors_5 = ["#d7191c", "#fdae61", "#ffffbf", "#a6d96a", "#1a9641"]


class HawkDoveAgent(mesa.Agent):
    """
    An agent with a risk attitude playing Hawk or Dove
    """

    def __init__(self, unique_id, model, risk_level=None, hawk_odds=None):
        super().__init__(unique_id, model)

        self.points = 0
        self.choice = self.initial_choice(hawk_odds)
        self.last_choice = None

        # risk level
        # - based partially on neighborhood size,
        #  which is configurable at the model level
        num_neighbors = 8 if self.model.include_diagonals else 4
        self.risk_level = risk_level or self.random.randint(0, num_neighbors)

    def initial_choice(self, hawk_odds=None):
        # first round : choose what to play randomly or based on initial hawk odds
        opts = {}
        if hawk_odds:
            opts["weight"] = hawk_odds
        return coinflip(play_choices, **opts)

    @property
    def choice_label(self):
        return "hawk" if self.choice == Play.HAWK else "dove"

    @property
    def neighbors(self):
        # use configured neighborhood (with or without diagonals) on the model;
        # don't include the current agent
        return self.model.grid.get_neighbors(
            self.pos, moore=self.model.include_diagonals, include_center=False
        )

    @property
    def num_dove_neighbors(self):
        """count how many neighbors played DOVE on the last round"""
        return len([n for n in self.neighbors if n.last_choice == Play.DOVE])

    def choose(self):
        "decide what to play this round"
        # after the first round, choose based on what neighbors did last time
        if self.model.schedule.steps > 0:
            # store previous choice
            self.last_choice = self.choice

            # choose based on the number of neighbors who played
            # dove last round and agent risk level

            # agent with r = 0 should always take the risky choice
            #   (any risk is acceptable).
            # agent with r = max should always take the safe option
            #   (no risk is acceptable)
            if self.num_dove_neighbors > self.risk_level:
                self.choice = Play.HAWK
            else:
                self.choice = Play.DOVE

    def play(self):
        # play against each neighbor and calculate cumulative payoff
        payoff = 0
        for n in self.neighbors:
            payoff += self.payoff(n)
        # update total points based on payoff this round
        self.points += payoff

    def payoff(self, other):
        """
        If I play HAWK and neighbor plays DOVE: 3
        If I play DOVE and neighbor plays DOVE: 2.1
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
                return 2.1
            if other.choice == Play.HAWK:
                return 1

    @property
    def points_rank(self):
        if self.points:
            return math.floor(self.points / self.model.max_agent_points * 10)
        return 0


class HawkDoveModel(mesa.Model):
    """ """

    running = True  # required for batch run

    def __init__(
        self,
        grid_size,
        include_diagonals=True,
        risk_attitudes="variable",
        agent_risk_level=None,
        hawk_odds=0.5,
    ):
        super().__init__()
        # assume a fully-populated square grid
        self.num_agents = grid_size * grid_size
        # mesa get_neighbors supports moore neighborhood (include diagonals)
        # and von neumann (exclude diagonals)
        self.include_diagonals = include_diagonals
        self.risk_attitudes = risk_attitudes
        # distribution of first choice (50/50 by default)
        self.hawk_odds = hawk_odds

        # initialize a single grid (each square inhabited by a single agent);
        # configure the grid to wrap around so everyone has neighbors
        self.grid = mesa.space.SingleGrid(grid_size, grid_size, True)
        self.schedule = mesa.time.StagedActivation(self, ["choose", "play"])

        agent_opts = {}
        # when started in single risk attitude mode, initialize all agents
        # with the specified risk level
        if risk_attitudes == "single" and agent_risk_level:
            agent_opts["risk_level"] = agent_risk_level

        for i in range(self.num_agents):
            agent = HawkDoveAgent(i, self, hawk_odds=self.hawk_odds, **agent_opts)
            self.schedule.add(agent)
            # place randomly in an empty spot
            self.grid.move_to_empty(agent)

        self.datacollector = mesa.DataCollector(
            model_reporters={"max_agent_points": "max_agent_points"},
            agent_reporters={"risk_level": "risk_level", "choice": "choice_label"},
        )

    def step(self):
        """
        A model step. Used for collecting data and advancing the schedule
        """
        self.schedule.step()
        self.datacollector.collect(self)

    @property
    def max_agent_points(self):
        # what is the current largest point total of any agent?
        return max([a.points for a in self.schedule.agents])
