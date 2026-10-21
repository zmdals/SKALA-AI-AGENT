from pathlib import Path
import json

def _load_known_systems() -> set[str]:
    """data/monitoring.json에서 모니터링 대상 시스템 목록을 읽는다."""
    path = Path(__file__).resolve().parent.parent / "data" / "monitoring.json"
    try:
        return set(json.loads(path.read_text()).keys())
    except (OSError, json.JSONDecodeError):
        return {"auth-service", "web-01"}

KNOWN_SYSTEMS = _load_known_systems()

def extract_system_name(query: str) -> str: 
    """쿼리에서 가장 먼저 등장하는 시스템 1개를 고른다. 없으면 auth-service로 폴백(추후 개선 대상)."""
    matches = [(query.index(s), s) for s in KNOWN_SYSTEMS if s in query]
    return min(matches)[1] if matches else "auth-service"

def guess_targets(query: str) -> list[str]:
    """research task가 통째로 0개일 때(모델이 agent=analysis만 던지는 등 계획 자체가
    붕괴됐을 때) 쓰는 복구용 — extract_system_name처럼 하나만 고르면 쿼리에 언급된 다른
    시스템이 조사에서 통째로 빠지고, write 단계가 그 빈 자리를 수치까지 지어내서
    채우는 할루시네이션으로 이어진다(실측 사례: cache-service 미조사 → "CPU 53.5%"
    조작). 쿼리에 등장하는 KNOWN_SYSTEMS 전부를 복구한다."""
    matched = sorted(s for s in KNOWN_SYSTEMS if s in query)
    return matched or ["auth-service"]