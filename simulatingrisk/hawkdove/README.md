# Hawk-Dove with risk attitudes

Hawk/Dove game with risk attitudes

## Game description

This is a variant of the Hawk/Dove Game: https://en.wikipedia.org/wiki/Chicken_(game)

| | H | D|
|-|-|-|
| H | 0, 0 | 3, 1|
| D |1, 3| 2, 2|

BACKGROUND: An unpublished paper by Simon Blessenohl shows that the equilibrium in this game is different for EU maximizers than for REU maximizers (all with the same risk-attitude), and that REU maximizers do better as a population (basically, play DOVE more often)

We want to know: what happens when different people have _different_ risk-attitudes.
(See also variant simulation [Hawk/Dove game with multiple risk attitudes](../hawkdovemulti/). )

GAME: Hawk-Dove with risk-attitudes

Players arranged on a lattice [options for both 4 neighbors (AYBD) and 8 neighbors (XYZABCDE)]

| | | |
|-|-|-|
| X | Y |Z |
|A | **I** |  B |
| C | D | E |

- Payoffs are determined as follows:
   -  Look at what each neighbor did, then:
   -  If I play HAWK and neighbor plays DOVE: 3
   -  If I play DOVE and neighbor plays DOVE: 2
   -  If I play DOVE and neighbor plays HAWK: 1
   - If I play HAWK and neighbor plays HAWK: 0

Each player on a lattice (grid in Mesa):
- Has parameter $r$ [from 0 to 9]
- Let `d` be the number of neighbors who played DOVE during the previous round. If $d >= r$, then play HAWK. Otherwise play DOVE. (Agents who are risk-avoidant only play HAWK if there are a lot of doves around them. More risk-avoidance requires a higher number of doves to get an agent to play HAWK.)
- The proportion of neighbors who play DOVE corresponds to your probability of encountering a DOVE when playing a randomly-selected neighbor. The intended interpretation is that you maximize REU for this probability of your opponent playing DOVE. Thus, $r$ corresponds to the probability above which playing HAWK maximizes REU.
  - Choice of play for the first round:
    - Who is a HAWK and who is a DOVE is randomly determined; proportion set at the beginning of each simulation. E.g. 30% are HAWKS; if we have 100 players, then each player has a 30% chance of being HAWK;
   - This initial parameter is called HAWK-ODDS; default is 50/50


## Payoffs and risk attitudes

This game has a discrete set of options instead of probability, so instead of defining `r` as a value between 0.0 and 1.0, we use discrete values based on the choices. For the game that includes diagonal neighbors when agents play all neighbors:

<table>
   <tr><th>r</th></th><th>0</th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th><th>6</th><th>7</th><th>8</th><th>9</th></tr>
   <tr>
      <th>Plays H when:</th>
      <td>always</td>
      <td>$\geq1$ D</td>
      <td>$\geq2$ D</td>
      <td>$\geq3$ D</td>
      <td>$\geq4$ D</td>
      <td>$\geq5$ D</td>
      <td>$\geq6$ D</td>
      <td>$\geq7$ D</td>
      <td>$\geq8$ D</td>
      <td>never</td>
   </tr>
   <tr><td></td>
      <td colspan="4">risk seeking</td>
      <td>EU maximizer<br>(risk neutral)</td>
      <td>EU maximizer<br>(risk neutral)</td>
   <td colspan="4">risk avoidant</td>
   </tr>
</table>


An REU maximizer will play HAWK when
```math
r(p) > \frac{(D,H)-(H,H)}{(H,D)-(D,D)}
```
In other words, when $r(p) > 0.52$. An EU maximizer, with $r(p) = p$, will play HAWK when $p > 0.52$, e.g., when more than 4 out of 8 neighbors play DOVE. Thus, $r = 4$ corresponds to risk-neutrality (EU maximization), $r < 4$ corresponds to risk-inclination, and $r > 4$ corresponds to risk-avoidance.

Payoffs were chosen to avoid the case in which two choices had equal expected utility for some number of neighbors. For example, if the payoff of $(D,D)$ was $(2,2)$, then at $p = 0.5$ (4 of 8 neighbors), then EU maximizers would be indifferent between HAWK and DOVE; in this case, no r-value would correspond to EU maximization, since $r = 4$ strictly prefers DOVE and $r = 3$ strictly prefers HAWK.

Another way to visualize the risk attitudes and choices in this game is this table, which shows when agents will play Hawk or Dove based on their risk attitudes (going down on the left side) and the number of neighbors playing Dove (across the top).

<table>
   <tr><td colspan="2"></td><th colspan="9"># of neighors playing DOVE</thr></tr>
   <tr><td><th>r</th><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td></tr>
   <tr><td rowspan="4">risk seeking</td><th>0</th><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td></tr>
   <tr><th>1</th><td>D</td><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td></tr>
   <tr><th>2</th><td>D</td><td>D</td><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td></tr>
   <tr><th>3</th><td>D</td><td>D</td><td>D</td><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td></tr>
   <tr><td rowspan="2">neutral</td></td><th>4</th><td>D</td><td>D</td><td>D</td><td>D</td><td>H</td><td>H</td><td>H</td><td>H</td><td>H</td></tr>
   <tr><th>5</th><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td><td>H</td><td>H</td><td>H</td><td>H</td></tr>
   <tr><td rowspan="4">risk avoidant</td><th>6</th><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td><td>H</td><td>H</td><td>H</td></tr>
   <tr><th>7</th><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td><td>H</td><td>H</td></tr>
   <tr><th>8</th><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td><td>H</td></tr>
   <tr><th>9</th><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td><td>D</td></tr>
</table>

## Convergence

The model is configured to stop automatically when it has stabilized. Convergence is based on a stable rolling average of the percent of agents in the simulation playing hawk.

A rolling average of the percent of agents playing hawk is calculated every round based on the percent for the last **30** rounds.  The rolling average is not calculated until after at least **15** rounds.

When we have collected the rolling average for at least **15** rounds and the last **30** rolling averages are the same when rounded to 2 percentage points, we consider the simulation converged.


