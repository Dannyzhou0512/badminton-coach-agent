"""
FastAPI backend for the standalone HTML frontend.

Run (local debug):
  python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000

Run (allow mobile preview on LAN):
  python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
"""



import copy
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
from fastapi import Body, Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles


ROOT = Path(__file__).resolve().parents[2]
INFERENCE_DIR = ROOT / "src" / "inference"
API_DIR = ROOT / "src" / "api"

# Load .env file if exists
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass
if str(INFERENCE_DIR) not in sys.path:
    sys.path.insert(0, str(INFERENCE_DIR))
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

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

from auth import router as auth_router  # noqa: E402
from auth import get_current_user  # noqa: E402


UPLOAD_DIR = ROOT / "outputs" / "api_uploads"
ANNOTATED_DIR = ROOT / "outputs" / "api_annotated"
SHOT_CLIP_DIR = ROOT / "outputs" / "api_shot_clips"
PREVIEW_DIR = ROOT / "outputs" / "api_previews"
DB_PATH = ROOT / "outputs" / "history.db"
DEFAULT_CHECKPOINT = ROOT / "models" / "pose_sequence_tcn_gru.pt"
DEFAULT_POSE_MODEL = ROOT / "yolov8s-pose.pt"


# ---------------------------------------------------------------------------
# Action name i18n (used by both web frontend and WeChat mini-program)
# ---------------------------------------------------------------------------
ACTION_NAME_I18N = {
    "Short Serve": {"zh": "短发球", "en": "Short Serve", "ja": "ショートサーブ", "ko": "숏 서브", "id": "Servis Pendek"},
    "Cross Court Flight": {"zh": "斜线高远球", "en": "Cross Court Flight", "ja": "クロスクリア", "ko": "크로스 클리어", "id": "Pukulan Melambung Silang"},
    "Lift": {"zh": "挑球", "en": "Lift", "ja": "リフト", "ko": "리프트", "id": "Lift"},
    "Tap Smash": {"zh": "点杀", "en": "Tap Smash", "ja": "タップスマッシュ", "ko": "탭 스매시", "id": "Tap Smash"},
    "Block": {"zh": "挡网", "en": "Block", "ja": "ブロック", "ko": "블록", "id": "Block"},
    "Drop Shot": {"zh": "吊球", "en": "Drop Shot", "ja": "ドロップショット", "ko": "드롭 샷", "id": "Drop Shot"},
    "Push Shot": {"zh": "推球", "en": "Push Shot", "ja": "プッシュショット", "ko": "푸시 샷", "id": "Push Shot"},
    "Transitional Slice": {"zh": "过渡劈吊", "en": "Transitional Slice", "ja": "トランジショナルスライス", "ko": "트랜지션 슬라이스", "id": "Transitional Slice"},
    "Cut": {"zh": "搓球", "en": "Cut", "ja": "カット", "ko": "컷", "id": "Cut"},
    "Rush Shot": {"zh": "突击球", "en": "Rush Shot", "ja": "ラッシュショット", "ko": "러시 샷", "id": "Rush Shot"},
    "Defensive Clear": {"zh": "防守高远球", "en": "Defensive Clear", "ja": "ディフェンシブクリア", "ko": "디펜시브 클리어", "id": "Defensive Clear"},
    "Defensive Drive": {"zh": "防守抽球", "en": "Defensive Drive", "ja": "ディフェンシブドライブ", "ko": "디펜시브 드라이브", "id": "Defensive Drive"},
    "Clear": {"zh": "高远球", "en": "Clear", "ja": "クリア", "ko": "클리어", "id": "Clear"},
    "Long Serve": {"zh": "长发球", "en": "Long Serve", "ja": "ロングサーブ", "ko": "롱 서브", "id": "Servis Panjang"},
    "Smash": {"zh": "杀球", "en": "Smash", "ja": "スマッシュ", "ko": "스매시", "id": "Smash"},
    "Flat Shot": {"zh": "平抽球", "en": "Flat Shot", "ja": "フラットショット", "ko": "플랫 샷", "id": "Flat Shot"},
    "Rear Court Flat Drive": {"zh": "后场平抽", "en": "Rear Court Flat Drive", "ja": "リアコートフラットドライブ", "ko": "리어코트 플랫 드라이브", "id": "Rear Court Flat Drive"},
    "Short Flat Shot": {"zh": "前场平抽", "en": "Short Flat Shot", "ja": "ショートフラットショット", "ko": "숏 플랫 샷", "id": "Short Flat Shot"},
}

ACTION_NAME_ZH_FALLBACK = {
    "Short Serve": "\u77ed\u53d1\u7403",
    "Cross Court Flight": "\u659c\u7ebf\u9ad8\u8fdc\u7403",
    "Lift": "\u6311\u7403",
    "Tap Smash": "\u70b9\u6740",
    "Block": "\u6321\u7f51",
    "Drop Shot": "\u540a\u7403",
    "Push Shot": "\u63a8\u7403",
    "Transitional Slice": "\u8fc7\u6e21\u5288\u540a",
    "Cut": "\u6413\u7403",
    "Rush Shot": "\u7a81\u51fb\u7403",
    "Defensive Clear": "\u9632\u5b88\u9ad8\u8fdc\u7403",
    "Defensive Drive": "\u9632\u5b88\u62bd\u7403",
    "Clear": "\u9ad8\u8fdc\u7403",
    "Long Serve": "\u957f\u53d1\u7403",
    "Smash": "\u6740\u7403",
    "Flat Shot": "\u5e73\u62bd\u7403",
    "Rear Court Flat Drive": "\u540e\u573a\u5e73\u62bd",
    "Short Flat Shot": "\u524d\u573a\u5e73\u62bd",
}


QUALITY_LEVEL_I18N = {
    "数据不足": {"zh": "数据不足", "en": "Insufficient Data", "ja": "データ不足", "ko": "데이터 부족", "id": "Data Tidak Cukup"},
    "优秀": {"zh": "优秀", "en": "Excellent", "ja": "優秀", "ko": "우수", "id": "Sangat Baik"},
    "良好": {"zh": "良好", "en": "Good", "ja": "良好", "ko": "양호", "id": "Baik"},
    "一般": {"zh": "一般", "en": "Average", "ja": "普通", "ko": "보통", "id": "Cukup"},
    "较差": {"zh": "较差", "en": "Below Average", "ja": "やや劣る", "ko": "부족", "id": "Kurang"},
}


