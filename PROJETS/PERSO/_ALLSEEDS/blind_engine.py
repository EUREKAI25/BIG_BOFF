
import numpy as np

def generate_pairs_with_wait(max_bets: int, rng: np.random.Generator, trigger_color: int = 1):
    pairs = []
    bets_placed = 0
    waiting_for_trigger = True

    while bets_placed < max_bets:
        toss = 1 if rng.random() < 0.5 else 0

        if waiting_for_trigger:
            if toss == trigger_color:
                next_toss = 1 if rng.random() < 0.5 else 0
                if next_toss == trigger_color:
                    pairs.append((2.0, 3.0))
                    waiting_for_trigger = False
                else:
                    pairs.append((3.0, 2.0))
                    waiting_for_trigger = True
                bets_placed += 1
        else:
            toss2 = 1 if rng.random() < 0.5 else 0
            if toss2 == trigger_color:
                pairs.append((2.0, 3.0))
                waiting_for_trigger = False
            else:
                pairs.append((3.0, 2.0))
                waiting_for_trigger = True
            bets_placed += 1

    return pairs
