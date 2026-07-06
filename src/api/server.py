"""
FastAPI backend for the standalone HTML frontend.

Run:
  python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000
"""

import hashlib
import json
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
import torch
from fastapi import Body, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles


ROOT = Path(__file__).resolve().parents[2]
INFERENCE_DIR = ROOT / "src" / "inference"
if str(INFERENCE_DIR) not in sys.path:
    sys.path.insert(0, str(INFERENCE_DIR))

from predict_video import (  # noqa: E402
    build_coach_report,
    build_report,
    classify_hit_events,
    compute_footwork_scores,
    compute_motion_summary,
    detect_hit_events,
    extract_pose_and_frames_from_video,
    filter_footwork_jumps,
    footwork_centers,
    load_model,
    predict_windows,
    topk_from_probs,
    write_full_length_annotated_video,
    write_shot_clips,
)
from llm_coach import (  # noqa: E402
    chat_completions,
    chat_completions_stream,
    generate_segmented_llm_coach_report,
    get_api_key,
    provider_defaults,
)


UPLOAD_DIR = ROOT / "outputs" / "api_uploads"
ANNOTATED_DIR = ROOT / "outputs" / "api_annotated"
SHOT_CLIP_DIR = ROOT / "outputs" / "api_shot_clips"
PREVIEW_DIR = ROOT / "outputs" / "api_previews"
DEFAULT_CHECKPOINT = ROOT / "models" / "pose_sequence_tcn_gru.pt"
DEFAULT_POSE_MODEL = ROOT / "yolov8s-pose.pt"


