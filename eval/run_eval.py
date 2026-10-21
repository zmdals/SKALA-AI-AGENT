from pathlib import Path
import json
import httpx
import time

LABELS_PATH = Path(__file__).parent/"labels.json"
with open(LABELS_PATH, encoding="utf-8") as f:
    labels = json.load(f)
URL = "http://127.0.0.1:8100/chat"
RUN_NAME = "after_clarify"
results = []
for item in labels:
    print(f"id:{item['id']}, query:{item['query']}, expected:{item['expected']}")
    start_time = time.perf_counter()
    data = httpx.post(URL, json={"message":item['query'], "thread_id":f"{RUN_NAME}-{item['id']}"}, timeout=300).json()
    end_time = time.perf_counter()

    targets = [e["target"] for e in data["events"]
               if e.get("type") == "TaskCompleted" and e["source"] == "runbook"]

    # 1. 되묻기 이벤트 찾기
    clarify = [e for e in data["events"] if e.get("type") == "Clarify"]

    # 2. actual 정하기
    if clarify:                                   # 되묻기를 했으면
        if clarify[0]["reason"] == "no_system":
            actual = "CLARIFY"
        else:
            actual = "UNKNOWN_SYSTEM"
    else:                                         # 되묻기를 안 했으면
        actual = targets

    # 3. 정답 판정
    if isinstance(item["expected"], str):         # 정답이 "CLARIFY" / "UNKNOWN_SYSTEM"
        correct = actual == item["expected"]      # 되묻기 종류까지 정확히 같아야 정답
    else:                                         # 정답이 runbook 리스트
        correct = isinstance(actual, list) and set(actual) == set(item["expected"])
    cost_usd = data["metadata"]["cost_usd"]
    time_elapsed = round(end_time - start_time,1)

    res = {"id":item["id"], 
           "query":item["query"], 
           "expected":item["expected"], 
           "actual":actual,
           "correct":correct,
           "elapsed_s":time_elapsed,
           "cost_usd":cost_usd,
           "reply":data["reply"],
           }
    print(res)
    results.append(res)

with open(f"eval/{RUN_NAME}.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

correct = sum(r["correct"] for r in results)
avg_elapsed_s = round(sum(r["elapsed_s"] for r in results) / len(results),1)
total_cost_usd = round(sum(r["cost_usd"] for r in results),3)
print(f"정확도: {correct} / {len(results)}, 평균 응답 시간: {avg_elapsed_s}s, 총 비용: ${total_cost_usd}")