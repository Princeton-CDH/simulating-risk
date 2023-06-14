from enum import Enum

import mesa

Bet = Enum("Bet", ["RISKY", "SAFE"])
bet_choices = [Bet.SAFE, Bet.RISKY]


class RiskyGambler(mesa.Agent):
    def __init__(self, unique_id, model, initial_wealth):
        super().__init__(unique_id, model)
        # starting wealth determined by the model
        self.wealth = initial_wealth
        # get a random risk tolerance; returns a value between 0.0 and 1.0
        self.risk_level = self.random.random()
        self.choice = None

    def step(self):
        # decide how to bet based on risk tolerance and likelihood
        # that the risky bet will pay off
        if self.risk_level > self.model.prob_risky_payoff:
            self.choice = Bet.RISKY
        else:
            self.choice = Bet.SAFE

        # determine the payoff for this choice
        self.calculate_payoff(self.choice)

    def calculate_payoff(self, choice):
        if choice == Bet.RISKY:
            # if the risky bet paid off, multiply current wealth by 1.5
            if self.model.risky_payoff:
                self.wealth = self.wealth * 1.5
                print(
                    "agent %s risky bet paid off, wealth is now %s"
                    % (self.unique_id, self.wealth)
                )

            # if it doesn't, multiply by 0.5
            else:
                self.wealth = self.wealth * 0.5
                print(
                    "agent %s risky bet did not paid off, wealth is now %s"
                    % (self.unique_id, self.wealth)
                )
        # safe choice = wealth stays the same
        print("agent %s no bet, wealth stays %s" % (self.unique_id, self.wealth))


class RiskyBetModel(mesa.Model):
    initial_wealth = 1000

    def __init__(self, grid_size):
        # assume a fully-populated square grid
        self.num_agents = grid_size * grid_size
        # initialize a single grid (each square inhabited by a single agent);
        # configure the grid to wrap around so everyone has neighbors
        self.grid = mesa.space.SingleGrid(grid_size, grid_size, True)
        self.schedule = mesa.time.SimultaneousActivation(self)

        # initialize agents and add to grid and scheduler
        for i in range(self.num_agents):
            a = RiskyGambler(i, self, self.initial_wealth)
            self.schedule.add(a)
            # place randomly in an empty spot
            self.grid.move_to_empty(a)

        self.datacollector = mesa.DataCollector(
            # TODO: figure out what data to collect
            model_reporters={
                # "prob_notcontaminated": "prob_notcontaminated",
                # "contaminated": "contaminated",
                # "average_risk_level": "avg_risk_level",
                # "min_risk_level": "min_risk_level",
                # "max_risk_level": "max_risk_level",
                # "num_agents": "total_agents",
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
        # TODO: add periodic agent risk adjustment (every ten rounds)
        self.datacollector.collect(self)

    def call_risky_bet(self):
        # flip a weighted coin to determine if the risky bet pays off,
        # weighted by current round payoff probability
        return self.random.choices(
            [True, False],
            weights=[self.prob_risky_payoff, 1 - self.prob_risky_payoff],
        )[0]