app = FastAPI(title="Badminton Coach Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def disable_frontend_cache(request, call_next):
    if request.url.path.startswith("/frontend"):
        request.scope["headers"] = [
            (key, value)
            for key, value in request.scope.get("headers", [])
            if key.lower() not in {b"if-none-match", b"if-modified-since"}
        ]
    response = await call_next(request)
    if request.url.path.startswith("/frontend"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


app.mount("/frontend", StaticFiles(directory=str(ROOT / "frontend"), html=True), name="frontend")
app.mount("/outputs", StaticFiles(directory=str(ROOT / "outputs")), name="outputs")


def digest_bytes(data):
    return hashlib.sha1(data).hexdigest()[:12]


def save_upload(upload: UploadFile):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    data = upload.file.read()
    suffix = Path(upload.filename or "video.mp4").suffix.lower() or ".mp4"
    stem = Path(upload.filename or "video").stem
    output_path = UPLOAD_DIR / f"{stem}_{digest_bytes(data)}{suffix}"
    output_path.write_bytes(data)
    return output_path


@lru_cache(maxsize=4)
def cached_model(checkpoint_path, use_cpu):
    device = torch.device("cuda" if torch.cuda.is_available() and not use_cpu else "cpu")
    model, checkpoint, label_names = load_model(checkpoint_path, device)
    return model, checkpoint, label_names, str(device)


@lru_cache(maxsize=8)
def cached_pose_result(
    video_path,
    pose_model_path,
    conf_threshold,
    max_frames,
    batch_size,
    target_player,
    target_roi,
    target_bbox,
):
    pose_seq, _, sampled_indices, video_fps = extract_pose_and_frames_from_video(
        video_path,
        pose_model_path,
        conf_threshold=conf_threshold,
        max_frames=max_frames,
        batch_size=batch_size,
        target_player=target_player,
        target_point=None,
        target_roi=target_roi,
        target_bbox=target_bbox,
    )
    return pose_seq, tuple(sampled_indices), float(video_fps)


def clean_class_name(raw_name):
    return raw_name.split("_", 1)[1] if "_" in raw_name else raw_name


def effective_pose_fps(sampled_indices, video_fps):
    if sampled_indices is None or len(sampled_indices) < 2:
        return float(video_fps or 30.0)
    import numpy as np

    frame_steps = np.diff(np.asarray(sampled_indices, dtype=np.float32))
    mean_step = float(np.mean(frame_steps[frame_steps > 0])) if np.any(frame_steps > 0) else 1.0
    return float(video_fps or 30.0) / max(mean_step, 1.0)


def parse_config(raw_config):
    if not raw_config:
        return {}
    try:
        return json.loads(raw_config)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid config JSON: {exc}") from exc


def config_roi(value):
    presets = {
        "full": None,
        "top": (0.0, 0.0, 1.0, 0.55),
        "bottom": (0.0, 0.45, 1.0, 1.0),
        "left": (0.0, 0.0, 0.55, 1.0),
        "right": (0.45, 0.0, 1.0, 1.0),
    }
    if isinstance(value, (list, tuple)) and len(value) == 4:
        return tuple(float(item) for item in value)
    return presets.get(value or "full")


def preset_values(name):
    presets = {
        "adaptive": {"max_frames": None, "window_size": 32, "stride": 8},
        "fast": {"max_frames": 300, "window_size": 64, "stride": 32},
        "balanced": {"max_frames": 600, "window_size": 32, "stride": 16},
        "full": {"max_frames": None, "window_size": 24, "stride": 4},
    }
    return presets.get(name or "adaptive", presets["adaptive"])


def aggregate_predictions(windows, aggregate_probs, topk, num_classes):
    if not windows:
        return topk_from_probs(aggregate_probs, topk=topk) if aggregate_probs is not None else []
    best_window = max(windows, key=lambda item: item["top_predictions"][0][1])
    return best_window["top_predictions"][:topk]


def to_public_url(path):
    if not path:
        return None
    relative = Path(path).resolve().relative_to(ROOT.resolve()).as_posix()
    return "/" + relative


def to_media_url(path):
    if not path:
        return None
    media_path = Path(path).resolve()
    media_path.relative_to(ANNOTATED_DIR.resolve())
    return f"/api/media/{media_path.name}"


def _check_browser_playable(video_path):
    """Return a warning string if the video is not encoded with H.264."""
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return "标注视频无法打开，请下载到本地查看。"
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        cap.release()
        h264_codes = {
            cv2.VideoWriter_fourcc(*"avc1"),
            cv2.VideoWriter_fourcc(*"H264"),
            cv2.VideoWriter_fourcc(*"h264"),
            cv2.VideoWriter_fourcc(*"X264"),
        }
        if fourcc not in h264_codes:
            codec_chars = "".join(chr((fourcc >> 8 * i) & 0xFF) for i in range(4))
            return (
                f"当前环境缺少 ffmpeg/OpenH264，标注视频使用 {codec_chars!r} 编码，"
                "浏览器可能无法直接播放。请下载后用本地播放器查看，"
                "或安装 ffmpeg 并加入系统 PATH 后重新分析。"
            )
    except Exception:
        pass
    return None


def iter_file_range(path, start, end, chunk_size=1024 * 1024):
    with Path(path).open("rb") as file:
        file.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            chunk = file.read(min(chunk_size, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


def extract_video_preview(video_path, output_path, time_sec=1.0):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = total_frames / fps if fps > 0 and total_frames > 0 else 0.0
    target_time = min(max(float(time_sec or 0.0), 0.0), max(duration - 0.1, 0.0)) if duration else 0.0
    cap.set(cv2.CAP_PROP_POS_MSEC, target_time * 1000.0)
    ok, frame = cap.read()

    if (not ok or frame is None) and total_frames > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(total_frames - 1, max(0, int(total_frames * 0.25))))
        ok, frame = cap.read()
    cap.release()

    if not ok or frame is None:
        return None
    if not cv2.imwrite(str(output_path), frame):
        return None
    return output_path


def read_video_metadata(video_path):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {}
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    return {
        "fps": fps,
        "frames": frames,
        "duration_sec": frames / fps if fps > 0 and frames > 0 else None,
        "width": width,
        "height": height,
    }


def build_footwork_trace(pose_seq, sampled_indices=None, frame_size=None, conf_threshold=0.3, max_points=180):
    centers = filter_footwork_jumps(footwork_centers(pose_seq, conf_threshold=conf_threshold))
    valid = [(idx, center) for idx, center in enumerate(centers) if center is not None]
    if len(valid) < 2:
        return []

    points = np.asarray([center for _, center in valid], dtype=np.float32)
    if frame_size and frame_size.get("width") and frame_size.get("height"):
        scale = np.asarray([max(float(frame_size["width"]), 1.0), max(float(frame_size["height"]), 1.0)], dtype=np.float32)
        normalized_points = np.clip(points / scale, 0.0, 1.0)
    else:
        mins = np.min(points, axis=0)
        maxs = np.max(points, axis=0)
        normalized_points = np.clip((points - mins) / np.maximum(maxs - mins, 1.0), 0.0, 1.0)

    filtered = []
    filtered_indices = []
    previous = None
    for (idx, _), point in zip(valid, normalized_points):
        if previous is not None and float(np.linalg.norm(point - previous)) > 0.18:
            continue
        filtered.append(point)
        filtered_indices.append(idx)
        previous = point

    if len(filtered) < 2:
        return []

    smoothed = np.asarray(filtered, dtype=np.float32)
    if len(smoothed) >= 5:
        smooth_copy = smoothed.copy()
        for i in range(2, len(smoothed) - 2):
            smooth_copy[i] = np.mean(smoothed[i - 2 : i + 3], axis=0)
        smoothed = smooth_copy

    step = max(1, int(np.ceil(len(smoothed) / max_points)))
    sampled_lookup = list(sampled_indices) if sampled_indices is not None else None

    trace = []
    for idx, norm in zip(filtered_indices[::step], smoothed[::step]):
        frame = int(sampled_lookup[idx]) if sampled_lookup and idx < len(sampled_lookup) else int(idx)
        trace.append(
            {
                "frame": frame,
                "pose_index": int(idx),
                "x": round(float(norm[0]), 4),
                "y": round(float(norm[1]), 4),
            }
        )
    return trace


def format_frontend_report(report):
    shot_events = report.get("shot_events", [])
    low_confidence_shots = [
        event for event in shot_events if float(event.get("shot_confidence") or event.get("confidence") or 1.0) < 0.45
    ]
    quality_scores = [
        float(event.get("quality_score"))
        for event in shot_events
        if event.get("quality_score") is not None
    ]
    raw_footwork = report.get("footwork_scores", {}) or {}
    footwork_values = [
        float(raw_footwork.get(key, 0.0))
        for key in ("movement", "explosiveness", "coordination", "stability", "recovery", "coverage", "balance")
        if raw_footwork.get(key) is not None
    ]
    avg_quality = float(np.mean(quality_scores)) if quality_scores else None
    avg_footwork = float(np.mean(footwork_values)) if footwork_values else None
    if avg_quality is not None and avg_footwork is not None:
        overall_score = avg_quality * 0.7 + avg_footwork * 0.3
    elif avg_quality is not None:
        overall_score = avg_quality
    elif avg_footwork is not None:
        overall_score = avg_footwork
    else:
        overall_score = float(report.get("confidence") or 0.0) * 100.0
    return {
        "predicted_action": report.get("predicted_action"),
        "confidence": report.get("confidence"),
        "detection_rate": report.get("motion_summary", {}).get("detection_rate"),
        "hit_count": len(report.get("hit_events", [])),
        "low_confidence_shots": len(low_confidence_shots),
        "quality_summary": {
            "overall_score": round(float(overall_score), 1),
            "avg_quality_score": round(float(avg_quality), 1) if avg_quality is not None else None,
            "min_quality_score": round(float(np.min(quality_scores)), 1) if quality_scores else None,
            "max_quality_score": round(float(np.max(quality_scores)), 1) if quality_scores else None,
            "avg_footwork_score": round(float(avg_footwork), 1) if avg_footwork is not None else None,
            "shot_count": len(quality_scores),
        },
        "top_predictions": [
            [item["class_name"], item["confidence"]]
            for item in report.get("top_predictions", [])
        ],
        "footwork_scores": {
            "移动量": report.get("footwork_scores", {}).get("movement", 0.0),
            "启动爆发": report.get("footwork_scores", {}).get("explosiveness", 0.0),
            "身体协调": report.get("footwork_scores", {}).get("coordination", 0.0),
            "重心稳定": report.get("footwork_scores", {}).get("stability", 0.0),
            "回位能力": report.get("footwork_scores", {}).get("recovery", 0.0),
            "覆盖范围": report.get("footwork_scores", {}).get("coverage", 0.0),
            "步幅平衡": report.get("footwork_scores", {}).get("balance", 0.0),
            "movement": report.get("footwork_scores", {}).get("movement", 0.0),
            "explosiveness": report.get("footwork_scores", {}).get("explosiveness", 0.0),
            "coordination": report.get("footwork_scores", {}).get("coordination", 0.0),
            "stability": report.get("footwork_scores", {}).get("stability", 0.0),
            "recovery": report.get("footwork_scores", {}).get("recovery", 0.0),
            "coverage": report.get("footwork_scores", {}).get("coverage", 0.0),
            "balance": report.get("footwork_scores", {}).get("balance", 0.0),
        },
        "coach_report": report.get("coach_report", {}),
        "llm_coach_report": report.get("llm_coach_report"),
        "llm_coach_segments": report.get("llm_coach_segments", []),
        "llm_coach_error": report.get("llm_coach_error"),
        "llm_provider": report.get("llm_provider"),
        "shot_events": shot_events,
        "footwork_trace": report.get("footwork_trace", []),
        "video_metadata": report.get("video_metadata", {}),
        "annotated_video_url": to_media_url(report.get("annotated_video")),
        "tracking_video_url": to_media_url(report.get("tracking_video")),
        "annotated_preview_url": to_public_url(report.get("annotated_preview")),
        "video_warning": report.get("video_warning"),
        "report": report,
    }


def compact_chat_report(report):
    if not isinstance(report, dict):
        return {}
    shot_events = report.get("shot_events") or report.get("report", {}).get("shot_events") or []
    return {
        "predicted_action": report.get("predicted_action"),
        "confidence": report.get("confidence"),
        "hit_count": report.get("hit_count"),
        "video_metadata": report.get("video_metadata", {}),
        "footwork_scores": report.get("footwork_scores", {}),
        "coach_report": report.get("coach_report", {}),
        "shot_events_sample": shot_events[:12],
        "llm_coach_report": report.get("llm_coach_report"),
    }


def build_coach_chat_messages(question, history=None, report=None):
    history = history or []
    context = compact_chat_report(report)
    system = (
        "你是“羽动智练”的羽毛球 AI 教练。回答要专业、具体、可执行，"
        "优先围绕羽毛球技术、步伐、训练计划、比赛复盘、运动恢复和安全建议。"
        "如果用户问到伤病、疼痛或医学问题，只给一般运动安全建议，并提醒必要时咨询医生或康复师。"
        "如果提供了训练分析上下文，只能基于这些数据做推断，不要编造视频中不存在的细节。"
        "回答不要使用 Markdown 标题、星号加粗、井号、代码块或项目符号占位符；"
        "请用自然中文短段落输出，必要时用“一、二、三”编号。"
    )
    messages = [{"role": "system", "content": system}]
    if context:
        messages.append(
            {
                "role": "system",
                "content": "本次训练分析上下文如下：\n"
                + json.dumps(context, ensure_ascii=False, indent=2),
            }
        )
    for item in history[-8:]:
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content[:1600]})
    messages.append({"role": "user", "content": str(question).strip()})
    return messages


def sse_payload(event, data):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/")
def index():
    return RedirectResponse(url="/frontend/")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "checkpoint": str(DEFAULT_CHECKPOINT),
        "pose_model": str(DEFAULT_POSE_MODEL),
    }


