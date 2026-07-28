"""
LLM 查询扩展：用户写中文描述 → LLM 扩展成英文+同义词
"""
import os
import json
import requests

LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

EXPAND_SYSTEM_PROMPT = (
    "You are a chemistry research assistant. Expand the user's research interest description "
    "into a concise English query for paper matching. Include key techniques, materials, "
    "reactions, and related terms. Keep under 100 words. Output only the expanded query."
)


def expand_query(description: str, keywords: str = "") -> str:
    if not LLM_ENDPOINT or not LLM_API_KEY:
        return description

    user_text = description
    if keywords:
        user_text = f"{description}\nKeywords: {keywords}"

    try:
        endpoint = LLM_ENDPOINT.rstrip("/")
        resp = requests.post(
            f"{endpoint}/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": EXPAND_SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                ],
                "temperature": 0.3,
                "max_tokens": 200,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            if content:
                return content
    except Exception as e:
        print(f"[LLM Expander] Failed: {e}")

    return description
