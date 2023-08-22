# Hawk-Dove with risk attitudes

Hawk/Dove game with variable risk attitudes

## Game description

This is a variant of the Hawk/Dove Game: https://en.wikipedia.org/wiki/Chicken_(game)

| | H | D|
|-|-|-|
| H | 0, 0 | 3, 1|
| D |1, 3| 2, 2|

BACKGROUND: An unpublished paper by Blessenohl shows that the equilibrium in this game is different for EU maximizers than for REU maximizers (all with the same risk-attitude), and that REU maximizers do better as a population (basically, play DOVE more often)

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
- Let `h` be the number of neighbors who played HAWK during the previous round. If `h` > `r`, then play DOVE. Otherwise play HAWK. 
  - [TODO: make sure comparison and risk attitude is defined consistently with other simulations]
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