@app.post("/api/coach/chat")
def coach_chat(payload: dict = Body(...)):
    question = str(payload.get("question", "")).strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    provider = str(payload.get("provider") or "qwen").strip().lower()
    if provider not in {"qwen", "zhipu"}:
        provider = "qwen"

    defaults = provider_defaults(provider)
    api_key = get_api_key(provider)
    if not api_key:
        env_names = " / ".join(defaults["api_key_env"])
        raise HTTPException(status_code=400, detail=f"Missing API key: {env_names}")

    messages = build_coach_chat_messages(
        question,
        history=payload.get("history") or [],
        report=payload.get("report") if payload.get("use_report_context", True) else None,
    )
    try:
        answer = chat_completions(
            defaults["base_url"],
            api_key,
            defaults["model"],
            messages,
            timeout=int(payload.get("timeout") or 90),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "provider": provider,
        "model": defaults["model"],
        "answer": answer,
    }


@app.post("/api/coach/chat/stream")
def coach_chat_stream(payload: dict = Body(...)):
    question = str(payload.get("question", "")).strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    provider = str(payload.get("provider") or "qwen").strip().lower()
    if provider not in {"qwen", "zhipu"}:
        provider = "qwen"

    defaults = provider_defaults(provider)
    api_key = get_api_key(provider)
    if not api_key:
        env_names = " / ".join(defaults["api_key_env"])
        raise HTTPException(status_code=400, detail=f"Missing API key: {env_names}")

    messages = build_coach_chat_messages(
        question,
        history=payload.get("history") or [],
        report=payload.get("report") if payload.get("use_report_context", True) else None,
    )

    def stream():
        try:
            yield sse_payload("status", {"text": "正在理解你的问题"})
            yield sse_payload("status", {"text": "正在结合训练报告和羽毛球训练知识"})
            yield sse_payload("status", {"text": "正在组织可执行的训练建议"})
            for chunk in chat_completions_stream(
                defaults["base_url"],
                api_key,
                defaults["model"],
                messages,
                timeout=int(payload.get("timeout") or 90),
            ):
                yield sse_payload("delta", {"text": chunk})
            yield sse_payload("done", {"provider": provider, "model": defaults["model"]})
        except Exception as exc:
            yield sse_payload("error", {"message": str(exc)})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/media/{filename}")
