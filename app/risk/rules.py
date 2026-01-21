from __future__ import annotations

RISK_RULES: dict[str, list[dict]] = {
    "net_profit_margin": [
        {"min": 0.2, "level": "low", "score": 10},
        {"min": 0.1, "level": "medium", "score": 50},
        {"min": -1e9, "level": "high", "score": 80},
    ],
    "current_ratio": [
        {"min": 1.5, "level": "low", "score": 15},
        {"min": 1.0, "level": "medium", "score": 50},
        {"min": -1e9, "level": "high", "score": 80},
    ],
    "roe": [
        {"min": 0.15, "level": "low", "score": 10},
        {"min": 0.08, "level": "medium", "score": 55},
        {"min": -1e9, "level": "high", "score": 85},
    ],
}
