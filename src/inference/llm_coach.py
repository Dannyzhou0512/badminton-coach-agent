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


LANG_CONFIG = {
    "zh": {
        "name": "中文",
        "system_role": "你是一名专业但友好的羽毛球训练教练。请只根据结构化分析结果生成训练反馈，不要虚构视频中不存在的信息。",
        "system_role_segment": "你是羽毛球智能训练助手，只基于结构化分析结果生成安全、可执行的训练建议。",
        "system_role_final": "你是一名专业但友好的羽毛球训练教练，负责把分段复盘整合成一份完整训练报告。",
        "main_prompt": (
            "请用中文输出，结构包括：\n"
            "1. 本次训练概览\n"
            "2. 逐拍重点观察\n"
            "3. 主要问题归纳\n"
            "4. 下一次训练计划\n"
            "5. 拍摄/系统使用建议\n\n"
            "要求：建议具体、可执行，适合业余羽毛球爱好者；如果置信度低，请明确提醒需要人工复核。"
        ),
        "segment_prompt": (
            "请用中文输出，控制在 300 字以内，包含：\n"
            "1. 本组主要动作和稳定性\n"
            "2. 重复出现的问题\n"
            "3. 下一组或下一轮训练最应该注意的一点"
        ),
        "segment_header": "下面是全程训练中的一个分段，请只根据结构化数据做小结。",
        "segment_range": "当前分段：第 {idx}/{total} 组，拍次范围：{rng}。",
        "final_prompt": (
            "请用中文输出，结构包含：\n"
            "1. 本次训练总体概览\n"
            "2. 全程趋势和高频问题\n"
            "3. 逐拍/分段复盘重点\n"
            "4. 下一轮训练计划，给出 3-5 个具体动作或练习\n"
            "5. 拍摄和系统使用建议\n\n"
            "要求：不要编造视频中不存在的信息；如果模型置信度低或问题来自算法推断，请明确提示需要人工复核。"
        ),
        "final_intro": "下面给出本地视觉模型的全程统计，以及按拍次分组得到的大模型小结。",
        "struct_header": "结构化结果：",
        "api_key_err": "未配置 API Key，请在页面输入或设置环境变量：{envs}",
    },
    "en": {
        "name": "English",
        "system_role": "You are a professional yet friendly badminton coach. Generate training feedback based ONLY on the structured analysis below. Do not fabricate information not present in the video.",
        "system_role_segment": "You are an intelligent badminton training assistant. Generate safe, actionable training advice based solely on the structured analysis.",
        "system_role_final": "You are a professional badminton coach. Integrate segment summaries into one complete training report.",
        "main_prompt": (
            "Please respond in English with this structure:\n"
            "1. Session Overview\n"
            "2. Key Shot Observations\n"
            "3. Main Issues Identified\n"
            "4. Next Training Plan\n"
            "5. Filming / System Tips\n\n"
            "Requirements: Advice must be concrete and actionable, suitable for amateur players; if confidence is low, explicitly note that manual review is recommended."
        ),
        "segment_prompt": (
            "Please respond in English within 300 words, including:\n"
            "1. Main strokes and stability in this segment\n"
            "2. Recurring issues\n"
            "3. One key point to focus on for the next set"
        ),
        "segment_header": "Below is one segment from the full session. Summarize only based on the structured data.",
        "segment_range": "Segment: {idx}/{total}, shot range: {rng}.",
        "final_prompt": (
            "Please respond in English with this structure:\n"
            "1. Overall Session Summary\n"
            "2. Trends and recurring issues\n"
            "3. Key takeaways per segment\n"
            "4. Next training plan: 3-5 specific drills\n"
            "5. Filming and usage tips\n\n"
            "Requirements: Do not fabricate information; if model confidence is low or issues are algorithm-inferred, note that manual review is recommended."
        ),
        "final_intro": "Below are the full-session statistics from the local vision model, plus segment-level summaries.",
        "struct_header": "Structured data:",
        "api_key_err": "API Key not configured. Please enter it on the page or set environment variable: {envs}",
    },
    "ja": {
        "name": "日本語",
        "system_role": "あなたはプロフェッショナルでフレンドリーなバドミントンコーチです。以下の構造化分析結果のみに基づいてトレーニングフィードバックを生成してください。動画に存在しない情報を捏造しないでください。",
        "system_role_segment": "あなたはバドミントンAIトレーニングアシスタントです。構造化分析結果に基づき、安全で実行可能なアドバイスを生成してください。",
        "system_role_final": "あなたはバドミントンコーチです。各セグメントの要約を統合して完全なトレーニングレポートを作成してください。",
        "main_prompt": (
            "日本語で以下の構成で出力してください：\n"
            "1. 今回の練習概要\n"
            "2. ショット別の観察ポイント\n"
            "3. 主な問題点\n"
            "4. 次回のトレーニング計画\n"
            "5. 撮影・システム利用のアドバイス\n\n"
            "要件：アドバイスは具体的で実行可能なものにし、アマチュアプレイヤー向けにしてください。信頼度が低い場合は、目視での確認を推奨する旨を明記してください。"
        ),
        "segment_prompt": (
            "日本語で300文字以内で出力してください：\n"
            "1. このセグメントの主なショットと安定性\n"
            "2. 繰り返し見られる問題\n"
            "3. 次のセットで最も注意すべき1点"
        ),
        "segment_header": "以下はセッション全体の1セグメントです。構造化データに基づいて要約してください。",
        "segment_range": "セグメント：{idx}/{total}、ショット範囲：{rng}。",
        "final_prompt": (
            "日本語で以下の構成で出力してください：\n"
            "1. 練習全体の概要\n"
            "2. 全体の傾向と頻出問題\n"
            "3. セグメント別の重要ポイント\n"
            "4. 次回トレーニング計画（具体的なドリル3-5個）\n"
            "5. 撮影とシステム利用のヒント\n\n"
            "要件：動画にない情報を捏造しないでください。信頼度が低い場合は目視確認を推奨してください。"
        ),
        "final_intro": "以下はローカルビジョンモデルによる全セッション統計と、ショット別セグメント要約です。",
        "struct_header": "構造化データ：",
        "api_key_err": "API Keyが設定されていません。ページで入力するか環境変数を設定してください：{envs}",
    },
    "ko": {
        "name": "한국어",
        "system_role": "당신은 전문적이고 친절한 배드민턴 코치입니다. 아래 구조화된 분석 결과만을 바탕으로 훈련 피드백을 생성하며, 영상에 없는 정보를 지어내지 마세요.",
        "system_role_segment": "당신은 배드민턴 AI 훈련 어시스턴트입니다. 구조화된 분석 결과에 기반해 안전하고 실행 가능한 훈련 조언을 생성하세요.",
        "system_role_final": "당신은 배드민턴 코치입니다. 구간별 요약을 통합하여 완전한 훈련 리포트를 작성하세요.",
        "main_prompt": (
            "한국어로 다음 구조로 출력하세요:\n"
            "1. 이번 훈련 개요\n"
            "2. 샷별 주요 관찰 사항\n"
            "3. 주요 문제점\n"
            "4. 다음 훈련 계획\n"
            "5. 촬영/시스템 사용 팁\n\n"
            "요구사항: 조언은 구체적이고 실행 가능해야 하며 아마추어 선수에게 적합해야 합니다. 신뢰도가 낮으면 수동 확인을 권장한다고 명시하세요."
        ),
        "segment_prompt": (
            "한국어로 300자 이내로 출력하세요:\n"
            "1. 이 구간의 주요 샷과 안정성\n"
            "2. 반복적으로 나타나는 문제\n"
            "3. 다음 세트에서 가장 주의해야 할 한 가지"
        ),
        "segment_header": "아래는 전체 세션의 한 구간입니다. 구조화된 데이터만 바탕으로 요약하세요.",
        "segment_range": "구간: {idx}/{total}, 샷 범위: {rng}.",
        "final_prompt": (
            "한국어로 다음 구조로 출력하세요:\n"
            "1. 전체 세션 요약\n"
            "2. 전반적인 경향과 반복 문제\n"
            "3. 구간별 핵심 내용\n"
            "4. 다음 훈련 계획(구체적 드릴 3-5개)\n"
            "5. 촬영 및 사용 팁\n\n"
            "요구사항: 영상에 없는 정보를 만들어내지 마세요. 신뢰도가 낮으면 수동 확인을 권장하세요."
        ),
        "final_intro": "아래는 로컬 비전 모델의 전체 세션 통계와 샷별 구간 요약입니다.",
        "struct_header": "구조화된 데이터:",
        "api_key_err": "API Key가 구성되지 않았습니다. 페이지에서 입력하거나 환경변수를 설정하세요: {envs}",
    },
    "id": {
        "name": "Bahasa Indonesia",
        "system_role": "Anda adalah pelatih bulu tangkis profesional yang ramah. Hasilkan umpan balik latihan HANYA berdasarkan analisis terstruktur di bawah. Jangan mengarang informasi yang tidak ada dalam video.",
        "system_role_segment": "Anda adalah asisten latihan bulu tangkis AI. Hasilkan saran latihan yang aman dan dapat dijalankan hanya berdasarkan analisis terstruktur.",
        "system_role_final": "Anda adalah pelatih bulu tangkis profesional. Gabungkan ringkasan segmen menjadi satu laporan latihan lengkap.",
        "main_prompt": (
            "Harap jawab dalam Bahasa Indonesia dengan struktur:\n"
            "1. Ringkasan Sesi\n"
            "2. Pengamatan Pukulan Kunci\n"
            "3. Masalah Utama\n"
            "4. Rencana Latihan Berikutnya\n"
            "5. Tips Pengambilan Video / Sistem\n\n"
            "Saran harus konkret dan dapat dijalankan, cocok untuk pemain amatir; jika kepercayaan model rendah, sarankan peninjauan manual."
        ),
        "segment_prompt": (
            "Jawab dalam Bahasa Indonesia dalam 300 kata:\n"
            "1. Pukulan utama dan stabilitas di segmen ini\n"
            "2. Masalah yang berulang\n"
            "3. Satu poin kunci untuk set berikutnya"
        ),
        "segment_header": "Berikut adalah satu segmen dari sesi latihan. Ringkas hanya berdasarkan data terstruktur.",
        "segment_range": "Segmen: {idx}/{total}, rentang pukulan: {rng}.",
        "final_prompt": (
            "Jawab dalam Bahasa Indonesia dengan struktur:\n"
            "1. Ringkasan Sesi Keseluruhan\n"
            "2. Tren dan masalah berulang\n"
            "3. Poin kunci per segmen\n"
            "4. Rencana latihan berikutnya: 3-5 latihan spesifik\n"
            "5. Tips pengambilan video dan penggunaan\n\n"
            "Jangan mengarang informasi; jika kepercayaan rendah, sarankan peninjauan manual."
        ),
        "final_intro": "Berikut adalah statistik sesi penuh dari model visi lokal dan ringkasan segmen per pukulan.",
        "struct_header": "Data terstruktur:",
        "api_key_err": "API Key belum dikonfigurasi. Silakan masukkan di halaman atau atur environment variable: {envs}",
    },
}


