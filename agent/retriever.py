import json
import math
import os
from pathlib import Path

import httpx


URL = "https://api.openai.com/v1/embeddings"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RUNBOOK_DIR = DATA_DIR / "runbooks"
# runbook 본문은 "대응 절차"라 질문("증상")과 잘 안 맞는다 → 유형별 일반적인 증상 설명을
# 앞에 붙여서 같이 임베딩한다(문서 보강). runbook 파일 자체는 건드리지 않아 write 노드가
# 읽는 매뉴얼 내용은 Before와 동일하게 유지된다.
SYMPTOMS_PATH = DATA_DIR / "runbook_symptoms.json"
SYSTEM_DESC_PATH = DATA_DIR / "system_descriptions.json"

def embed(texts: list[str]) -> list[list[float]]:
    key = os.environ["OPENAI_API_KEY"]
    headers = {"Authorization": f"Bearer {key}"}
    body = {"model": "text-embedding-3-small", "input": texts}
    resp = httpx.post(URL, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return [item['embedding'] for item in data["data"]]


def cosine(a: list[float], b: list[float]) -> float:
    dot    = sum(x * y for x, y in zip(a, b))   # 같은 자리끼리 곱해서 전부 더함
    norm_a = math.sqrt(sum(x*x for x in a))    # a의 길이
    norm_b = math.sqrt(sum(y*y for y in b))    # b의 길이
    return dot / (norm_a * norm_b)

class EmbeddingIndex:
    """문서 여러 개를 미리 임베딩해 두고, 텍스트와 가장 가까운 문서의 이름을 찾는다.
    runbook 분류(RunbookRetriever)와 서버 후보 추천(system matcher)이 같이 쓴다."""

    def __init__(self, docs: dict[str, str]):
        if not docs:
            raise ValueError("임베딩할 문서가 없습니다")
        names = list(docs.keys())
        vectors = embed(list(docs.values()))               # 한 번에 임베딩
        self.index = list(zip(names, vectors))             # [("cpu-spike", [...]), ...]

    def classify(self, text: str) -> tuple[str, float]:
        query_vec = embed([text])[0]                       # text 하나를 임베딩
        best_name, best_score = "", -1.0
        for name, vec in self.index:
            score = cosine(query_vec, vec)
            if score > best_score:
                best_name, best_score = name, score
        return best_name, best_score


class RunbookRetriever(EmbeddingIndex):
    """runbook 6개(증상 설명 + 본문)로 만든 EmbeddingIndex."""

    def __init__(self, runbook_dir: Path = RUNBOOK_DIR):
        paths = sorted(runbook_dir.glob("*.md"))           # runbook 파일 6개
        if not paths:
            raise ValueError(f"runbook 파일이 없습니다: {runbook_dir}")
        symptoms = json.loads(SYMPTOMS_PATH.read_text(encoding="utf-8"))
        docs = {p.stem: f"증상: {symptoms[p.stem]}\n\n{p.read_text(encoding='utf-8')}"   # 증상 설명 + 본문
                for p in paths}
        super().__init__(docs)

def build_system_matcher(path: Path = SYSTEM_DESC_PATH) -> EmbeddingIndex:
    """서버 설명으로 만든 EmbeddingIndex — 서버 이름이 없는 질문에서 후보를 추천할 때 쓴다."""
    return EmbeddingIndex(json.loads(path.read_text(encoding="utf-8")))