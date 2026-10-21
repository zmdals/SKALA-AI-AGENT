from pathlib import Path
import json

def _load_known_systems() -> set[str]:
    """ollama_llm.py/openai_llm.py와 동일한 소스(data/monitoring.json)에서
    시스템 목록을 읽는다 — plan_node가 MCP Prompt에 넘길 system_name을
    쿼리에서 멤버십 매칭으로 뽑아낼 때 쓴다."""
    path = Path(__file__).resolve().parent.parent / "data" / "monitoring.json"
    try:
        return set(json.loads(path.read_text()).keys())
    except (OSError, json.JSONDecodeError):
        return {"auth-service", "web-01"}

KNOWN_SYSTEMS = _load_known_systems()

def extract_system_name(query: str) -> str: 
    """정규식 대신 실제 KNOWN_SYSTEMS 멤버십 매칭 — MCP Prompt(incident_analysis_
    prompt)의 system_name은 "시스템: X" 한 줄짜리 컨텍스트라 항상 정해진 이름
    중 하나로만 고정한다(여러 개 언급돼도 join하지 않음 — 실제 조사 대상 목록은
    이후 plan()의 tasks가 별도로 결정). 쿼리에서 가장 먼저 등장하는 시스템을
    고르고, 하나도 안 걸리면 가장 흔한 사례인 auth-service로 폴백."""
    matches = [(query.index(s), s) for s in KNOWN_SYSTEMS if s in query]
    return min(matches)[1] if matches else "auth-service"

def guess_targets(query: str) -> list[str]:
    """research task가 통째로 0개일 때(모델이 agent=analysis만 던지는 등 계획 자체가
    붕괴됐을 때) 쓰는 복구용 — _guess_target처럼 하나만 고르면 쿼리에 언급된 다른
    시스템이 조사에서 통째로 빠지고, write 단계가 그 빈 자리를 수치까지 지어내서
    채우는 할루시네이션으로 이어진다(실측 사례: cache-service 미조사 → "CPU 53.5%"
    조작). 쿼리에 등장하는 KNOWN_SYSTEMS 전부를 복구한다."""
    matched = sorted(s for s in KNOWN_SYSTEMS if s in query)
    return matched or ["auth-service"]