def translate_action_name(name, language):
    lang = language if language in {"zh", "en", "ja", "ko", "id"} else "en"
    clean_name = name.strip() if isinstance(name, str) else name
    if lang == "zh" and clean_name in ACTION_NAME_ZH_FALLBACK:
        return ACTION_NAME_ZH_FALLBACK[clean_name]
    mapping = ACTION_NAME_I18N.get(clean_name)
    if mapping:
        return mapping.get(lang, name)
    return name


def translate_quality_level(level, language):
    lang = language if language in {"zh", "en", "ja", "ko", "id"} else "en"
    mapping = QUALITY_LEVEL_I18N.get(level)
    if mapping:
        return mapping.get(lang, level)
    return level


def translate_text_terms(text, language):
    lang = language if language in {"zh", "en", "ja", "ko", "id"} else "en"
    if lang == "en" or not isinstance(text, str):
        return text
    # Replace longest names first to avoid partial overlaps
    for en_name in sorted(ACTION_NAME_I18N.keys(), key=len, reverse=True):
        translated = ACTION_NAME_I18N[en_name].get(lang)
        if translated and en_name in text:
            text = text.replace(en_name, translated)
    return text


def translate_report(report, language):
    lang = language if language in {"zh", "en", "ja", "ko", "id"} else "en"
    if lang == "en":
        return report

    if report.get("predicted_action"):
        report["predicted_action"] = translate_action_name(report["predicted_action"], lang)

    for item in report.get("top_predictions", []):
        if isinstance(item, dict) and item.get("class_name"):
            item["class_name"] = translate_action_name(item["class_name"], lang)

    for event in report.get("hit_events", []):
        if event.get("predicted_action"):
            event["predicted_action"] = translate_action_name(event["predicted_action"], lang)

    for event in report.get("shot_events", []):
        if event.get("predicted_action"):
            event["predicted_action"] = translate_action_name(event["predicted_action"], lang)
        if event.get("shot_action"):
            event["shot_action"] = translate_action_name(event["shot_action"], lang)
        if event.get("quality_level"):
            event["quality_level"] = translate_quality_level(event["quality_level"], lang)
        for pred in event.get("shot_top_predictions", []):
            if pred.get("action"):
                pred["action"] = translate_action_name(pred["action"], lang)

    # Translate action terms embedded in coach report free text
    coach_report = report.get("coach_report")
    if isinstance(coach_report, dict):
        for key in ("highlights", "focus", "plan"):
            if isinstance(coach_report.get(key), list):
                coach_report[key] = [translate_text_terms(t, lang) for t in coach_report[key]]
        if isinstance(coach_report.get("summary"), str):
            coach_report["summary"] = translate_text_terms(coach_report["summary"], lang)

    if isinstance(report.get("llm_coach_report"), str):
        report["llm_coach_report"] = translate_text_terms(report["llm_coach_report"], lang)

    for segment in report.get("llm_coach_segments", []):
        if isinstance(segment, dict):
            for seg_key in ("content", "summary", "advice"):
                if isinstance(segment.get(seg_key), str):
                    segment[seg_key] = translate_text_terms(segment[seg_key], lang)

    return report


app = FastAPI(title="Badminton Coach Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.on_event("startup")
async def startup_check():
    print("=" * 60)
    print("🏸 羽毛球AI教练系统启动中...")
    print("=" * 60)

    # Check model files
    checkpoint_path = DEFAULT_CHECKPOINT
    yolo_path = DEFAULT_POSE_MODEL
    models_ok = True
    if not checkpoint_path.exists():
        print(f"❌ 错误: 姿态分类模型缺失: {checkpoint_path}")
        models_ok = False
    else:
        print(f"✅ 姿态分类模型已加载: {checkpoint_path.name}")

    if not yolo_path.exists():
        print(f"⚠️  YOLOv8姿态模型未找到，首次分析时将自动下载")
    else:
        print(f"✅ YOLOv8姿态模型已就绪: {yolo_path.name}")

    # Check CUDA
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        print(f"✅ GPU加速已启用: {gpu_name}")
    else:
        print("⚠️  未检测到NVIDIA GPU，将使用CPU模式（速度较慢）")
        print("   如需GPU加速，请安装CUDA版本的PyTorch")

    # Check FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print(f"✅ FFmpeg已就绪: {ffmpeg_path}")
    else:
        print("⚠️  未检测到FFmpeg，标注视频生成速度可能较慢")
        print("   安装FFmpeg可启用NVENC硬件加速，速度提升3-5倍")

    # Check LLM API keys
    llm_configured = False
    for key in ["DASHSCOPE_API_KEY", "QWEN_API_KEY", "ZHIPUAI_API_KEY", "ZHIPU_API_KEY"]:
        if os.environ.get(key):
            llm_configured = True
            break
    if llm_configured:
        print("✅ AI教练API Key已配置")
    else:
        print("ℹ️  AI教练API Key未配置（可选功能，不影响核心分析）")
        print("   如需使用AI教练点评，请在.env文件中配置API Key")

    # Ensure directories exist
    for d in [UPLOAD_DIR, ANNOTATED_DIR, SHOT_CLIP_DIR, PREVIEW_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    init_db()
    print("=" * 60)
    print("🚀 服务启动完成！请在浏览器中访问:")
    print("   http://127.0.0.1:8000/frontend/")
    print("=" * 60)


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            created_at TEXT NOT NULL,
            video_name TEXT,
            duration_seconds REAL,
            total_shots INTEGER,
            avg_quality_score REAL,
            dominant_action TEXT,
            report_json TEXT NOT NULL,
            annotated_video_url TEXT,
            annotated_preview_url TEXT
        )"""
    )
    conn.commit()

    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(history)").fetchall()]
        if "user_id" not in cols:
            conn.execute("ALTER TABLE history ADD COLUMN user_id INTEGER")
            conn.commit()
            print("[DB] Added user_id column to history table")
    except Exception as e:
        print(f"[WARN] Failed to migrate user_id column: {e}")

    rows = conn.execute(
        "SELECT id, report_json FROM history WHERE avg_quality_score IS NULL OR dominant_action IS NULL"
    ).fetchall()
    for row in rows:
        try:
            report = json.loads(row["report_json"])
            shots = report.get("shot_events", []) or []
            scores = []
            for s in shots:
                score = s.get("quality_score")
                if score is None and isinstance(s.get("quality"), dict):
                    score = s["quality"].get("overall")
                if score is not None:
                    scores.append(float(score))
            avg_score = round(float(np.mean(scores)), 1) if scores else None
            action_counts = {}
            for s in shots:
                name = s.get("shot_action") or s.get("action_name") or s.get("predicted_action") or "unknown"
                action_counts[name] = action_counts.get(name, 0) + 1
            dominant = max(action_counts, key=action_counts.get) if action_counts else None
            conn.execute(
                "UPDATE history SET avg_quality_score = ?, dominant_action = ? WHERE id = ?",
                (avg_score, dominant, row["id"]),
            )
        except Exception as e:
            print(f"[WARN] Failed to backfill history score for id={row['id']}: {e}")
    if rows:
        conn.commit()
    conn.close()


def save_history(video_name, report, annotated_video_url=None, annotated_preview_url=None, user_id=None):
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    shots = report.get("shot_events", []) or []
    scores = []
    for s in shots:
        score = s.get("quality_score")
        if score is None and isinstance(s.get("quality"), dict):
            score = s["quality"].get("overall")
        if score is not None:
            scores.append(float(score))
    avg_score = round(float(np.mean(scores)), 1) if scores else None
    action_counts = {}
    for s in shots:
        name = s.get("shot_action") or s.get("action_name") or s.get("predicted_action") or "unknown"
        action_counts[name] = action_counts.get(name, 0) + 1
    dominant = max(action_counts, key=action_counts.get) if action_counts else None
    conn.execute(
        """INSERT INTO history
           (user_id, created_at, video_name, duration_seconds, total_shots, avg_quality_score,
            dominant_action, report_json, annotated_video_url, annotated_preview_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            datetime.now().isoformat(),
            video_name,
            report.get("video_metadata", {}).get("duration_seconds")
            or report.get("video_metadata", {}).get("duration_sec")
            or report.get("duration_seconds"),
            len(shots),
            avg_score,
            dominant,
            json.dumps(report, ensure_ascii=False),
            annotated_video_url,
            annotated_preview_url,
        ),
    )
    conn.commit()
    conn.close()


