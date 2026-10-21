import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv() # 서버 없이 돌려서 직접 해야함.

from agent.retriever import RunbookRetriever
from agent.systems import extract_system_name

ROOT = Path(__file__).resolve().parent.parent
with open(ROOT/"eval"/"labels.json", encoding="utf-8") as f:
    labels = json.load(f)
with open(ROOT/"data"/"monitoring.json", encoding="utf-8") as f:
    monitoring = json.load(f)   

TARGET_IDS = {1, 2, 3, 9, 10, 11, 12}
retriever = RunbookRetriever()

for item in labels:
    if item["id"] not in TARGET_IDS:
        continue
    system = extract_system_name(item["query"])
    info = monitoring[system]

    text_a = item["query"]
    text_b = f"{item['query']}\n상태: {info['status']}\n알림: {','.join(info['alerts'])}"

    type_a, score_a = retriever.classify(text_a)
    type_b, score_b = retriever.classify(text_b)
    print(item["id"], item["expected"], "| A:", type_a, round(score_a, 3), "| B:", type_b, round(score_b, 3))
