"""
翻译系统: LLM (主要) → 百度翻译 (降级) → 原文
"""
import os
import time
import requests
from config.settings import settings

BAIDU_APP_ID = settings.get("BAIDU_TRANSLATE_APP_ID", "")
BAIDU_API_KEY = settings.get("BAIDU_TRANSLATE_API_KEY", "")
BAIDU_SECRET = settings.get("BAIDU_TRANSLATE_SECRET", "")

_baidu_token = None
_baidu_token_expires = 0

TRANSLATE_SYSTEM_PROMPT = (
    "Translate the following academic paper title or abstract into concise, "
    "faithful Chinese. Keep technical terms precise. Output only the translation."
)


def _get_baidu_token():
    """Get Baidu AI Cloud access token (cached, auto-refresh)"""
    global _baidu_token, _baidu_token_expires
    now = time.time()
    if _baidu_token and now < _baidu_token_expires - 300:
        return _baidu_token
    if not BAIDU_API_KEY or not BAIDU_SECRET:
        return None
    try:
        resp = requests.post(
            "https://aip.baidubce.com/oauth/2.0/token",
            params={
                "grant_type": "client_credentials",
                "client_id": BAIDU_API_KEY,
                "client_secret": BAIDU_SECRET,
            },
            timeout=10,
        )
        data = resp.json()
        _baidu_token = data.get("access_token")
        _baidu_token_expires = now + data.get("expires_in", 2592000)
        return _baidu_token
    except Exception as e:
        print(f"[Baidu Token] {e}")
        return None


def translate_with_llm(text: str, endpoint: str = "", model: str = "", api_key: str = "") -> str:
    """Translate using OpenAI-compatible LLM API"""
    if not endpoint or not api_key:
        return None
    try:
        ep = endpoint.rstrip("/")
        resp = requests.post(
            f"{ep}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": TRANSLATE_SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                "temperature": 0.2,
                "max_tokens": 500,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[Translate LLM] {e}")
    return None


def translate_with_baidu(text: str, from_lang="zh", to_lang="en") -> str:
    """Translate using Baidu AI Cloud API (free tier)"""
    token = _get_baidu_token()
    if not token:
        return None
    try:
        resp = requests.post(
            f"https://aip.baidubce.com/rpc/2.0/mt/texttrans/v1?access_token={token}",
            json={"from": from_lang, "to": to_lang, "q": text},
            timeout=10,
        )
        data = resp.json()
        results = data.get("result", {}).get("trans_result", [])
        if results:
            return results[0].get("dst", "")
    except Exception as e:
        print(f"[Translate Baidu] {e}")
    return None


def translate_text(text: str, mode: str = "llm", llm_config: dict = None) -> str:
    """Main translation: try LLM → Baidu → original"""
    if not text or not text.strip():
        return text

    if mode == "llm":
        cfg = llm_config or {}
        endpoint = cfg.get("endpoint", os.getenv("LLM_ENDPOINT", ""))
        model = cfg.get("model", os.getenv("LLM_MODEL", ""))
        api_key = cfg.get("api_key", os.getenv("LLM_API_KEY", ""))
        result = translate_with_llm(text, endpoint, model, api_key)
        if result:
            return result

    if mode in ("llm", "baidu"):
        result = translate_with_baidu(text)
        if result:
            return result

    return text