def get_history_list(user_id=None, limit=50):
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    if user_id is not None:
        rows = conn.execute(
            """SELECT id, created_at, video_name, duration_seconds, total_shots,
                      avg_quality_score, dominant_action, annotated_video_url, annotated_preview_url
               FROM history WHERE user_id = ? ORDER BY id DESC LIMIT ?""",
            (user_id, limit,),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT id, created_at, video_name, duration_seconds, total_shots,
                      avg_quality_score, dominant_action, annotated_video_url, annotated_preview_url
               FROM history ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_history_detail(session_id, user_id=None):
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    if user_id is not None:
        row = conn.execute(
            "SELECT * FROM history WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        ).fetchone()
    else:
        row = conn.execute("SELECT * FROM history WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    if not row:
        return None
    result = dict(row)
    result["report"] = json.loads(result.pop("report_json"))
    return result


def delete_history(session_id, user_id=None):
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    if user_id is not None:
        conn.execute(
            "DELETE FROM history WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        )
    else:
        conn.execute("DELETE FROM history WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


@lru_cache(maxsize=1)
def get_yolo_model(pose_model_path):
    from ultralytics import YOLO
    return YOLO(str(pose_model_path))


def precheck_video(video_path, pose_model_path, conf_threshold=0.25):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {"ok": False, "items": [{"name": "视频可打开", "status": "fail", "value": "无法打开视频文件", "detail": "请检查视频格式是否为MP4/MOV/AVI"}]}

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration = total_frames / fps if fps > 0 else 0

    items = []

    items.append({
        "name": "视频分辨率",
        "status": "pass" if min(width, height) >= 360 else "warn",
        "value": f"{width}x{height}",
        "detail": None if min(width, height) >= 360 else "分辨率过低，建议至少480p以保证关键点检测精度",
    })

    items.append({
        "name": "视频时长",
        "status": "pass" if 3 <= duration <= 600 else "warn",
        "value": f"{duration:.1f}秒",
        "detail": None if 3 <= duration <= 600 else ("视频过短，建议至少3秒" if duration < 3 else "视频较长（>10分钟），分析时间会较久"),
    })

    model = get_yolo_model(str(pose_model_path))

    sample_count = min(10, max(3, total_frames // 30 if total_frames > 0 else 3))
    sample_indices = []
    if total_frames > sample_count:
        for i in range(1, sample_count + 1):
            sample_indices.append(int(i * total_frames / (sample_count + 1)))
    else:
        sample_indices = list(range(min(total_frames, 3)))
    sample_indices = sorted(set(sample_indices))

    person_sizes = []
    person_detected_frames = 0
    person_counts_per_frame = []
    blurry_scores = []
    checked_frames = 0

    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        checked_frames += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        blurry_scores.append(laplacian_var)

        results = model(frame, conf=conf_threshold, verbose=False)
        persons_in_frame = []
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                if int(box.cls[0]) == 0:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    area = (x2 - x1) * (y2 - y1)
                    persons_in_frame.append(area)
        frame_area = width * height if width * height > 0 else 1
        if persons_in_frame:
            best_area = max(persons_in_frame)
            ratio = best_area / frame_area
            person_sizes.append(ratio)
            person_detected_frames += 1
        else:
            person_sizes.append(0)
        person_counts_per_frame.append(len(persons_in_frame))

    cap.release()

    detection_ratio = person_detected_frames / max(checked_frames, 1)
    avg_person_ratio = float(np.mean(person_sizes)) if person_sizes else 0
    max_person_ratio = float(np.max(person_sizes)) if person_sizes else 0
    avg_person_count = float(np.mean(person_counts_per_frame)) if person_counts_per_frame else 0
    avg_blur = float(np.mean(blurry_scores)) if blurry_scores else 0

    scene_type = "closeup"
    scene_label = "近景训练"
    if avg_person_ratio < 0.04 and avg_person_count >= 2 and detection_ratio >= 0.5:
        scene_type = "match_wide"
        scene_label = "比赛远景"
    elif avg_person_ratio < 0.06 and detection_ratio >= 0.5:
        scene_type = "wide"
        scene_label = "远景拍摄"

    items.append({
        "name": "人物检测",
        "status": "pass" if detection_ratio >= 0.5 else ("warn" if detection_ratio >= 0.2 else "fail"),
        "value": f"{person_detected_frames}/{checked_frames}帧检测到人",
        "detail": None if detection_ratio >= 0.5 else (
            "部分帧未检测到人物，可能存在遮挡或画面问题" if detection_ratio >= 0.2
            else "大多数帧未检测到人物，请确认视频拍摄的是羽毛球活动场景"
        ),
    })

    if avg_person_ratio >= 0.005:
        if avg_person_ratio >= 0.06:
            size_status = "pass"
            size_detail = None
        elif avg_person_ratio >= 0.02:
            size_status = "warn"
            size_detail = f"人物在画面中偏小（{scene_label}），系统将使用远景优化模式进行分析，建议靠近拍摄可获得更高精度"
        else:
            size_status = "warn"
            size_detail = "人物较小，关键点精度可能下降，建议在播放后检查标注视频确认跟踪是否正确"
        items.append({
            "name": "人物大小",
            "status": size_status,
            "value": f"占画面{avg_person_ratio*100:.1f}%",
            "detail": size_detail,
        })
    else:
        items.append({
            "name": "人物大小",
            "status": "fail",
            "value": f"占画面{avg_person_ratio*100:.1f}%",
            "detail": "人物在画面中极小或未检测到，请确认拍摄距离合适",
        })

    items.append({
        "name": "画面清晰度",
        "status": "pass" if avg_blur >= 50 else ("warn" if avg_blur >= 20 else "fail"),
        "value": f"清晰度{avg_blur:.0f}",
        "detail": None if avg_blur >= 50 else (
            "画面存在一定压缩/模糊，可能影响关键点精度" if avg_blur >= 20
            else "画面严重模糊，请确保拍摄时对焦清晰、光线充足"
        ),
    })

    items.append({
        "name": "场景识别",
        "status": "pass" if scene_type != "closeup" or avg_person_ratio >= 0.04 else "warn",
        "value": scene_label,
        "detail": None if scene_type != "match_wide" else (
            "检测到比赛远景视频：人物较小但可识别，系统将自动适配分析参数"
            if avg_person_ratio >= 0.01 else
            "检测到极远景比赛视频，球员可能在画面中过小，建议选择更近的视角"
        ) if scene_type == "match_wide" else None,
    })

    has_fail = any(i["status"] == "fail" for i in items)
    has_warn = any(i["status"] == "warn" for i in items)
    overall = "fail" if has_fail else ("warn" if has_warn else "pass")

    if overall == "fail" and detection_ratio >= 0.2 and avg_person_ratio >= 0.005:
        overall = "warn"
        for item in items:
            if item["name"] == "人物大小" and item["status"] == "fail":
                item["status"] = "warn"
                item["detail"] = "人物较小，但已成功检测到人体，将尝试分析"
            elif item["status"] == "fail" and item["name"] != "视频可打开":
                item["status"] = "warn"
        has_fail = any(i["status"] == "fail" for i in items)
        overall = "fail" if has_fail else "warn"

    return {
        "ok": overall != "fail",
        "overall": overall,
        "scene_type": scene_type,
        "items": items,
        "summary": {
            "resolution": f"{width}x{height}",
            "duration_seconds": round(duration, 1),
            "fps": round(fps, 1),
            "person_detection_ratio": round(detection_ratio, 2),
            "avg_person_ratio": round(avg_person_ratio, 3),
            "max_person_ratio": round(max_person_ratio, 3),
            "avg_person_count": round(avg_person_count, 1),
            "avg_blur_score": round(avg_blur, 1),
            "scene_type": scene_type,
            "scene_label": scene_label,
        },
    }


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
    sample_stride=2,
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
        sample_stride=sample_stride,
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


def localized_label_names(label_names, language):
    return {
        int(label): translate_action_name(clean_class_name(name), language)
        for label, name in (label_names or {}).items()
    }


def normalize_court_corners(value):
    if not isinstance(value, dict):
        return None
    required = ["top_left", "top_right", "bottom_left", "bottom_right"]
    normalized = {}
    for key in required:
        point = value.get(key)
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            return None
        try:
            x = float(point[0])
            y = float(point[1])
        except (TypeError, ValueError):
            return None
        normalized[key] = [min(max(x, 0.0), 1.0), min(max(y, 0.0), 1.0)]
    return normalized


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
        "adaptive": {"max_frames": None, "sample_stride": 2, "batch_size": 128, "window_size": 32, "stride": 8},
        "fast": {"max_frames": None, "sample_stride": 3, "batch_size": 128, "window_size": 32, "stride": 16},
        "balanced": {"max_frames": None, "sample_stride": 2, "batch_size": 128, "window_size": 32, "stride": 12},
        "full": {"max_frames": None, "sample_stride": 1, "batch_size": 64, "window_size": 24, "stride": 4},
        "match_far": {"max_frames": None, "sample_stride": 3, "batch_size": 128, "window_size": 32, "stride": 16},
        "training_close": {"max_frames": None, "sample_stride": 2, "batch_size": 128, "window_size": 32, "stride": 8},
        "standard": {"max_frames": None, "sample_stride": 2, "batch_size": 128, "window_size": 32, "stride": 12},
    }
    return presets.get(name or "adaptive", presets["adaptive"])


def render_cache_key(cfg, target_player, target_bbox, target_roi, ui_language):
    payload = {
        "version": 2,
        "target_player": target_player,
        "target_bbox": list(target_bbox) if target_bbox is not None else None,
        "target_roi": list(target_roi) if target_roi is not None else None,
        "conf_threshold": round(float(cfg.get("conf_threshold", 0.3)), 4),
        "analysis_preset": cfg.get("analysis_preset", "adaptive"),
        "sample_stride": cfg.get("sample_stride"),
        "window_size": cfg.get("window_size"),
        "stride": cfg.get("stride"),
        "language": ui_language,
        "browser_video_profile": "h264-baseline-ultrafast",
        "annotated_output_fps": cfg.get("annotated_output_fps"),
    }
    return digest_bytes(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8"))


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


def build_footwork_trace(pose_seq, sampled_indices=None, frame_size=None, conf_threshold=0.3, max_points=720, fps=None, court_corners=None):
    centers_raw = footwork_centers(pose_seq, conf_threshold=conf_threshold)
    centers_filtered = filter_footwork_jumps(centers_raw)

    frame_indices = []
    points_list = []
    for seq_idx, center in enumerate(centers_filtered):
        if center is None:
            continue
        if sampled_indices and seq_idx < len(sampled_indices):
            real_frame = int(sampled_indices[seq_idx])
        else:
            real_frame = int(seq_idx)
        frame_indices.append(real_frame)
        points_list.append(center)

    if len(points_list) < 3:
        return []

    points = np.asarray(points_list, dtype=np.float32)
    frame_indices = np.asarray(frame_indices, dtype=np.int32)
    fps_val = float(fps) if fps is not None else 30.0

    if court_corners:
        if frame_size and frame_size.get("width") and frame_size.get("height"):
            scale = np.asarray([max(float(frame_size["width"]), 1.0), max(float(frame_size["height"]), 1.0)], dtype=np.float32)
            normalized_points = np.clip(points / scale, 0.0, 1.0)
        else:
            normalized_points = np.clip(points / max(np.max(points), 1.0), 0.0, 1.0)
        source = np.asarray(
            [
                [court_corners["top_left"][0], court_corners["top_left"][1]],
                [court_corners["top_right"][0], court_corners["top_right"][1]],
                [court_corners["bottom_left"][0], court_corners["bottom_left"][1]],
                [court_corners["bottom_right"][0], court_corners["bottom_right"][1]],
            ],
            dtype=np.float32,
        )
        destination = np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], dtype=np.float32)
        matrix = cv2.getPerspectiveTransform(source, destination)
        mapped = cv2.perspectiveTransform(normalized_points.reshape(-1, 1, 2).astype(np.float32), matrix)
        normalized_points = np.clip(mapped.reshape(-1, 2), 0.0, 1.0)
    else:
        if frame_size and frame_size.get("width") and frame_size.get("height"):
            scale = np.asarray([max(float(frame_size["width"]), 1.0), max(float(frame_size["height"]), 1.0)], dtype=np.float32)
            points_scaled = points / scale
            mins = np.percentile(points_scaled, 2, axis=0)
            maxs = np.percentile(points_scaled, 98, axis=0)
            span = maxs - mins
            span = np.where(span < 0.1, np.array([0.4, 0.6]), span)
            margin = span * 0.2
            mins_adj = np.maximum(mins - margin, 0.0)
            maxs_adj = np.minimum(maxs + margin, 1.0)
            normalized_points = np.clip((points_scaled - mins_adj) / (maxs_adj - mins_adj), 0.0, 1.0)
        else:
            mins = np.percentile(points, 2, axis=0)
            maxs = np.percentile(points, 98, axis=0)
            span = maxs - mins
            span = np.where(span < 30, np.array([200, 200]), span)
            margin = span * 0.2
            mins_adj = mins - margin
            maxs_adj = maxs + margin
            normalized_points = np.clip((points - mins_adj) / (maxs_adj - mins_adj), 0.0, 1.0)

    smoothed = normalized_points.copy()
    if len(smoothed) >= 7:
        kernel = np.array([0.06, 0.12, 0.2, 0.24, 0.2, 0.12, 0.06], dtype=np.float32)
        kernel = kernel / kernel.sum()
        for _ in range(3):
            temp = smoothed.copy()
            for i in range(3, len(smoothed) - 3):
                window = smoothed[i-3:i+4]
                temp[i] = np.average(window, axis=0, weights=kernel)
            smoothed = temp
    elif len(smoothed) >= 5:
        for _ in range(3):
            temp = smoothed.copy()
            for i in range(2, len(smoothed) - 2):
                temp[i] = np.mean(smoothed[i-2:i+3], axis=0)
            smoothed = temp

    times_sec = frame_indices.astype(np.float64) / max(fps_val, 1.0)

    if len(smoothed) > max_points:
        target_times = np.linspace(times_sec[0], times_sec[-1], max_points)
        resampled_x = np.interp(target_times, times_sec, smoothed[:, 0])
        resampled_y = np.interp(target_times, times_sec, smoothed[:, 1])
        resampled_frames = np.interp(target_times, times_sec, frame_indices)
        trace = []
        for t, fx, fy, fr in zip(target_times, resampled_x, resampled_y, resampled_frames):
            trace.append({
                "frame": int(round(fr)),
                "x": round(float(np.clip(fx, 0.0, 1.0)), 4),
                "y": round(float(np.clip(fy, 0.0, 1.0)), 4),
                "time_sec": round(float(t), 3),
            })
    else:
        trace = []
        for fr, fx, fy, t in zip(frame_indices, smoothed[:, 0], smoothed[:, 1], times_sec):
            trace.append({
                "frame": int(fr),
                "x": round(float(np.clip(fx, 0.0, 1.0)), 4),
                "y": round(float(np.clip(fy, 0.0, 1.0)), 4),
                "time_sec": round(float(t), 3),
            })

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
        "llm_language": report.get("llm_language", "zh"),
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


CHAT_SYSTEM_PROMPTS = {
    "zh": (
        "你是\"羽动智练\"的羽毛球 AI 教练。回答要专业、具体、可执行，"
        "优先围绕羽毛球技术、步伐、训练计划、比赛复盘、运动恢复和安全建议。"
        "如果用户问到伤病、疼痛或医学问题，只给一般运动安全建议，并提醒必要时咨询医生或康复师。"
        "如果提供了训练分析上下文，只能基于这些数据做推断，不要编造视频中不存在的细节。"
        "回答不要使用 Markdown 标题、星号加粗、井号、代码块或项目符号占位符；"
        "请用自然中文短段落输出，必要时用\"一、二、三\"编号。"
    ),
    "en": (
        "You are the AI badminton coach of \"BadmintonAI\". Answer professionally, concretely, and actionably, "
        "focusing on badminton technique, footwork, training plans, match review, recovery, and safety. "
        "If asked about injury or medical issues, give general safety advice and recommend consulting a doctor. "
        "If training context is provided, infer only from that data; do not fabricate details. "
        "Do not use markdown headers, bold asterisks, code blocks, or bullet placeholders; "
        "use natural short paragraphs, numbered with \"1. 2. 3.\" when needed."
    ),
    "ja": (
        "あなたは「BadmintonAI」のバドミントンAIコーチです。技術、フットワーク、練習計画、試合复盘、リカバリー、安全について、"
        "専門的で具体的かつ実行可能な回答をしてください。怪我や痛みについては一般的な安全アドバイスにとどめ、医師への相談を推奨してください。"
        "分析コンテキストがある場合はそのデータのみに基づき、動画にない詳細を捏造しないでください。"
        "Markdownの見出し、太字、コードブロック、箇条書きは使わず、自然な短い段落で、必要に応じて「1. 2. 3.」で番号付けしてください。"
    ),
    "ko": (
        "당신은 'BadmintonAI'의 배드민턴 AI 코치입니다. 기술, 풋워크, 훈련 계획, 경기 복기, 회복, 안전에 대해 "
        "전문적이고 구체적이며 실행 가능한 답변을 하세요. 부상에 관한 질문에는 일반적 안전 조언만 하고 의사 상담을 권장하세요. "
        "분석 컨텍스트가 제공되면 그 데이터만 기반으로 추론하고, 영상에 없는 세부사항을 지어내지 마세요. "
        "Markdown 제목, 굵은 글씨, 코드 블록, 글머리 기호는 사용하지 말고 자연스러운 짧은 단락으로, 필요시 '1. 2. 3.'으로 번호 매기세요."
    ),
    "id": (
        "Anda adalah pelatih bulu tangkis AI dari 'BadmintonAI'. Jawablah secara profesional, konkret, dan dapat dijalankan, "
        "fokus pada teknik, footwork, rencana latihan, review tanding, pemulihan, dan keselamatan. "
        "Jika ditanya cedera, berikan saran keamanan umum dan sarankan konsultasi dokter. "
        "Jika konteks analisis diberikan, simpulkan hanya dari data itu; jangan mengarang detail. "
        "Jangan gunakan heading markdown, blok kode, atau bullet; gunakan paragraf pendek alami, bernomor '1. 2. 3.' bila perlu."
    ),
}

CHAT_CONTEXT_PROMPTS = {
    "zh": "本次训练分析上下文如下：\n",
    "en": "Training analysis context:\n",
    "ja": "今回のトレーニング分析コンテキスト：\n",
    "ko": "이번 훈련 분석 컨텍스트:\n",
    "id": "Konteks analisis latihan:\n",
}

CHAT_STREAM_STATUS = {
    "zh": ["正在理解你的问题", "正在结合训练报告和羽毛球训练知识", "正在组织可执行的训练建议"],
    "en": ["Understanding your question", "Combining report with badminton knowledge", "Drafting actionable advice"],
    "ja": ["質問を理解しています", "レポートとバドミントン知識を統合しています", "実行可能なアドバイスを作成中"],
    "ko": ["질문을 이해하는 중", "리포트와 배드민턴 지식을 결합하는 중", "실행 가능한 조언을 구성하는 중"],
    "id": ["Memahami pertanyaan Anda", "Menggabungkan laporan dengan pengetahuan bulu tangkis", "Menyusun saran yang dapat dijalankan"],
}


def build_coach_chat_messages(question, history=None, report=None, language="zh"):
    history = history or []
    context = compact_chat_report(report)
    lang = language if language in CHAT_SYSTEM_PROMPTS else "zh"
    system = CHAT_SYSTEM_PROMPTS[lang]
    messages = [{"role": "system", "content": system}]
    if context:
        messages.append(
            {
                "role": "system",
                "content": CHAT_CONTEXT_PROMPTS[lang]
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


@app.post("/api/precheck")
async def api_precheck(video: UploadFile = File(...)):
    video_path = save_upload(video)
    try:
        result = precheck_video(video_path, DEFAULT_POSE_MODEL, conf_threshold=0.25)
        return result
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Precheck failed: {exc}") from exc


@app.get("/api/history")
def api_history_list(limit: int = 50, language: str = "zh", user: dict = Depends(get_current_user)):
    lang = language if language in {"zh", "en", "ja", "ko", "id"} else "zh"
    items = get_history_list(user_id=user["id"], limit=min(limit, 200))
    for item in items:
        item["created_at_display"] = item["created_at"].replace("T", " ")[:19] if item.get("created_at") else ""
        if item.get("dominant_action"):
            item["dominant_action"] = translate_action_name(item["dominant_action"], lang)
    return {"items": items}


@app.get("/api/history/{session_id}")
def api_history_detail(session_id: int, language: str = "zh", user: dict = Depends(get_current_user)):
    lang = language if language in {"zh", "en", "ja", "ko", "id"} else "zh"
    detail = get_history_detail(session_id, user_id=user["id"])
    if not detail:
        raise HTTPException(status_code=404, detail="Session not found")
    detail["created_at_display"] = detail["created_at"].replace("T", " ")[:19] if detail.get("created_at") else ""
    if detail.get("dominant_action"):
        detail["dominant_action"] = translate_action_name(detail["dominant_action"], lang)
    if detail.get("report"):
        translate_report(detail["report"], lang)
    return detail


@app.delete("/api/history/{session_id}")
def api_history_delete(session_id: int, user: dict = Depends(get_current_user)):
    delete_history(session_id, user_id=user["id"])
    return {"ok": True}


@app.post("/api/coach/chat")
def coach_chat(payload: dict = Body(...)):
    question = str(payload.get("question", "")).strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    provider = str(payload.get("provider") or "qwen").strip().lower()
    if provider not in {"qwen", "zhipu"}:
        provider = "qwen"
    language = str(payload.get("language") or "zh").strip().lower()
    if language not in CHAT_SYSTEM_PROMPTS:
        language = "zh"

    defaults = provider_defaults(provider)
    api_key = get_api_key(provider)
    if not api_key:
        env_names = " / ".join(defaults["api_key_env"])
        raise HTTPException(status_code=400, detail=f"Missing API key: {env_names}")

    messages = build_coach_chat_messages(
        question,
        history=payload.get("history") or [],
        report=payload.get("report") if payload.get("use_report_context", True) else None,
        language=language,
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
    language = str(payload.get("language") or "zh").strip().lower()
    if language not in CHAT_SYSTEM_PROMPTS:
        language = "zh"

    defaults = provider_defaults(provider)
    api_key = get_api_key(provider)
    if not api_key:
        env_names = " / ".join(defaults["api_key_env"])
        raise HTTPException(status_code=400, detail=f"Missing API key: {env_names}")

    messages = build_coach_chat_messages(
        question,
        history=payload.get("history") or [],
        report=payload.get("report") if payload.get("use_report_context", True) else None,
        language=language,
    )
    status_lines = CHAT_STREAM_STATUS.get(language, CHAT_STREAM_STATUS["zh"])

    def stream():
        try:
            for line in status_lines:
                yield sse_payload("status", {"text": line})
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


def nms_boxes(boxes, iou_threshold=0.5):
    if len(boxes) == 0:
        return []
    boxes_arr = np.array([[b["x1"], b["y1"], b["x2"], b["y2"]] for b in boxes], dtype=np.float32)
    scores = np.array([b.get("confidence", 0.5) for b in boxes], dtype=np.float32)
    areas = (boxes_arr[:, 2] - boxes_arr[:, 0]) * (boxes_arr[:, 3] - boxes_arr[:, 1])
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(boxes_arr[i, 0], boxes_arr[order[1:], 0])
        yy1 = np.maximum(boxes_arr[i, 1], boxes_arr[order[1:], 1])
        xx2 = np.minimum(boxes_arr[i, 2], boxes_arr[order[1:], 2])
        yy2 = np.minimum(boxes_arr[i, 3], boxes_arr[order[1:], 3])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(ovr <= iou_threshold)[0]
        order = order[inds + 1]
    return [boxes[i] for i in keep]


def remove_nested_boxes(boxes, area_overlap_threshold=0.85):
    if len(boxes) <= 1:
        return boxes
    result = []
    for i, box_a in enumerate(boxes):
        is_nested = False
        ax1, ay1, ax2, ay2 = box_a["x1"], box_a["y1"], box_a["x2"], box_a["y2"]
        area_a = (ax2 - ax1) * (ay2 - ay1)
        for j, box_b in enumerate(boxes):
            if i == j:
                continue
            bx1, by1, bx2, by2 = box_b["x1"], box_b["y1"], box_b["x2"], box_b["y2"]
            area_b = (bx2 - bx1) * (by2 - by1)
            if area_b <= area_a:
                continue
            ix1 = max(ax1, bx1)
            iy1 = max(ay1, by1)
            ix2 = min(ax2, bx2)
            iy2 = min(ay2, by2)
            iw = max(0, ix2 - ix1)
            ih = max(0, iy2 - iy1)
            intersection = iw * ih
            if intersection / max(area_a, 1e-6) > area_overlap_threshold:
                is_nested = True
                break
        if not is_nested:
            result.append(box_a)
    return result if result else boxes


@app.post("/api/detect-players")
async def api_detect_players(video: UploadFile = File(...), conf_threshold: float = Form(0.25)):
    import base64
    video_path = save_upload(video)
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="无法打开视频文件")

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration = total_frames / fps if fps > 0 and total_frames > 0 else 0

        sample_times = [0.0, 0.5, 1.5, 2.5, 4.0]
        sample_frames = []
        for t in sample_times:
            if duration > 0 and t > duration - 0.1:
                continue
            sample_frames.append(t)
        if not sample_frames:
            sample_frames = [0.0]

        model = get_yolo_model(str(DEFAULT_POSE_MODEL))
        frames_data = []
        all_boxes = []

        for time_sec in sample_frames:
            cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000.0)
            ret, frame = cap.read()
            if not ret:
                frame_idx = min(total_frames - 1, max(0, int(time_sec * fps))) if total_frames > 0 else 0
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
            if not ret or frame is None:
                continue

            fh, fw = frame.shape[:2]
            results = model(frame, conf=conf_threshold, verbose=False)
            persons = []
            for r in results:
                if r.boxes is None:
                    continue
                for box in r.boxes:
                    if int(box.cls[0]) == 0:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0].cpu().numpy())
                        area = (x2 - x1) * (y2 - y1)
                        frame_area = fw * fh if fw * fh > 0 else 1
                        area_ratio = area / frame_area
                        persons.append({
                            "x1": float(x1 / fw),
                            "y1": float(y1 / fh),
                            "x2": float(x2 / fw),
                            "y2": float(y2 / fh),
                            "confidence": conf,
                            "area_ratio": float(area_ratio),
                        })

            persons = remove_nested_boxes(persons, area_overlap_threshold=0.85)
            persons = nms_boxes(persons, iou_threshold=0.5)
            persons.sort(key=lambda b: b.get("area_ratio", 0), reverse=True)

            ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            img_b64 = base64.b64encode(encoded.tobytes()).decode("utf-8") if ok else None

            frames_data.append({
                "time_sec": round(time_sec, 2),
                "width": fw,
                "height": fh,
                "image_base64": img_b64,
                "persons": persons[:10],
            })
            for p in persons:
                p["frame_time"] = round(time_sec, 2)
                all_boxes.append(p)

        cap.release()

        if not frames_data:
            raise HTTPException(status_code=422, detail="无法提取视频帧")

        best_frame_idx = 0
        best_count = -1
        for i, fd in enumerate(frames_data):
            score = len(fd["persons"]) * 10 + (1.0 if fd["time_sec"] < 1.0 else 0.5)
            if score > best_count:
                best_count = score
                best_frame_idx = i

        return {
            "ok": True,
            "video_width": width,
            "video_height": height,
            "duration": round(duration, 2),
            "fps": round(fps, 1),
            "frames": frames_data,
            "recommended_frame_idx": best_frame_idx,
            "total_persons_detected": len(all_boxes),
        }
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"球员检测失败: {exc}") from exc


@app.post("/api/analyze")
def analyze_video(video: UploadFile = File(...), config: str = Form("{}"), authorization: Optional[str] = Header(None)):
    cfg = parse_config(config)
    if not DEFAULT_CHECKPOINT.exists():
        raise HTTPException(status_code=500, detail=f"Classifier checkpoint not found: {DEFAULT_CHECKPOINT}")
    if not DEFAULT_POSE_MODEL.exists():
        raise HTTPException(status_code=500, detail=f"Pose model not found: {DEFAULT_POSE_MODEL}")

    current_user = None
    if authorization:
        try:
            from auth import get_user_by_token
            current_user = get_user_by_token(authorization)
        except Exception:
            current_user = None
    user_id = current_user["id"] if current_user else None

    import queue
    import threading

    progress_q = queue.Queue()

    def worker():
        try:
            video_path = progress_q.path
            _do_analyze(video_path, video, cfg, progress_q, user_id=user_id)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            try:
                progress_q.put({"event": "error", "message": str(exc)})
            except Exception:
                pass

    try:
        video_path = save_upload(video)
        progress_q.path = video_path
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    def event_generator():
        yield sse_payload("start", {"message": "开始分析..."})
        while True:
            try:
                evt = progress_q.get(timeout=60)
            except queue.Empty:
                yield sse_payload("heartbeat", {})
                continue
            ev_type = evt.get("event", "progress")
            if ev_type == "done":
                thread.join(timeout=5)
                if "report" in evt:
                    ui_language = str(cfg.get("language") or cfg.get("llm_language") or "zh").strip().lower()
                    if ui_language in {"zh", "en", "ja", "ko", "id"}:
                        translate_report(evt["report"], ui_language)
                    yield sse_payload("result", evt["report"])
                break
            if ev_type == "error":
                thread.join(timeout=5)
                yield sse_payload("error", {"message": evt.get("message", "unknown error")})
                break
            yield sse_payload("progress", evt)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


def _do_analyze(video_path, video, cfg, q, user_id=None):
    def emit(percent, message):
        try:
            q.put({"event": "progress", "percent": int(percent), "message": message})
        except Exception:
            pass

    _stage_start = [time.perf_counter()]
    _t0 = _stage_start[0]

    def lap(label):
        now = time.perf_counter()
        elapsed = now - _stage_start[0]
        print(f"[TIMING] {label}: {elapsed:.2f}s")
        _stage_start[0] = now

    emit(3, "读取视频元数据...")
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
    court_corners = normalize_court_corners(cfg.get("court_corners"))
    footwork_map_mode = str(cfg.get("footwork_map_mode") or "image").strip().lower()
    if court_corners is not None:
        footwork_map_mode = "calibrated"

    if not bool(cfg.get("skip_backend_precheck", False)):
        try:
            quick_check = precheck_video(video_path, DEFAULT_POSE_MODEL, conf_threshold=0.2)
            auto_scene = quick_check.get("scene_type", "closeup")
            if auto_scene == "match_wide" and not cfg.get("conf_threshold"):
                cfg["conf_threshold"] = 0.2
                print(f"[INFO] Auto-detected match_wide scene, using conf_threshold=0.2 for better small-person detection")
            if auto_scene == "match_wide" and target_player == "near" and not cfg.get("target_player"):
                target_player = "largest"
                print(f"[INFO] Auto-detected match_wide scene, using largest target selection")
        except Exception:
            pass
    else:
        print("[INFO] Skipping backend precheck because frontend already completed video precheck")
    lap("load model + precheck")
    print(f"[INFO] Using device={device_name}, preset={cfg.get('analysis_preset', 'adaptive')}, max_frames={preset['max_frames']}, sample_stride={preset.get('sample_stride', 2)}, batch_size={preset.get('batch_size', 64)}")

    emit(10, "提取姿态序列...")
    pose_seq, sampled_indices, video_fps = cached_pose_result(
        str(video_path.resolve()),
        str(DEFAULT_POSE_MODEL.resolve()),
        float(cfg.get("conf_threshold", 0.3)),
        preset["max_frames"],
        int(cfg.get("batch_size", preset.get("batch_size", 64))),
        target_player,
        target_roi,
        target_bbox,
        sample_stride=int(cfg.get("sample_stride", preset.get("sample_stride", 2))),
    )
    lap("pose extraction")

    emit(35, "动作分类中...")
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
    lap("action classification + report")

    emit(50, "检测击球事件...")
    report["hit_events"] = detect_hit_events(pose_seq, windows=windows, label_names=label_names, fps=analysis_fps)
    emit(62, "分类击球类型...")
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
    lap("hit detection + shot classification")

    emit(72, "分析步伐轨迹...")
    report["footwork_scores"] = compute_footwork_scores(pose_seq)
    report["footwork_trace"] = build_footwork_trace(
        pose_seq,
        sampled_indices=sampled_indices,
        frame_size=video_metadata,
        conf_threshold=float(cfg.get("conf_threshold", 0.3)),
        fps=video_fps,
        court_corners=court_corners,
    )
    lap("footwork trace")
    ui_language = str(cfg.get("language") or cfg.get("llm_language") or "zh").strip().lower()
    if ui_language not in {"zh", "en", "ja", "ko", "id"}:
        ui_language = "zh"

    # Build coach/LLM reports using translated action names for better localization
    llm_input_report = translate_report(copy.deepcopy(report), ui_language) if ui_language != "en" else report
    report["coach_report"] = build_coach_report(llm_input_report)
    lap("rule-based coach report")

    llm_provider = cfg.get("llm_provider") or "qwen"
    llm_language = str(cfg.get("llm_language") or "zh").strip().lower()
    if llm_language not in {"zh", "en", "ja", "ko", "id"}:
        llm_language = "zh"
    if bool(cfg.get("generate_llm_report", False)):
        emit(78, "AI教练点评中...")
        try:
            llm_result = generate_segmented_llm_coach_report(
                llm_input_report,
                provider=llm_provider,
                timeout=int(cfg.get("llm_timeout", 120)),
                shots_per_group=int(cfg.get("llm_shots_per_group", 8)),
                max_groups=cfg.get("llm_max_groups"),
                language=llm_language,
            )
            report["llm_provider"] = llm_provider
            report["llm_language"] = llm_language
            report["llm_coach_mode"] = llm_result.get("mode", "segmented")
            report["llm_coach_report"] = llm_result.get("summary", "")
            report["llm_coach_segments"] = llm_result.get("segments", [])
        except Exception as exc:
            report["llm_provider"] = llm_provider
            report["llm_language"] = llm_language
            report["llm_coach_error"] = str(exc)
    lap("llm coach report (if enabled)")

    emit(85, "生成标注视频...")
    render_key = render_cache_key(cfg, target_player, target_bbox, target_roi, ui_language)
    annotated_video = ANNOTATED_DIR / f"{video_path.stem}_{render_key}_annotated.mp4"
    status_text = f"Target: {target_player}"
    video_label_names = localized_label_names(label_names, ui_language)
    video_event_key = "shot_events" if report.get("shot_events") else "hit_events"
    video_event_report = {"hit_events": [], "shot_events": []}
    video_event_report[video_event_key] = copy.deepcopy(report.get(video_event_key) or [])
    video_hit_events = translate_report(video_event_report, ui_language)[video_event_key]
    reuse_annotated_video = bool(cfg.get("reuse_annotated_video", True))
    reused_annotated_video = (
        reuse_annotated_video
        and annotated_video.exists()
        and annotated_video.stat().st_size > 0
    )
    if reused_annotated_video:
        print(f"[INFO] Reusing annotated video cache: {annotated_video.name}")
    else:
        write_full_length_annotated_video(
            video_path,
            pose_seq,
            sampled_indices,
            windows,
            video_label_names,
            annotated_video,
            conf_threshold=float(cfg.get("conf_threshold", 0.3)),
            hit_events=video_hit_events,
            status_text=status_text,
            output_fps=cfg.get("annotated_output_fps"),
        )
    if bool(cfg.get("write_shot_clips", False)):
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
    lap("annotated video + shot clips")
    report["runtime"] = {
        "device": device_name,
        "target_player": target_player,
        "target_bbox": target_bbox,
        "analysis_preset": cfg.get("analysis_preset", "adaptive"),
        "footwork_map_mode": footwork_map_mode,
        "court_calibrated": court_corners is not None,
        "reused_annotated_video": reused_annotated_video,
        "write_shot_clips": bool(cfg.get("write_shot_clips", False)),
    }

    emit(95, "整理报告...")
    frontend_report = format_frontend_report(report)
    try:
        save_history(
            video_name=video.filename,
            report=frontend_report,
            annotated_video_url=frontend_report.get("annotated_video_url"),
            annotated_preview_url=frontend_report.get("annotated_preview_url"),
            user_id=user_id,
        )
    except Exception as hist_exc:
        print(f"[WARN] Failed to save history: {hist_exc}")
    lap("format & save report")
    total = time.perf_counter() - _t0
    print(f"[TIMING] total analysis time: {total:.2f}s")

    q.put({"event": "done", "percent": 100, "message": "分析完成！", "report": frontend_report})
