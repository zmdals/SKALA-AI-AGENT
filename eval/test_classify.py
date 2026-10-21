import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv() # 서버 없이 돌려서 직접 해야함.

from agent.retriever import RunbookRetriever
from agent.systems import guess_targets

ROOT = Path(__file__).resolve().parent.parent
with open(ROOT/"eval"/"labels.json", encoding="utf-8") as f:
    labels = json.load(f)
with open(ROOT/"data"/"monitoring.json", encoding="utf-8") as f:
    monitoring = json.load(f)   

TARGET_IDS = {1, 2, 3, 4, 5, 6, 9, 10, 11, 12}
retriever = RunbookRetriever()

for item in labels:
    if item["id"] not in TARGET_IDS:
        continue

    found = set()                                   # 이 질문에서 나온 runbook 유형들
    for system in guess_targets(item["query"]):     # 질문에 나온 서버 전부
        info = monitoring[system]
        if info["alerts"]:                          # 그 서버에 알림이 있으면
            text = f"{system} 상태: {info['status']}\n알림: {','.join(info['alerts'])}"
        else:                                       # 알림이 없으면 (healthy)
            text = item["query"]
        incident_type, score = retriever.classify(text)
        print(f"   {system}: {incident_type} ({score:.3f})")
        found.add(incident_type)

    ok = found == set(item["expected"])
    print(item["id"], item["expected"], "→", sorted(found), "✅" if ok else "❌")