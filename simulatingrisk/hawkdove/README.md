# Hawk-Dove with risk attitudes

Hawk/Dove game with variable risk attitudes

## Game description

This is a variant of the Hawk/Dove Game: https://en.wikipedia.org/wiki/Chicken_(game)

| | H | D|
|-|-|-|
| H | 0, 0 | 3, 1|
| D |1, 3| 2.1, 2.1|

BACKGROUND: An unpublished paper by Simon Blessenohl shows that the equilibrium in this game is different for EU maximizers than for REU maximizers (all with the same risk-attitude), and that REU maximizers do better as a population (basically, play DOVE more often)

We want to know: what happens when different people have _different_ risk-attitudes.

GAME: Hawk-Dove with risk-attitudes

Players arranged on a lattice [try both 4 neighbors (AYBD) and 8 neighbors (XYZABCDE)]

| | | |
|-|-|-|
| X | Y |Z |
|A | **I** |  B |
| C | D | E |

 
Each player on a lattice (grid in Mesa):
- Has parameter `r` [from 0 to 8, or 0 to 4 for four neighbors]
- Let `d` be the number of neighbors who played DOVE during the previous round. If `d > r`, then play HAWK. Otherwise play DOVE. (Agents who are risk-avoidant only play HAWK if there are a lot of doves around them. More risk-avoidance requires a higher number of doves to get an agent to play HAWK.)
- The proportion of neighbors who play DOVE corresponds to your probability of encountering a DOVE when playing a randomly-selected neighbor. The intended interpretation is that you maximize REU for this probability of your opponent playing DOVE. Thus, r corresponds to the probability above which playing HAWK maximizes REU.
- An REU maximizer will play HAWK when r(p) > [(D,H)-(H,H)]/[(H,D)-(D,D)] ; in other words, when r(p) > 0.52. An EU maximizer, with r(p) = p, will play HAWK when p > 0.52, e.g., when more than 4 out of 8 neighbors play DOVE. Thus, r = 4 corresponds to risk-neutrality (EU maximization), r < 4 corresponds to risk-inclination, and r > 4 corresponds to risk-avoidance.
- Payoffs were chosen to avoid the case in which two choices had equal expected utility for some number of neighbors. For example, if the payoff of (D,D) was (2,2), then at p = 0.5 (4 of 8 neighbors), then EU maximizers would be indifferent between HAWK and DOVE; in this case, no r-value would correspond to EU maximization, since r = 4 strictly prefers DOVE and r = 3 strictly prefers HAWK.
  
  - Choice for the first round could be randomly determined, or add parameters to see how initial conditions matter?
  - [OR VARY FIRST ROUND: what proportion starts as HAWK
    - [Who is a HAWK and who is a DOVE is randomly determined; proportion set at the beginning of each simulation. E.g. 30% are HAWKS; if we have 100 players, then each player has a 30% chance of being HAWK]
   - Call this initial parameter HAWK-ODDS
- Payoffs are determined as follows:
   -  Look at what each neighbor did, then:
   -  If I play HAWK and neighbor plays DOVE: 3
   -  If I play DOVE and neighbor plays DOVE: 2
   -  If I play DOVE and neighbor plays HAWK: 1
   - If I play HAWK and neighbor plays HAWK: 0


