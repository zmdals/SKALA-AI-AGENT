from dotenv import load_dotenv
import os
import httpx
import math

load_dotenv()
key = os.environ["OPENAI_API_KEY"]

URL = "https://api.openai.com/v1/embeddings"
headers = {"Authorization": f"Bearer {key}"}

def embed(texts: list[str]) -> list[list[float]]:
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

texts = ["web-01 CPU 급증해요", "CPU 사용률이 갑자기 치솟음", "디스크 공간이 부족함"]
vecs = embed(texts)
print("1↔2:", cosine(vecs[0], vecs[1]))
print("1↔3:", cosine(vecs[0], vecs[2]))

#print(f"벡터 길이: {len(data['data'][0]['embedding'])}, 앞 5개: {data['data'][0]['embedding'][:5]}, 사용한 토큰 수:{data['usage']['total_tokens']}개")