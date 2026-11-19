# Glossary

Terms used in the line-following AI unit, in alphabetical order. Names in `code font` are what you'll see in the code.

**Average fitness** — The mean fitness of all 40 cars in a generation. It is the blue line on the training chart. When it climbs toward the champion's line, the whole population is getting better, not just one lucky car.

**Bias (training data bias)** — When what a brain learned from reflects the examples it trained on, not the whole world it will face. Every car here trains on Track A only, so its brain is biased toward Track A's shape and corners. Time trial it on Track B and the bias can show up as crashes or slower laps. The fix is not more training on the same track: it is more varied training examples.

**Checkpoint** — One of the waypoints along the track (`track_points`). A car "passes" a checkpoint by getting within 20 pixels of it. Checkpoints are how the program measures real progress along the track.

**Champion** — The car with the highest fitness in a generation. It is copied into the next generation unchanged, so training never loses its best driver. The champion's weights are what get saved to `best_weights.json`.

**Crashed** — The time-trial result when a car leaves the track. A car has left the track when *none* of its sensors see the line. (Only the sensors are checked, not the body of the car.)

**Crossover** — Making a child brain by mixing two parents. For each of the 18 weights, the child copies it from one parent or the other, picked at random.

**DNF** — "Did not finish." A time-trial run that ends without a lap time: crashed, stuck, or timed out.

**Exploit** — Using what has already been learned to perform well, instead of trying something new. A time trial is pure exploitation: nothing is learned, and the car simply drives with the best weights found in training. Notice what is being exploited: the *learning* (the weights), not the raw data. The car doesn't look anything up. The scores from thousands of trial laps have already been squeezed into 18 numbers. Inside training, keeping the champion and breeding the top 20% is exploitation too. See **Explore**.

**Explore** — Trying things you haven't tried, to find out what works. Training is mostly exploration: it starts with random weights, and each generation of 40 cars is a batch of experiments. The scores they earn are the "data", gathered across many cars, not by one car while driving. Mutation is the exploring built into training: small random changes that might be better or worse. Too little exploring and training gets stuck (**Plateau**). Too much and it never settles on anything good. People face the same choice: try a new restaurant, or go to your favourite? See **Exploit**.

**Fitness** — The score for how well a brain drove. It rewards checkpoints passed and staying alive, and subtracts the distance still to go to the next checkpoint. Each brain is scored at several speeds and the scores are averaged. A bigger number is better, but it has no maximum, so use the speed checklist to know when you're *done*.

**Generalization** — How well a brain does on situations it was *not* trained on. A brain that drives Track A perfectly but crashes on Track B has learned Track A, not "how to follow a line". Time trials on Track B measure generalization.

**Generation** — One round of training: all 40 cars drive (up to 25 simulated seconds), the best are chosen, and they breed the next 40. "Gen 12" means the twelfth round.

**Genetic algorithm (GA)** — The method used to train the brains. Keep the best drivers, breed them, mutate a little, repeat. It copies natural selection.

**Genome** — The complete list of a brain's 18 weights. The program stores it as one flat list of numbers. "Genome" and "weights" mean almost the same thing here: the genome is the whole list, a weight is one number in it.

**Hidden neuron / hidden node** — A neuron between the inputs and outputs. This brain has 6 (`HIDDEN_NODES`). Each one looks at both sensors and does its own small calculation.

**Input** — A number going into the brain. Here there are two: the left and right sensor readings, each 1 (on the line) or 0 (off it).

**Lap** — One full trip around the track, which means passing every checkpoint once. A lap is what the time trial times, and what the training "speed checklist" tests for.

**Lap time** — How many simulated seconds a car needed to finish one lap. The menu keeps your best lap time at each speed.

**Mutation** — A small random change to a child's weights. It is how training *explores*. About 12% of weights (`MUTATION_RATE`) get nudged by up to ±0.4 (`MUTATION_STRENGTH`). Without mutation, the population could stop discovering anything new.

