from __future__ import annotations

from datetime import datetime
import time
from functools import lru_cache
import os
from pathlib import Path
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError


TEAM_ALIASES: Dict[str, List[str]] = {
    "lg twins": ["lg", "lg twins", "lgt", "lg트윈스", "트윈스", "엘지", "엘지트윈스"],
    "doosan bears": ["doosan", "doosan bears", "doo", "두산", "두산베어스", "베어스"],
    "kt wiz": ["kt", "kt wiz", "ktw", "kt위즈", "케이티", "케이티위즈", "위즈"],
    "ssg landers": ["ssg", "ssg landers", "ssg랜더스", "랜더스"],
    "nc dinos": ["nc", "nc dinos", "ncd", "nc다이노스", "다이노스"],
    "kia tigers": ["kia", "kia tigers", "kia t", "기아", "기아타이거즈", "타이거즈"],
    "lotte giants": ["lotte", "lotte giants", "lot", "롯데", "롯데자이언츠", "자이언츠"],
    "samsung lions": ["samsung", "samsung lions", "sl", "삼성", "삼성라이온즈", "라이온즈"],
    "hanwha eagles": ["hanwha", "hanwha eagles", "han", "한화", "한화이글스", "이글스"],
    "kiwoom heroes": ["kiwoom", "kiwoom heroes", "kh", "키움", "키움히어로즈", "히어로즈"],
}