def _lc(lang):
    return LANG_CONFIG.get(lang, LANG_CONFIG["zh"])


def build_prompt(report, max_shots=5, language="zh"):
    cfg = _lc(language)
    data = compact_report(report, max_shots=max_shots)
    return (
        cfg["system_role"]
        + cfg["main_prompt"]
        + "\n\n"
        + cfg["struct_header"]
        + "\n"
        + json.dumps(data, ensure_ascii=False, indent=2)
    )


def build_segment_prompt(report, shot_events, segment_index, total_segments, language="zh"):
    cfg = _lc(language)
    data = compact_report(report, max_shots=len(shot_events), shot_events=shot_events)
    shot_range = ""
    if shot_events:
        shot_range = f"{shot_events[0].get('index')}-{shot_events[-1].get('index')}"
    header = cfg["segment_header"]
    rng_line = cfg["segment_range"].format(idx=segment_index, total=total_segments, rng=shot_range) if shot_range else ""
    return (
        header + "\n"
        + rng_line + "\n"
        + cfg["segment_prompt"]
        + "\n\n"
        + cfg["struct_header"]
        + "\n"
        + json.dumps(data, ensure_ascii=False, indent=2)
    )


def build_final_prompt(report, segments, language="zh"):
    cfg = _lc(language)
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
        cfg["system_role_final"]
        + cfg["final_intro"]
        + "\n"
        + cfg["final_prompt"]
        + "\n\n"
        + cfg["struct_header"]
        + "\n"
        + json.dumps(data, ensure_ascii=False, indent=2)
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
    language="zh",
):
    defaults = provider_defaults(provider)
    resolved_key = get_api_key(provider, api_key)
    cfg = _lc(language)
    if not resolved_key:
        env_names = " 或 ".join(defaults["api_key_env"])
        raise RuntimeError(cfg["api_key_err"].format(envs=env_names))

    resolved_base_url = base_url or defaults["base_url"]
    resolved_model = model or defaults["model"]
    messages = [
        {
            "role": "system",
            "content": cfg["system_role_segment"],
        },
        {
            "role": "user",
            "content": build_prompt(report, max_shots=max_shots, language=language),
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
    language="zh",
):
    defaults = provider_defaults(provider)
    resolved_key = get_api_key(provider, api_key)
    cfg = _lc(language)
    if not resolved_key:
        env_names = " 或 ".join(defaults["api_key_env"])
        raise RuntimeError(cfg["api_key_err"].format(envs=env_names))

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
            language=language,
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
                "content": cfg["system_role_segment"],
            },
            {
                "role": "user",
                "content": build_segment_prompt(report, chunk, idx, total_segments, language=language),
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
            "content": cfg["system_role_final"],
        },
        {
            "role": "user",
            "content": build_final_prompt(report, segments, language=language),
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
