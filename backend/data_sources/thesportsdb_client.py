from __future__ import annotations

import os
from typing import Any, Dict, List

import requests

KBO_LEAGUE_NAME = "Korean KBO League"
DEFAULT_API_KEY = os.getenv("THESPORTSDB_API_KEY", "3")

FALLBACK_TEAMS: List[Dict[str, str]] = [
    {"id": "KBO-LG", "name": "LG Twins", "short_name": "LG", "stadium": "Jamsil"},
    {"id": "KBO-DO", "name": "Doosan Bears", "short_name": "DOO", "stadium": "Jamsil"},
    {"id": "KBO-KT", "name": "KT Wiz", "short_name": "KT", "stadium": "Suwon"},
    {"id": "KBO-SSG", "name": "SSG Landers", "short_name": "SSG", "stadium": "Incheon"},
    {"id": "KBO-NC", "name": "NC Dinos", "short_name": "NC", "stadium": "Changwon"},
    {"id": "KBO-KIA", "name": "KIA Tigers", "short_name": "KIA", "stadium": "Gwangju"},
    {"id": "KBO-LOT", "name": "Lotte Giants", "short_name": "LOT", "stadium": "Sajik"},
    {"id": "KBO-SAM", "name": "Samsung Lions", "short_name": "SAM", "stadium": "Daegu"},
    {"id": "KBO-HAN", "name": "Hanwha Eagles", "short_name": "HAN", "stadium": "Daejeon"},
    {"id": "KBO-KIW", "name": "Kiwoom Heroes", "short_name": "KIW", "stadium": "Gocheok"},
]


class TheSportsDBClient:
    def __init__(self, api_key: str = DEFAULT_API_KEY, timeout: int = 8) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = f"https://www.thesportsdb.com/api/v1/json/{api_key}"

    def _get_json(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{path}"
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_kbo_teams(self) -> Dict[str, Any]:
        try:
            payload = self._get_json("search_all_teams.php", {"l": KBO_LEAGUE_NAME})
            teams = payload.get("teams") or []
            normalized = [
                {
                    "id": t.get("idTeam") or "",
                    "name": t.get("strTeam") or "",
                    "short_name": t.get("strTeamShort") or t.get("strTeam") or "",
                    "stadium": t.get("strStadium") or "",
                }
                for t in teams
                if t.get("idTeam") and t.get("strTeam")
            ]
            if normalized:
                return {"source": "thesportsdb", "teams": normalized}
        except Exception:
            pass

        return {"source": "fallback", "teams": FALLBACK_TEAMS}

    def get_recent_events(self, team_id: str) -> List[Dict[str, Any]]:
        if not team_id:
            return []
        try:
            payload = self._get_json("eventslast.php", {"id": team_id})
            return payload.get("results") or []
        except Exception:
            return []