def stream_annotated_media(filename: str, range: str | None = Header(default=None)):
    media_path = (ANNOTATED_DIR / filename).resolve()
    try:
        media_path.relative_to(ANNOTATED_DIR.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Invalid media path") from exc
    if not media_path.exists() or media_path.suffix.lower() != ".mp4":
        raise HTTPException(status_code=404, detail="Media not found")

    file_size = media_path.stat().st_size
    headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-store",
        "Content-Disposition": f'inline; filename="{media_path.name}"',
    }

    if range:
        try:
            range_value = range.strip().lower()
            if not range_value.startswith("bytes="):
                raise ValueError("Unsupported range unit")
            range_spec = range_value.replace("bytes=", "", 1).split(",", 1)[0]
            start_text, end_text = range_spec.split("-", 1)
            if start_text:
                start = int(start_text)
                end = int(end_text) if end_text else file_size - 1
            else:
                suffix_length = int(end_text)
                start = max(file_size - suffix_length, 0)
                end = file_size - 1
            start = max(0, min(start, file_size - 1))
            end = max(start, min(end, file_size - 1))
        except Exception as exc:
            raise HTTPException(status_code=416, detail="Invalid range") from exc

        headers.update(
            {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(end - start + 1),
            }
        )
        return StreamingResponse(
            iter_file_range(media_path, start, end),
            status_code=206,
            media_type="video/mp4",
            headers=headers,
        )

    headers["Content-Length"] = str(file_size)
    return StreamingResponse(
        iter_file_range(media_path, 0, file_size - 1),
        media_type="video/mp4",
        headers=headers,
    )


