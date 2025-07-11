from collections import defaultdict
from enum import Enum
from functools import cached_property
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
        if risk_level is None:  # only set randomly if None; allow zero risk
            risk_level = self.random.random()
        self.risk_level = risk_level
        self.choice = None

    def __repr__(self):
        return f"<RiskyFoodAgent id={self.unique_id} risk_level={self.risk_level}>"

    def step(self):
        # choose food based on the probability not contaminated and risk tolerance
        # lower risk level = risk seeking
        # higher = risk averse
        #   risk level 1.0 should always choose safe (not strictly greater)
        if self.model.prob_notcontaminated > self.risk_level:
            self.choice = FoodChoice.RISKY
        else:
            self.choice = FoodChoice.SAFE
        self.payoff = self.model.payoff(self.choice)


class RiskyFoodModel(mesa.Model):
    prob_notcontaminated = None
    running = True  # required for batch running

    def __init__(self, n=110, mode="types"):
        super().__init__()
        self.num_agents = n
        self.mode = mode
        self.schedule = mesa.time.SimultaneousActivation(self)
        # initialize agents for the first round

        # when mode is types, initialize 10 agents each of 11 risk types
        if mode == "types":
            # currently ignores n...
            # maybe n could be n per type when mode is types
            for i in range(11):
                risk_level = i / 10  # 0, 0.1, 0.2, 0.3, ... 1.0
                for j in range(10):
                    # agents need unique ids;
                    # create them from type & index
                    agent_id = f"{i}-{j}"
                    a = Agent(agent_id, self, risk_level=risk_level)
                    self.schedule.add(a)

        else:
            # when mode is not types, initialize risk level randomly
            for i in range(self.num_agents):
                a = Agent(i, self)
                self.schedule.add(a)

        self.nextid = self.num_agents + 1

        model_data = {
            "prob_notcontaminated": "prob_notcontaminated",
            "contaminated": "contaminated",
            "average_risk_level": "avg_risk_level",
            "min_risk_level": "min_risk_level",
            "max_risk_level": "max_risk_level",
            "num_agents": "total_agents",
        }
        # # report percent agents by risk level
        # for i in range(11):
        #     risk_level = i / 10
        #     model_data["pct_r%.1f" % risk_level] = lambda m: m.percent_agents_risk(
        #         risk_level
        #     )

        self.datacollector = mesa.DataCollector(
            model_reporters=model_data,
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

        # delete cached property before the next round
        del self.agent_risk_levels

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

        # when mode is types, payoff is based on number of each type of agent
        if self.mode == "types":
            self.propagate_types()
            return

        # otherwise, use previous logic

        # get a generator of agents from the scheduler that
        # will allow us to add and remove
        for agent in self.schedule.agents:
            # add offspring based on payoff; keep risk level
            # logic is offspring = to payoff, original dies off,
            # but for efficiency just add payoff - 1 and keep the  original
            for i in range(agent.payoff - 1):
                a = Agent(i + self.nextid, self, risk_level=agent.risk_level)
                self.schedule.add(a)

            self.nextid = self.total_agents + 1

    def propagate_types(self):
        for risk_level, agents in self.agents_by_risktype.items():
            # adjust population based on payoff and number of agents
            total = len(agents)
            # calculate number of agents of this type for next round
            # - convert to int so we can use for array slicing
            new_total = int((total * agents[0].payoff) / 2)

            # if new total is less, remove agents over the expected total
            for agent in agents[new_total:]:
                self.schedule.remove(agent)
            # if new total is more, add new agents with same risk level
            if new_total > total:
                for i in range(new_total - total):
                    a = Agent(self.nextid, self, risk_level)
                    self.schedule.add(a)
                    self.nextid += 1

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
        return self.schedule.agents

    @property
    def total_agents(self):
        return self.schedule.get_agent_count()

    def total_agents_risk(self, risk_level):
        # total number of agents with a particular risk level
        return len(self.agents_by_risktype[risk_level])
        # return len([a for a in self.agents if a.risk_level == risk_level])

    def percent_agents_risk(self, risk_level):
        # # percent of agents with a particular risk level
        risk_total = self.total_agents_risk(risk_level)
        # print(
        #     "risk %s total %s total agents %d percent %s"
        #     % (
        #         risk_level,
        #         risk_total,
        #         self.total_agents,
        #         (risk_level / self.total_agents) * 100,
        #     )
        # )
        return (risk_total / self.total_agents) * 100

    @property
    def agents_by_risktype(self):
        # group agents by risk level for propagation
        agents = defaultdict(list)
        for a in self.agents:
            agents[a.risk_level].append(a)
        return agents

    @cached_property
    def agent_risk_levels(self) -> [float]:
        # list of all risk levels for all current agents;
        # property is cached but should be cleared in each new round

        # NOTE: occasionally median method is complaining that this is empty
        return [a.risk_level for a in self.agents]

    @property
    def avg_risk_level(self):
        return mean(self.agent_risk_levels)

    @property
    def min_risk_level(self):
        return min(self.agent_risk_levels)

    @property
    def max_risk_level(self):
        return max(self.agent_risk_levels)

    payoffs = {
        "range": {"safe": 2, "not_contaminated": 3, "contaminated": 1},
        "types": {"safe": 2, "not_contaminated": 4, "contaminated": 1},
    }

    def payoff(self, choice):
        "Calculate the payoff for a given choice, based on current food status"

        # safe food choice always has a payoff of 2
        if choice == FoodChoice.SAFE:
            # return 2
            return self.payoffs[self.mode]["safe"]
        # payoff for risky food choice depends on contamination
        # - if not contaminated, payoff of 3
        if self.risky_food_status == FoodStatus.NOTCONTAMINATED:
            # return 3
            return self.payoffs[self.mode]["not_contaminated"]

        # otherwise only payoff of 1
        return self.payoffs[self.mode]["contaminated"]
        # return 1
