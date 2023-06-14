from enum import Enum
from functools import partial

import mesa

HuntChoice = Enum("Hunt", ["STAG", "HARE"])
choices = [HuntChoice.STAG, HuntChoice.HARE]


class StagHuntAgent(mesa.Agent):
    """An hunter agent who hunts stag or hare."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        # self.wealth = 1
        # initialize hunt choice randomly for now
        self.hunting = self.random.choices(list(HuntChoice), weights=[15, 85])[0]
        # print("%s hunting %s" % (unique_id, self.hunting))
        # self.hunting = self.random.choice(choices)
        self.last_payoff = None

    def payoff(self, other_agent):
        # hunting hare has a payoff of 3 no matter what the other agent does
        if self.hunting == HuntChoice.HARE:
            return 3

        # if both hunt stag, payoff is 4
        if other_agent.hunting == HuntChoice.STAG:
            return 4

        # hunting stag alone payoff is zero
        return 0

    def get_neighbors(self):
        # use moore neighborhood (include diagonals), don't include self
        return self.model.grid.get_neighbors(self.pos, True, False)

    def choose(self):
        # decide on hunting strategy
        # for first hunt, use initial strategy

        # if this is not the first time hunting,
        # compare our payoff to neighbors
        if self.last_payoff is not None:
            neighbors = self.get_neighbors()
            # update strategy for next time based on neighbors
            # sort neighbors by their last payoff
            neighbor_success = sorted(
                neighbors, key=lambda n: n.last_payoff, reverse=True
            )
            most_successful = neighbor_success[0]
            if most_successful.last_payoff > self.last_payoff:
                print(
                    "most successful neighbor: %s payoff=%s hunting=%s"
                    % (
                        most_successful.unique_id,
                        most_successful.last_payoff,
                        most_successful.hunting,
                    )
                )
                self.hunting = most_successful.hunting

    def hunt(self):
        # how to pair up agents? for now use random?

        neighbors = self.get_neighbors()
        # choose hunting partner from neighbors randomly
        other_agent = self.random.choice(neighbors)

        # other_agent = self.random.choice(self.model.schedule.agents)
        self.last_payoff = self.payoff(other_agent)
        # print("%s payoff %s" % (self.unique_id, self.last_payoff))


def count_stag_hunters(model):
    return len(
        [agent for agent in model.schedule.agents if agent.hunting == HuntChoice.STAG]
    )


def num_hunting_choice(model, hunting):
    return len(
        [hunter for hunter in model.schedule.agents if hunter.hunting == hunting]
    )


class StagHuntModel(mesa.Model):
    """A model with some number of stag-hunt agents."""

    # def __init__(self, N):
    # self.num_agents = N
    def __init__(self, width, height):
        self.num_agents = width * height
        self.grid = mesa.space.SingleGrid(width, height, True)
        self.schedule = mesa.time.StagedActivation(self, ["choose", "hunt"])
        # Create agents
        for i in range(self.num_agents):
            a = StagHuntAgent(i, self)
            self.schedule.add(a)
            # place randomly in an empty spot
            self.grid.move_to_empty(a)

        # self.datacollector = mesa.DataCollector(
        #     model_reporters={"stag hunters": count_stag_hunters},
        #     agent_reporters={"Hunting": "hunting", "Payoff": "last_payoff"},
        # )

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "stag_hunters": partial(
                    num_hunting_choice, self, hunting=HuntChoice.STAG
                ),
                "hare_hunters": partial(
                    num_hunting_choice, self, hunting=HuntChoice.HARE
                ),
            }
        )
        self.datacollector.collect(self)

    def step(self):
        """Advance the model by one step."""
        self.datacollector.collect(self)
        self.schedule.step()
