from enum import Enum
from statistics import mean

import mesa

from simulatingrisk.utils import coinflip


class FoodChoice(Enum):
    RISKY = "R"
    SAFE = "S"


class FoodStatus(Enum):
    CONTAMINATED = "C"
    NOTCONTAMINATED = "N"


class Agent(mesa.Agent):
    def __init__(self, unique_id, model, risk_level=None):
        super().__init__(unique_id, model)
        # get a random risk tolerance; returns a value between 0.0 and 1.0
        self.risk_level = risk_level or self.random.random()

    def step(self):
        # choose food based on the probability not contaminated and risk tolerance
        if self.risk_level > self.model.prob_notcontaminated:
            choice = FoodChoice.RISKY
        else:
            choice = FoodChoice.SAFE
        self.payoff = self.model.payoff(choice)


class RiskyFoodModel(mesa.Model):
    prob_notcontaminated = None

    def __init__(self, n):
        self.num_agents = n
        self.schedule = mesa.time.SimultaneousActivation(self)
        # initialize agents for the first round
        for i in range(self.num_agents):
            a = Agent(i, self)
            self.schedule.add(a)

        self.nextid = i + 1

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "prob_notcontaminated": "prob_notcontaminated",
                "contaminated": "contaminated",
                "average_risk_level": "avg_risk_level",
                "min_risk_level": "min_risk_level",
                "max_risk_level": "max_risk_level",
                "num_agents": "total_agents",
            },
            agent_reporters={"risk_level": "risk_level", "payoff": "payoff"},
        )

    def step(self):
        """Advance the model by one step."""
        # pick a probability for risky food being not contaminated this round
        self.prob_notcontaminated = self.random.random()

        self.risky_food_status = self.get_risky_food_status()

        self.schedule.step()
        self.datacollector.collect(self)

        # setup agents for the next round
        self.propagate()

    def get_risky_food_status(self):
        # determine actual food status for this round,
        # weighted by probability of non-contamination

        # randomly choose status, with first choice weighted by
        # current probability not contaminated
        return coinflip(
            choices=[FoodStatus.NOTCONTAMINATED, FoodStatus.CONTAMINATED],
            weight=self.prob_notcontaminated,
        )

    def propagate(self):
        # update agents based on payoff from the completed round

        # get a generator of agents from the scheduler that
        # will allow us to add and remove
        for agent in self.schedule.agent_buffer():
            # add offspring based on payoff; keep risk level
            # logic is offspring = to payoff, original dies off,
            # but for efficiency just add payoff - 1 and keep the  original
            for i in range(agent.payoff - 1):
                a = Agent(i + self.nextid, self, agent.risk_level)
                self.schedule.add(a)

            self.nextid += agent.payoff

    @property
    def contaminated(self):
        # return a value for food status this round, for data collection
        if self.risky_food_status == FoodStatus.CONTAMINATED:
            return 1
        return 0

    @property
    def agents(self):
        # custom property to make it easy to access all current agents

        # uses a generator of agents from the scheduler that
        # will allow adding and removing agents from the scheduler
        return self.schedule.agent_buffer()

    @property
    def total_agents(self):
        return self.schedule.get_agent_count()

    @property
    def avg_risk_level(self):
        return mean([agent.risk_level for agent in self.agents])

    @property
    def min_risk_level(self):
        return min([agent.risk_level for agent in self.agents])

    @property
    def max_risk_level(self):
        return max([agent.risk_level for agent in self.agents])

    def payoff(self, choice):
        "Calculate the payoff for a given choice, based on current food status"

        # safe food choice always has a payoff of 2
        if choice == FoodChoice.SAFE:
            return 2
        # payoff for risky food choice depends on contamination
        # - if not contaminated, payoff of 3
        if self.risky_food_status == FoodStatus.NOTCONTAMINATED:
            return 3

        # otherwise only payoff of 1
        return 1
