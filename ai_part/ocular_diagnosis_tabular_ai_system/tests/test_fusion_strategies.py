# FILE: tests/test_fusion_strategies.py

import pytest
import numpy as np
from src.fusion_strategies import F1ScoreFusion, WeightedAverageFusion, get_fusion_strategy

@pytest.fixture
def sample_probs():
    return np.array([0.1, 0.8, 0.05, 0.05, 0, 0, 0, 0.1]), np.array([0.7, 0.1, 0.05, 0, 0, 0])

def test_f1_fusion_output_shape(sample_probs):
    multi, expert = sample_probs
    strategy = F1ScoreFusion()
    fused = strategy.fuse(multi, expert)
    assert fused.shape == (8,)

def test_get_strategy_factory():
    strategy = get_fusion_strategy("F1ScoreFusion", {})
    assert isinstance(strategy, F1ScoreFusion)
    with pytest.raises(ValueError):
        get_fusion_strategy("UnknownStrategy", {})