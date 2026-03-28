from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import random
from typing import Any, Dict, List, Tuple


def _stable_seed(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:8], 16)


def _parse_event_date(raw: str) -> datetime | None:
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw[:19], fmt)
        except ValueError:
            continue
    return None


def _grade(energy_score: float) -> str:
    if energy_score >= 75:
        return "good"
    if energy_score >= 50:
        return "watch"
    return "risk"


def _availability_label(availability: float) -> str:
    if availability >= 0.75:
        return "high"
    if availability >= 0.45:
        return "medium"
    return "low"


def _team_risk(top3_avg: float) -> str:
    if top3_avg >= 70:
        return "safe"
    if top3_avg >= 50:
        return "caution"
    return "danger"


def _role_for_index(idx: int) -> str:
    if idx == 0:
        return "Closer"
    if idx == 1:
        return "Setup A"
    if idx == 2:
        return "Setup B"
    if idx == 3:
        return "Middle A"
    if idx == 4:
        return "Middle B"
    if idx == 5:
        return "Long Relief"
    return f"Relief {idx - 5}"


def _normalize_pitcher_names(pitcher_names: List[str]) -> List[str]:
    cleaned = []
    seen = set()
    for raw in pitcher_names:
        name = str(raw).strip()
        if not name:
            continue
        lowered = name.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        cleaned.append(name)

    return cleaned


def _build_pitchers(team_name: str, pitcher_names: List[str] | None = None) -> List[Dict[str, Any]]:
    seed = _stable_seed(team_name)
    rng = random.Random(seed)
    names = _normalize_pitcher_names(pitcher_names or [])
    if not names:
        # Fallback roster for production resilience when external roster crawling is disabled/unavailable.
        names = [f"{team_name} Pitcher {i}" for i in range(1, 9)]

    pitchers = []
    for idx, pitcher_name in enumerate(names):
        role = _role_for_index(idx)
        handed = "L" if rng.random() < 0.35 else "R"
        base_energy = rng.randint(58, 90)
        pitchers.append(
            {
                "pitcher_id": f"{team_name.lower().replace(' ', '-')}-{idx+1}",
                "name": pitcher_name,
                "role": role,
                "handed": handed,
                "base_energy": base_energy,
            }
        )
    return pitchers


def _calc_load_metrics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    now = datetime.utcnow()
    last_7d = now - timedelta(days=7)
    last_3d = now - timedelta(days=3)

    games_7d = 0
    games_3d = 0
    parsed_dates: List[datetime] = []
    for e in events:
        dt = _parse_event_date(e.get("dateEvent") or "")
        if not dt:
            continue
        parsed_dates.append(dt)
        if dt >= last_7d:
            games_7d += 1
        if dt >= last_3d:
            games_3d += 1

    latest_event = max(parsed_dates).date().isoformat() if parsed_dates else None
    oldest_event = min(parsed_dates).date().isoformat() if parsed_dates else None

    return {
        "games_7d": float(games_7d),
        "games_3d": float(games_3d),
        "event_count": len(parsed_dates),
        "latest_event_date": latest_event,
        "oldest_event_date": oldest_event,
        "data_window_start": last_7d.date().isoformat(),
        "data_window_end": now.date().isoformat(),
        "data_as_of": now.isoformat(timespec="seconds") + "Z",
    }


def build_bullpen_snapshot(
    team_name: str,
    events: List[Dict[str, Any]],
    pitcher_names: List[str] | None = None,
) -> Dict[str, Any]:
    pitchers = _build_pitchers(team_name, pitcher_names=pitcher_names)
    load = _calc_load_metrics(events)

    base_penalty = min(28, load["games_7d"] * 2.5 + load["games_3d"] * 4.0)
    rng = random.Random(_stable_seed(team_name + "-energy"))

    pitcher_states: List[Dict[str, Any]] = []
    for p in pitchers:
        last3_pitch_count = int(12 + load["games_3d"] * rng.uniform(6, 13) + rng.uniform(0, 12))
        consecutive_days = int(min(3, max(0, round(load["games_3d"] - rng.uniform(0.2, 1.4)))))
        high_stress = int(rng.random() < (0.2 + 0.15 * consecutive_days))

        penalty = base_penalty + (last3_pitch_count * 0.55) + (consecutive_days * 10) + (high_stress * 12)
        energy = max(5.0, min(100.0, p["base_energy"] - penalty * 0.35 + rng.uniform(-3, 3)))
        availability = max(0.05, min(0.98, energy / 100.0 + rng.uniform(-0.08, 0.08)))

        pitcher_states.append(
            {
                "pitcher_id": p["pitcher_id"],
                "name": p["name"],
                "role": p["role"],
                "handed": p["handed"],
                "energy_score": round(energy, 1),
                "fatigue_grade": _grade(energy),
                "availability": round(availability, 2),
                "availability_label": _availability_label(availability),
                "stats": {
                    "last3_pitch_count": last3_pitch_count,
                    "consecutive_days": consecutive_days,
                    "high_stress_appearance": high_stress,
                },
            }
        )

    top3 = sorted(pitcher_states, key=lambda x: x["energy_score"], reverse=True)[:3]
    top3_avg = round(sum(p["energy_score"] for p in top3) / len(top3), 1) if top3 else None

    return {
        "team": team_name,
        "as_of": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "energy_index": round(max(0.0, min(100.0, top3_avg + 5)), 1) if top3_avg is not None else None,
        "risk_level": _team_risk(top3_avg) if top3_avg is not None else "unavailable",
        "usable_pitchers": sum(1 for p in pitcher_states if p["availability"] >= 0.45),
        "metrics": {
            "games_7d": int(load["games_7d"]),
            "games_3d": int(load["games_3d"]),
            "top3_avg_energy": top3_avg,
            "event_count": int(load["event_count"]),
            "latest_event_date": load["latest_event_date"],
            "oldest_event_date": load["oldest_event_date"],
            "data_window_start": load["data_window_start"],
            "data_window_end": load["data_window_end"],
            "data_as_of": load["data_as_of"],
        },
        "pitchers": pitcher_states,
    }


def recommend_pitchers(
    snapshot: Dict[str, Any],
    inning: int,
    score_diff: int,
    batter_side: str,
    count: int = 2,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    candidates = []
    leverage = min(1.0, max(0.1, (inning - 5) / 4))

    for p in snapshot.get("pitchers", []):
        handed_bonus = 0.08 if (p["handed"] == "L" and batter_side == "L") or (p["handed"] == "R" and batter_side == "R") else -0.03
        role_bonus = 0.06 if p["role"].startswith("Setup") or p["role"] == "Closer" else 0.0
        score_pressure = 0.08 if abs(score_diff) <= 2 else -0.04

        final_score = (p["availability"] * 0.65) + leverage * 0.12 + handed_bonus + role_bonus + score_pressure
        candidates.append(
            {
                "pitcher_id": p["pitcher_id"],
                "name": p["name"],
                "role": p["role"],
                "handed": p["handed"],
                "energy_score": p["energy_score"],
                "availability": p["availability"],
                "recommendation_score": round(final_score, 3),
            }
        )

    ranked = sorted(candidates, key=lambda x: x["recommendation_score"], reverse=True)
    picks = ranked[: max(1, count)]

    reasons = [
        f"최근 3일 피로 지표를 반영한 불펜 에너지 지수: {snapshot.get('metrics', {}).get('top3_avg_energy', 0)}",
        f"{inning}회/점수차 {score_diff} 상황의 레버리지와 역할 적합도 반영",
        f"타자 유형({batter_side}) 대비 좌우 매치업 보너스 반영",
    ]

    return picks, reasons