**Neural network** — A small calculating machine made of neurons joined by weights. This one is 2 inputs → 6 hidden neurons → 1 output. It takes sensor readings in and gives a steering decision out.

**Neuron** — One calculating unit: multiply each input by its weight, add the results, squash the total with `tanh`.

**Output** — A number coming out of the brain. This brain has just one: how hard to turn (−1 = full left, +1 = full right).

**Overfitting** — Getting very good at exactly what you were scored on, and worse at everything else (a different speed, or a different track). Brains scored only at normal speed lose their margin at high speed. That's why every brain is tested at 1× to 3× speed.

**Plateau** — A stretch of training where the champion stops improving. The training panel says "Plateau" after 15 generations with no gain. More training probably won't help, because the exploring has stopped finding anything better. Try stopping and training again from scratch, since every run is random.

**Population** — All the cars in one generation (40, `POPULATION_SIZE`), each with its own brain.

**Progress bar (Lap)** — On the training panel, how much of one lap the champion covered at normal speed.

<!-- CLASS-SPECIFIC: names the class's Stage 2 block program and sensor B. See CLASS-SPECIFIC.md. -->

**Rule (hand-written)** — The program *you* wrote for your robot in Stage 2. Each block is a decision you made, like "if sensor B sees black, turn left." A rule is not the same as an **untrained** brain: a rule has decisions you wrote in, an untrained brain has none. Rules are readable and change one case at a time. Weights are the opposite: found by training, and a change to one affects many answers. Menu option 4 compares them side by side.

**Selection** — Choosing which cars become parents. Here the top 20% by fitness (at least 4 cars) survive to breed.

**Sensor** — A light reader on the car. Each sensor reports on the line (dark) or off the line (light). Two sensors ride the two edges of the track, matching the real robot.

**Simulation (sim)** — The pygame version of the track and cars. *Sim time* is the clock inside the simulation. It runs in fixed steps (1/60 s) so the same weights always give the same time on any laptop.

**Solved** — Training's definition of "done": the champion finishes a lap at *every* training speed (1×, 1.5×, 2×, 2.5×, 3×). When all five speed boxes turn green, the panel says SOLVED. You can keep training for more reliability, but you already have a brain that works.

**Speed multiplier** — How fast the car drives compared with normal (1×). The time-trial slider goes from 0.5× to 3×. Faster is harder to steer because the car has the same turning rate but covers more ground.

**Stuck** — The time-trial result when the car goes too long without reaching a new checkpoint (15 simulated seconds at 1×). It can still be moving, for example circling. The limit is stretched at slow speeds, so a slow car isn't penalised for being slow.

**Tanh** — A squashing function. It turns any number into one between −1 and 1, so no single neuron can shout louder than the rest.

**Time trial** — One car, driven by your saved weights, runs one lap while the clock is running. It tells you *how good* the brain is, not just that training improved. It *exploits* what training learned. With no saved weights it runs an **untrained** car instead. Press T to run it on Track B too.

**Timeout** — The time-trial result when a run takes too long (120 s at 1×, longer at slower speeds).

**Track A / Track B** — The two tracks in the simulation. **Track A** is the training track: every car trains on it. **Track B** has a different shape (squarer corners and a dent in the bottom edge) and is *never* used in training, so a lap on it shows how the brain copes with something new. Press **T** in the time trial to switch. Your best times are kept separately for each track.

**Training** — Evolving better weights, generation after generation. This is the *exploring* phase. The car doesn't learn while driving. Instead, whole populations of cars are tried, and the weights of the winners are bred together.

**Untrained** — A brain whose weights are still random, like every car in generation 1. It is *not* a bad rule: it has no decisions in it at all, so it steers by chance, sometimes the right way and often the wrong way. A rule has knowledge you wrote in, an untrained brain has none, and a trained brain has knowledge it found by exploring. The time trial and Rules vs Weights page can both show an untrained brain.

**Weight** — A single number that turns one signal up or down, like a volume knob. This brain has 18. In an **untrained** brain they are random, and training finds good ones. Together they *are* the brain. See [weights-explained.md](weights-explained.md).
