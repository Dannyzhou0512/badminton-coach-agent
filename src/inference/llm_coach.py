"""
Optional LLM coach report generation.

The vision/action models keep making the structured judgments. This module only
turns those structured results into a more natural coaching report.
"""

import json
import os
from pathlib import Path
from urllib import request, error


ROOT = Path(__file__).resolve().parents[2]


def load_env_file(path=ROOT / ".env"):
    path = Path(path)
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()


PROVIDERS = {
    "qwen": {
        "name": "Qwen",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "base_url_env": "QWEN_BASE_URL",
        "api_key_env": ["DASHSCOPE_API_KEY", "QWEN_API_KEY"],
        "model": "qwen-plus",
        "model_env": "QWEN_MODEL",
    },
    "zhipu": {
        "name": "ZhipuAI",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "base_url_env": "ZHIPU_BASE_URL",
        "api_key_env": ["ZHIPUAI_API_KEY", "ZHIPU_API_KEY"],
        "model": "glm-4-plus",
        "model_env": "ZHIPU_MODEL",
    },
}


def provider_defaults(provider):
    defaults = dict(PROVIDERS.get(provider, PROVIDERS["qwen"]))
    defaults["base_url"] = os.getenv(defaults["base_url_env"], defaults["base_url"])
    defaults["model"] = os.getenv(defaults["model_env"], defaults["model"])
    return defaults


def get_api_key(provider, explicit_key=None):
    if explicit_key:
        return explicit_key
    defaults = provider_defaults(provider)
    for env_name in defaults["api_key_env"]:
        value = os.getenv(env_name)
        if value:
            return value
    return None


def compact_report(report, max_shots=5, shot_events=None):
    shots = []
    source_events = report.get("shot_events", []) if shot_events is None else shot_events
    for event in source_events[:max_shots]:
        shots.append(
            {
                "index": event.get("index"),
                "time_sec": event.get("time_sec"),
                "action": event.get("shot_action"),
                "confidence": event.get("shot_confidence"),
                "quality_score": event.get("quality_score"),
                "quality_level": event.get("quality_level"),
                "issues": event.get("quality_issues", []),
                "advice": event.get("quality_advice", []),
            }
        )

    return {
        "predicted_action": report.get("predicted_action"),
        "confidence": report.get("confidence"),
        "motion_summary": report.get("motion_summary", {}),
        "footwork_scores": report.get("footwork_scores", {}),
        "coach_report": report.get("coach_report", {}),
        "shot_count_total": len(report.get("shot_events", [])),
        "shots": shots,
        "runtime": report.get("runtime", {}),
    }


def build_prompt(report, max_shots=5):
    data = compact_report(report, max_shots=max_shots)
    return (
        "你是一名专业但友好的羽毛球训练教练。"
        "请只根据下面的结构化分析结果生成训练反馈，不要虚构视频中不存在的信息。"
        "请用中文输出，结构包括：\n"
        "1. 本次训练概览\n"
        "2. 逐拍重点观察\n"
        "3. 主要问题归纳\n"
        "4. 下一次训练计划\n"
        "5. 拍摄/系统使用建议\n\n"
        "要求：建议具体、可执行，适合业余羽毛球爱好者；如果置信度低，请明确提醒需要人工复核。\n\n"
        f"结构化结果：\n{json.dumps(data, ensure_ascii=False, indent=2)}"
    )


def build_segment_prompt(report, shot_events, segment_index, total_segments):
    data = compact_report(report, max_shots=len(shot_events), shot_events=shot_events)
    shot_range = ""
    if shot_events:
        shot_range = f"{shot_events[0].get('index')}-{shot_events[-1].get('index')}"
    return (
        "你是一名羽毛球智能训练教练。下面是全程训练中的一个分段，请只根据结构化数据做小结。\n"
        f"当前分段：第 {segment_index}/{total_segments} 组，拍次范围：{shot_range}。\n"
        "请用中文输出，控制在 300 字以内，包含：\n"
        "1. 本组主要动作和稳定性\n"
        "2. 重复出现的问题\n"
        "3. 下一组或下一轮训练最应该注意的一点\n\n"
        f"结构化结果：\n{json.dumps(data, ensure_ascii=False, indent=2)}"
    )