class KBODataClient:
    """
    Optional roster provider backed by kbodata.
    If kbodata/chromedriver is unavailable, returns empty list so callers can fallback.
    """

    def __init__(self, chromedriver_path: str | None = None) -> None:
        self.chromedriver_path = chromedriver_path or os.getenv("KBO_CHROMEDRIVER_PATH", "").strip()
        self.roster_enabled = str(os.getenv("KBO_ROSTER_ENABLED", "false")).strip().lower() in {"1", "true", "yes", "on"}
        self.fetch_timeout_sec = int(os.getenv("KBO_ROSTER_TIMEOUT_SEC", "20"))
        self.scan_limit_sec = int(os.getenv("KBO_ROSTER_SCAN_LIMIT_SEC", "10"))
        self.cache_ttl_sec = int(os.getenv("KBO_ROSTER_CACHE_TTL_SEC", "1800"))
        self._team_cache: Dict[str, Dict[str, Any]] = {}
        self._league_cache: Dict[str, Any] | None = None

    def get_team_pitcher_names(self, team_name: str) -> Dict[str, Any]:
        if not self.roster_enabled:
            return {"source": "disabled", "pitcher_names": [], "reason": "roster_feature_disabled"}

        team_key = team_name.lower().strip()
        cached = self._team_cache.get(team_key)
        now_ts = time.monotonic()
        if cached and (now_ts - float(cached.get("cached_at", 0)) <= self.cache_ttl_sec):
            return cached.get("result", {})
        if cached:
            self._team_cache.pop(team_key, None)

        resolved_path, resolve_reason = self._resolve_chromedriver_path(self.chromedriver_path)
        if not resolved_path:
            return {"source": "error", "pitcher_names": [], "reason": resolve_reason}

        league_result = self._get_league_pitcher_df(resolved_path)
        if league_result.get("source") != "kbodata":
            return {
                "source": "error",
                "pitcher_names": [],
                "reason": league_result.get("reason", "kbodata_unavailable"),
            }

        pitcher_df = league_result.get("pitcher_df")
        result = self._extract_team_pitchers(team_key, pitcher_df)

        # Keep successful results in-process to avoid repeated Selenium calls.
        if result.get("source") == "kbodata" and result.get("pitcher_names"):
            self._team_cache[team_key] = {"cached_at": now_ts, "result": result}
        return result

    @staticmethod
    @lru_cache(maxsize=2)
    def _resolve_chromedriver_path(explicit_path: str) -> tuple[str | None, str]:
        if explicit_path:
            return explicit_path, "explicit_path"

        # Prefer preinstalled system chromedriver in Linux containers.
        system_candidates = [
            "/usr/bin/chromedriver",
            "/usr/local/bin/chromedriver",
        ]
        for candidate in system_candidates:
            if Path(candidate).exists():
                return candidate, "system_chromedriver"

        # Prefer existing local webdriver-manager cache to avoid network dependency.
        cached = _find_cached_chromedriver()
        if cached:
            return cached, "webdriver_manager_cache"

        # Try webdriver-manager auto-install if user did not provide a path.
        try:
            from webdriver_manager.chrome import ChromeDriverManager  # type: ignore
            driver_path = ChromeDriverManager().install()
            if driver_path:
                return driver_path, "webdriver_manager"
        except Exception:
            pass

        return None, "chromedriver_path_missing"

    def _get_league_pitcher_df(self, chromedriver_path: str) -> Dict[str, Any]:
        now_ts = time.monotonic()
        if self._league_cache and (now_ts - float(self._league_cache.get("cached_at", 0)) <= self.cache_ttl_sec):
            return {"source": "kbodata", "pitcher_df": self._league_cache.get("pitcher_df"), "reason": "ok_cache"}

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self._fetch_recent_pitcher_df, chromedriver_path)
        try:
            if self.fetch_timeout_sec <= 0:
                result = future.result()
            else:
                result = future.result(timeout=self.fetch_timeout_sec)
        except FutureTimeoutError:
            future.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            return {"source": "error", "reason": f"kbodata_timeout_{self.fetch_timeout_sec}s"}
        except Exception as e:
            future.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            return {"source": "error", "reason": f"kbodata_fetch_failed: {e!r}"}
        finally:
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass

        if result.get("source") == "kbodata":
            self._league_cache = {"cached_at": now_ts, "pitcher_df": result.get("pitcher_df")}
        return result

    @staticmethod
    def _fetch_recent_pitcher_df(chromedriver_path: str) -> Dict[str, Any]:
        try:
            import kbodata  # type: ignore
        except Exception:
            return {"source": "error", "reason": "kbodata_not_installed"}

        now = datetime.now()
        pitcher_df = None
        last_error = ""
        scan_limit_sec = int(os.getenv("KBO_ROSTER_SCAN_LIMIT_SEC", "10"))
        start_ts = time.monotonic()
        # Off-season/current-month empty cases are common; scan backward up to 4 months.
        for year, month in _iter_year_months(now.year, now.month, count=4):
            if scan_limit_sec > 0 and (time.monotonic() - start_ts > scan_limit_sec):
                break
            try:
                schedule = kbodata.get_monthly_schedule(year, month, chromedriver_path)
                if schedule is None or len(schedule) == 0:
                    continue
                game_data = kbodata.get_game_data(schedule, chromedriver_path)
                if game_data is None or len(game_data) == 0:
                    continue
                candidate_df = kbodata.pitcher_to_DataFrame(game_data)
                if candidate_df is not None and len(candidate_df) > 0:
                    pitcher_df = candidate_df
                    break
            except Exception as e:
                last_error = f"{type(e).__name__}: {e!r}"
                continue

        if pitcher_df is None or len(pitcher_df) == 0:
            reason = "empty_pitcher_dataframe"
            if last_error:
                reason = f"kbodata_fetch_failed: {last_error}"
            return {"source": "error", "reason": reason}

        return {"source": "kbodata", "pitcher_df": pitcher_df, "reason": "ok"}

    @staticmethod
    def _extract_team_pitchers(team_name_lower: str, pitcher_df: Any) -> Dict[str, Any]:
        try:
            import pandas as pd  # type: ignore
        except Exception:
            return {"source": "error", "pitcher_names": [], "reason": "pandas_not_installed"}

        aliases = TEAM_ALIASES.get(team_name_lower, [team_name_lower])
        aliases_norm = [_norm(a) for a in aliases]

        team_col = _find_col(pitcher_df, ["team", "club"])
        name_col = _find_col(pitcher_df, ["name", "pitcher", "player"])
        date_col = _find_col(pitcher_df, ["date", "game"])

        if not team_col or not name_col:
            return {"source": "error", "pitcher_names": [], "reason": "required_columns_not_found"}

        df = pitcher_df.copy()
        df[team_col] = df[team_col].astype(str)
        team_mask = df[team_col].apply(lambda v: any(alias and alias in _norm(v) for alias in aliases_norm))
        filtered = df[team_mask].copy()
        if len(filtered) == 0:
            return {"source": "error", "pitcher_names": [], "reason": "team_filter_empty"}

        if date_col and date_col in filtered.columns:
            try:
                filtered[date_col] = pd.to_datetime(filtered[date_col], errors="coerce")
                filtered = filtered.sort_values(date_col, ascending=False)
            except Exception:
                pass

        names: List[str] = []
        seen = set()
        for value in filtered[name_col].astype(str).tolist():
            name = value.strip()
            if not name:
                continue
            lowered = name.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            names.append(name)

        return {
            "source": "kbodata",
            "pitcher_names": names,
            "reason": "ok",
        }


def _find_col(df: Any, keywords: List[str]) -> str | None:
    cols = list(df.columns)
    lowered = {c: str(c).lower() for c in cols}
    for key in keywords:
        for c in cols:
            if key in lowered[c]:
                return str(c)
    return None


def _norm(value: str) -> str:
    return "".join(ch for ch in value.lower().strip() if ch.isalnum())


def _iter_year_months(year: int, month: int, count: int) -> List[tuple[int, int]]:
    values: List[tuple[int, int]] = []
    y = year
    m = month
    for _ in range(count):
        values.append((y, m))
        m -= 1
        if m == 0:
            y -= 1
            m = 12
    return values


def _find_cached_chromedriver() -> str | None:
    base = Path.home() / ".wdm" / "drivers" / "chromedriver"
    if not base.exists():
        return None
    candidates = sorted(
        [*base.rglob("chromedriver.exe"), *base.rglob("chromedriver")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return str(candidates[0]) if candidates else None