@app.head("/api/media/{filename}")
def head_annotated_media(filename: str):
    media_path = (ANNOTATED_DIR / filename).resolve()
    try:
        media_path.relative_to(ANNOTATED_DIR.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Invalid media path") from exc
    if not media_path.exists() or media_path.suffix.lower() != ".mp4":
        raise HTTPException(status_code=404, detail="Media not found")

    file_size = media_path.stat().st_size
    return Response(
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-store",
            "Content-Length": str(file_size),
            "Content-Disposition": f'inline; filename="{media_path.name}"',
        },
    )


@app.post("/api/frame")
def extract_video_frame(video: UploadFile = File(...), time_sec: float = Form(1.0)):
    try:
        video_path = save_upload(video)
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Video cannot be opened by OpenCV")

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = total_frames / fps if total_frames > 0 and fps > 0 else 0.0
        target_time = max(0.0, float(time_sec or 0.0))
        if duration > 0:
            target_time = min(target_time, max(duration - 0.05, 0.0))

        cap.set(cv2.CAP_PROP_POS_MSEC, target_time * 1000.0)
        ok, frame = cap.read()
        if not ok and total_frames > 0:
            frame_index = min(total_frames - 1, max(0, int(target_time * fps)))
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = cap.read()
        cap.release()

        if not ok or frame is None:
            raise HTTPException(status_code=422, detail="Frame cannot be extracted")

        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        if not ok:
            raise HTTPException(status_code=500, detail="Frame cannot be encoded")

        return Response(
            content=encoded.tobytes(),
            media_type="image/jpeg",
            headers={"X-Frame-Time": f"{target_time:.3f}"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/analyze")
def analyze_video(video: UploadFile = File(...), config: str = Form("{}")):
    cfg = parse_config(config)
    if not DEFAULT_CHECKPOINT.exists():
        raise HTTPException(status_code=500, detail=f"Classifier checkpoint not found: {DEFAULT_CHECKPOINT}")
    if not DEFAULT_POSE_MODEL.exists():
        raise HTTPException(status_code=500, detail=f"Pose model not found: {DEFAULT_POSE_MODEL}")

    try:
        video_path = save_upload(video)
        video_metadata = read_video_metadata(video_path)
        use_cpu = bool(cfg.get("use_cpu", False))
        model, checkpoint, label_names, device_name = cached_model(str(DEFAULT_CHECKPOINT), use_cpu)
        device = torch.device(device_name)

        preset = preset_values(cfg.get("analysis_preset"))
        target_player = cfg.get("target_player") or "near"
        target_bbox = cfg.get("target_bbox")
        if target_bbox is not None:
            target_bbox = tuple(float(item) for item in target_bbox)

        target_roi = config_roi(cfg.get("target_roi"))
        pose_seq, sampled_indices, video_fps = cached_pose_result(
            str(video_path.resolve()),
            str(DEFAULT_POSE_MODEL.resolve()),
            float(cfg.get("conf_threshold", 0.3)),
            preset["max_frames"],
            int(cfg.get("batch_size", 32)),
            target_player,
            target_roi,
            target_bbox,
        )

        windows, aggregate_probs = predict_windows(
            model,
            checkpoint,
            pose_seq,
            device,
            window_size=int(cfg.get("window_size", preset["window_size"])),
            stride=int(cfg.get("stride", preset["stride"])),
            topk=3,
        )
        top_predictions = aggregate_predictions(
            windows,
            aggregate_probs,
            topk=5,
            num_classes=int(checkpoint.get("num_classes", 18)),
        )
        summary = compute_motion_summary(pose_seq, conf_threshold=float(cfg.get("conf_threshold", 0.3)))
        report = build_report(video_path, top_predictions, label_names, summary)
        report["video_metadata"] = video_metadata
        analysis_fps = effective_pose_fps(sampled_indices, video_fps)
        report["hit_events"] = detect_hit_events(pose_seq, windows=windows, label_names=label_names, fps=analysis_fps)
        report["shot_events"] = classify_hit_events(
            model,
            checkpoint,
            pose_seq,
            report["hit_events"],
            label_names,
            device,
            fps=analysis_fps,
            topk=3,
        )
        for event in report["hit_events"]:
            event["time_sec"] = round(float(event.get("frame", 0)) / max(analysis_fps, 1e-6), 3)
        for event in report["shot_events"]:
            event["time_sec"] = round(float(event.get("frame", 0)) / max(analysis_fps, 1e-6), 3)
        report["footwork_scores"] = compute_footwork_scores(pose_seq)
        report["footwork_trace"] = build_footwork_trace(
            pose_seq,
            sampled_indices=sampled_indices,
            frame_size=video_metadata,
            conf_threshold=float(cfg.get("conf_threshold", 0.3)),
        )
        report["coach_report"] = build_coach_report(report)

        llm_provider = cfg.get("llm_provider") or "qwen"
        if bool(cfg.get("generate_llm_report", False)):
            try:
                llm_result = generate_segmented_llm_coach_report(
                    report,
                    provider=llm_provider,
                    timeout=int(cfg.get("llm_timeout", 120)),
                    shots_per_group=int(cfg.get("llm_shots_per_group", 8)),
                    max_groups=cfg.get("llm_max_groups"),
                )
                report["llm_provider"] = llm_provider
                report["llm_coach_mode"] = llm_result.get("mode", "segmented")
                report["llm_coach_report"] = llm_result.get("summary", "")
                report["llm_coach_segments"] = llm_result.get("segments", [])
            except Exception as exc:
                report["llm_provider"] = llm_provider
                report["llm_coach_error"] = str(exc)

        annotated_video = ANNOTATED_DIR / f"{video_path.stem}_annotated.mp4"
        status_text = f"Target: {target_player}"
        write_full_length_annotated_video(
            video_path,
            pose_seq,
            sampled_indices,
            windows,
            label_names,
            annotated_video,
            conf_threshold=float(cfg.get("conf_threshold", 0.3)),
            hit_events=report.get("shot_events") or report["hit_events"],
            status_text=status_text,
        )
        report["shot_events"] = write_shot_clips(video_path, report["shot_events"], SHOT_CLIP_DIR / video_path.stem)
        report["annotated_video"] = str(annotated_video)
        video_warning = _check_browser_playable(annotated_video)
        if video_warning:
            report["video_warning"] = video_warning
        preview_path = extract_video_preview(
            annotated_video,
            PREVIEW_DIR / f"{video_path.stem}_annotated_preview.jpg",
            time_sec=1.0,
        )
        if preview_path:
            report["annotated_preview"] = str(preview_path)
        report["runtime"] = {
            "device": device_name,
            "target_player": target_player,
            "target_bbox": target_bbox,
            "analysis_preset": cfg.get("analysis_preset", "adaptive"),
            "footwork_map_mode": cfg.get("footwork_map_mode", "image"),
        }
        return format_frontend_report(report)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