def build_final_prompt(report, segments):
    compact = compact_report(report, max_shots=0)
    segment_text = [
        {
            "range": item.get("range"),
            "shot_count": item.get("shot_count"),
            "summary": item.get("content"),
        }
        for item in segments
    ]
    data = {
        "overall": compact,
        "segment_summaries": segment_text,
    }
    return (
        "你是一名专业但友好的羽毛球训练教练。下面给出本地视觉模型的全程统计，以及按拍次分组得到的大模型小结。\n"
        "请生成一份完整训练报告。不要编造视频中不存在的信息；如果模型置信度低或问题来自算法推断，请明确提示需要人工复核。\n"
        "请用中文输出，结构包含：\n"
        "1. 本次训练总体概览\n"
        "2. 全程趋势和高频问题\n"
        "3. 逐拍/分段复盘重点\n"
        "4. 下一轮训练计划，给出 3-5 个具体动作或练习\n"
        "5. 拍摄和系统使用建议\n\n"
        f"结构化结果：\n{json.dumps(data, ensure_ascii=False, indent=2)}"
    )


def chunk_shots(shot_events, shots_per_group=8, max_groups=None):
    shots_per_group = max(1, int(shots_per_group or 8))
    chunks = [
        shot_events[start : start + shots_per_group]
        for start in range(0, len(shot_events), shots_per_group)
    ]
    if max_groups:
        chunks = chunks[: int(max_groups)]
    return chunks


def chat_completions(base_url, api_key, model, messages, timeout=60):
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.4,
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"LLM API HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"LLM API request failed: {exc.reason}") from exc

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected LLM API response: {data}") from exc


def chat_completions_stream(base_url, api_key, model, messages, timeout=90):
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.35,
        "stream": True,
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="ignore").strip()
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                content = delta.get("content") or ""
                if content:
                    yield content
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"LLM API HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"LLM API request failed: {exc.reason}") from exc


def generate_llm_coach_report(
    report,
    provider="qwen",
    api_key=None,
    base_url=None,
    model=None,
    timeout=120,
    max_shots=5,
):
    defaults = provider_defaults(provider)
    resolved_key = get_api_key(provider, api_key)
    if not resolved_key:
        env_names = " 或 ".join(defaults["api_key_env"])
        raise RuntimeError(f"未配置 API Key，请在页面输入或设置环境变量：{env_names}")

    resolved_base_url = base_url or defaults["base_url"]
    resolved_model = model or defaults["model"]
    messages = [
        {
            "role": "system",
            "content": "你是羽毛球智能训练助手，只基于结构化分析结果生成安全、可执行的训练建议。",
        },
        {
            "role": "user",
            "content": build_prompt(report, max_shots=max_shots),
        },
    ]
    return chat_completions(
        resolved_base_url,
        resolved_key,
        resolved_model,
        messages,
        timeout=timeout,
    )


def generate_segmented_llm_coach_report(
    report,
    provider="qwen",
    api_key=None,
    base_url=None,
    model=None,
    timeout=120,
    shots_per_group=8,
    max_groups=None,
):
    defaults = provider_defaults(provider)
    resolved_key = get_api_key(provider, api_key)
    if not resolved_key:
        env_names = " 或 ".join(defaults["api_key_env"])
        raise RuntimeError(f"未配置 API Key，请在页面输入或设置环境变量：{env_names}")

    resolved_base_url = base_url or defaults["base_url"]
    resolved_model = model or defaults["model"]
    shot_events = report.get("shot_events", [])
    chunks = chunk_shots(shot_events, shots_per_group=shots_per_group, max_groups=max_groups)
    if not chunks:
        summary = generate_llm_coach_report(
            report,
            provider=provider,
            api_key=resolved_key,
            base_url=resolved_base_url,
            model=resolved_model,
            timeout=timeout,
            max_shots=0,
        )
        return {
            "mode": "segmented",
            "summary": summary,
            "segments": [],
        }

    segments = []
    total_segments = len(chunks)
    for idx, chunk in enumerate(chunks, start=1):
        first_index = chunk[0].get("index") if chunk else None
        last_index = chunk[-1].get("index") if chunk else None
        messages = [
            {
                "role": "system",
                "content": "你是羽毛球智能训练助手，只基于结构化分析结果生成安全、可执行的训练建议。",
            },
            {
                "role": "user",
                "content": build_segment_prompt(report, chunk, idx, total_segments),
            },
        ]
        content = chat_completions(
            resolved_base_url,
            resolved_key,
            resolved_model,
            messages,
            timeout=timeout,
        )
        segments.append(
            {
                "index": idx,
                "range": f"{first_index}-{last_index}",
                "shot_count": len(chunk),
                "content": content,
            }
        )

    final_messages = [
        {
            "role": "system",
            "content": "你是羽毛球智能训练助手，负责把分段复盘整合成一份完整训练报告。",
        },
        {
            "role": "user",
            "content": build_final_prompt(report, segments),
        },
    ]
    summary = chat_completions(
        resolved_base_url,
        resolved_key,
        resolved_model,
        final_messages,
        timeout=timeout,
    )
    return {
        "mode": "segmented",
        "summary": summary,
        "segments": segments,
    }
