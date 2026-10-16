"""Uniform baseline; no information in history affects its probabilities."""
import random

from .base import validate_ticket


class RandomModel:
    def score_numbers(self, history, target_draw_context=None) -> dict[int, float]:
        return {number: 6 / 45 for number in range(1, 46)}

    def predict(self, history, context=None, k=6, seed=None) -> list[int]:
        if type(k) is not int or k != 6:
            raise ValueError("Lotto tickets require k=6")
        return validate_ticket(random.Random(seed).sample(range(1, 46), k))
