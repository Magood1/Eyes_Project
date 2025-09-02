# FILE: src/fusion_strategies.py

import numpy as np
from typing import Protocol, Dict

class FusionStrategy(Protocol):
    def fuse(self, multi_class_probs: np.ndarray, expert_probs: np.ndarray) -> np.ndarray: ...

class F1ScoreFusion:
    def _calculate_f1_score(self, p_multi, p_expert, epsilon=1e-8):
        return (2 * p_multi * p_expert) / (p_multi + p_expert + epsilon)

    def fuse(self, multi_class_probs: np.ndarray, expert_probs: np.ndarray) -> np.ndarray:
        fused = [multi_class_probs[0]]
        for i in range(len(expert_probs)):
            fused.append(self._calculate_f1_score(multi_class_probs[i + 1], expert_probs[i]))
        fused.append(multi_class_probs[-1])
        return np.array(fused)

class WeightedAverageFusion:
    def __init__(self, multi_class_weight=0.5, expert_weight=0.5):
        self.w1, self.w2 = multi_class_weight, expert_weight

    def fuse(self, multi_class_probs: np.ndarray, expert_probs: np.ndarray) -> np.ndarray:
        fused = [multi_class_probs[0]]
        for i in range(len(expert_probs)):
            fused.append(self.w1 * multi_class_probs[i + 1] + self.w2 * expert_probs[i])
        fused.append(multi_class_probs[-1])
        return np.array(fused)

STRATEGY_REGISTRY: Dict[str, type] = {
    "F1ScoreFusion": F1ScoreFusion,
    "WeightedAverageFusion": WeightedAverageFusion,
}

def get_fusion_strategy(name: str, params: dict) -> FusionStrategy:
    strategy_class = STRATEGY_REGISTRY.get(name)
    if not strategy_class: raise ValueError(f"استراتيجية الدمج '{name}' غير معروفة.")
    return strategy_class(**params)