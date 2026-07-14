# -*- coding: utf-8 -*-
"""DeepSeek API 调用封装。

使用 OpenAI 兼容的 Chat Completions 接口，启用 JSON 输出模式，
并提供一次失败自动重试的能力。
"""

import json
import os
import time

import requests


class DeepSeekError(Exception):
    """DeepSeek 调用相关异常。"""


def _get_config():
    """从环境变量读取 API 配置。"""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip().rstrip("/")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat").strip()
    return api_key, base_url, model


def chat_json(system_prompt, user_prompt, timeout=120, max_retries=1):
    """调用 DeepSeek，返回解析后的 JSON（dict）。

    - system_prompt / user_prompt：系统与用户提示词
    - 启用 response_format=json_object，保证返回可被 json.loads 解析
    - 失败时最多重试 max_retries 次
    """
    api_key, base_url, model = _get_config()
    if not api_key:
        raise DeepSeekError("未配置 DEEPSEEK_API_KEY，请在 .env 中填写后重启。")

    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
        "stream": False,
    }

    last_error = None
    # 首次调用 + 重试，总共尝试 max_retries + 1 次
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code != 200:
                raise DeepSeekError(f"接口返回 {resp.status_code}：{resp.text[:300]}")

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as exc:
            last_error = exc
            # 最后一次失败则不再等待
            if attempt < max_retries:
                time.sleep(1.5)

    raise DeepSeekError(f"调用 DeepSeek 失败：{last_error}")
