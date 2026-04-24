from __future__ import annotations


def calculate_overall_confidence(confidence_map: dict[str, float]) -> float:
    if not confidence_map:
        return 0.0
    return round(sum(confidence_map.values()) / len(confidence_map), 2)
