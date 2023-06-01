from enum import Enum
from functools import partial

import mesa


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
        print(f"agent {unique_id} risk level {self.risk_level}")

    def step(self):
        # choose food based on the probability not contaminated and risk tolerance
        if self.risk_level > self.model.prob_notcontaminated:
            choice = FoodChoice.RISKY
        else:
            choice = FoodChoice.SAFE
        self.payoff = self.model.payoff(choice)
        print(
            f"agent {self.unique_id} r {self.risk_level:.4f} p {self.model.prob_notcontaminated:.4f} choice: {choice} payoff {self.payoff}"
        )


def food_status(model):
    if model.risky_food_status == FoodStatus.CONTAMINATED:
        print("food status 1")
        return 1
    print("food status 0")
    return 0


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
            }
            # TODO: add data collection for agents to track risk level
        )

    def step(self):
        """Advance the model by one step."""
        # pick a probability for risky food being not contaminated this round
        self.prob_notcontaminated = self.random.random()
        # determine actual food status, weighted by probability of non-contamination
        print([self.prob_notcontaminated, 1 - self.prob_notcontaminated])
        # randomly choose based on probabality not contaminated; return the first choice
        self.risky_food_status = self.random.choices(
            [FoodStatus.NOTCONTAMINATED, FoodStatus.CONTAMINATED],
            weights=[self.prob_notcontaminated, 1 - self.prob_notcontaminated],
        )[0]
        print(
            f"p not contaminated: {self.prob_notcontaminated:.4f} actual status: {self.risky_food_status}"
        )
        self.schedule.step()
        self.datacollector.collect(self)

        # setup agents for the next round
        self.propagate()

    def propagate(self):
        # update agents based on payoff from the completed round

        # get a generator of agents from the scheduler that
        # will allow us to add and remove
        for agent in self.schedule.agent_buffer():
            # add offspring based on payoff; keep risk level
            for i in range(agent.payoff):
                a = Agent(i + self.nextid, self, agent.risk_level)
                self.schedule.add(a)
            # remove agent from previous round
            self.schedule.remove(agent)

            self.nextid += agent.payoff

        print(f"finished propagation, {self.schedule.get_agent_count()} total agents")

    @property
    def contaminated(self):
        # return a value for food status this round, for data collection
        if self.risky_food_status == FoodStatus.CONTAMINATED:
            return 1
        return 0

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
