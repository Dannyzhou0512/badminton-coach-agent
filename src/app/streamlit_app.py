"""
Streamlit demo for the Badminton AI Coach prototype.
"""

import hashlib
import inspect
import json
import sys
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import torch
from PIL import Image

try:
    from streamlit_drawable_canvas import st_canvas
except ImportError:
    st_canvas = None


ROOT = Path(__file__).resolve().parents[2]
INFERENCE_DIR = ROOT / "src" / "inference"
if str(INFERENCE_DIR) not in sys.path:
    sys.path.insert(0, str(INFERENCE_DIR))

import llm_coach as llm_coach_module  # noqa: E402
from llm_coach import generate_llm_coach_report, provider_defaults  # noqa: E402
from predict_video import (  # noqa: E402
    build_report,
    build_coach_report,
    classify_hit_events,
    compute_motion_summary,
    compute_footwork_scores,
    detect_hit_events,
    extract_pose_and_frames_from_video,
    load_model,
    predict_pose_sequence,
    predict_windows,
    topk_from_probs,
    write_full_length_annotated_video,
    write_full_length_tracking_video,
    write_shot_clips,
)


UPLOAD_DIR = ROOT / "outputs" / "streamlit_uploads"
ANNOTATED_DIR = ROOT / "outputs" / "annotated"
SHOT_CLIP_DIR = ROOT / "outputs" / "shot_clips"
DEFAULT_CHECKPOINT = ROOT / "models" / "pose_sequence_tcn_gru.pt"
DEFAULT_POSE_MODEL = ROOT / "yolov8s-pose.pt"


st.set_page_config(page_title="羽动智练", page_icon="羽", layout="wide")


APP_CSS = """
<style>
:root {
  --coach-bg: #f6faf7;
  --coach-ink: #10251d;
  --coach-muted: #60756c;
  --coach-line: #dfe9e3;
  --coach-panel: #ffffff;
  --coach-green: #16a36a;
  --coach-blue: #1f7ae0;
  --coach-warm: #f2bd3d;
  --coach-danger: #ff4b4b;
}

.stApp {
  background:
    radial-gradient(circle at 8% 0%, rgba(22, 163, 106, 0.12), transparent 28rem),
    radial-gradient(circle at 92% 8%, rgba(31, 122, 224, 0.10), transparent 24rem),
    var(--coach-bg);
  color: var(--coach-ink);
}

[data-testid="stSidebar"] {
  background: #eef5f1;
  border-right: 1px solid var(--coach-line);
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  color: var(--coach-ink);
}

.block-container {
  padding-top: 1.25rem;
  max-width: 1480px;
}

div.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--coach-danger), #ff7a4a);
  border: 0;
  min-height: 44px;
  font-weight: 700;
}

div.stDownloadButton > button,
div.stButton > button {
  border-radius: 8px;
}

[data-testid="stMetric"] {
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid var(--coach-line);
  border-radius: 8px;
  padding: 14px 16px;
  box-shadow: 0 12px 28px rgba(16, 37, 29, 0.05);
}

.coach-hero {
  border: 1px solid rgba(22, 163, 106, 0.25);
  border-radius: 10px;
  padding: 26px 28px;
  margin-bottom: 18px;
  background:
    linear-gradient(135deg, rgba(9, 44, 32, 0.94), rgba(15, 78, 55, 0.92)),
    linear-gradient(90deg, transparent 49.8%, rgba(94, 255, 159, 0.25) 50%, transparent 50.2%);
  color: #f4fff9;
  box-shadow: 0 22px 64px rgba(16, 37, 29, 0.16);
}

.coach-hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.coach-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 800;
}

.coach-brand-mark {
  display: inline-grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 8px;
  background: linear-gradient(135deg, #5eff9f, #7dc7ff);
  color: #07130f;
  font-weight: 900;
}

.coach-hero h1 {
  margin: 18px 0 8px;
  font-size: clamp(2.3rem, 5vw, 4.7rem);
  line-height: 0.98;
  letter-spacing: 0;
}

.coach-hero p {
  max-width: 840px;
  margin: 0;
  color: #c7e7d8;
  font-size: 1.02rem;
}

.coach-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}

.coach-pill {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 11px;
  border: 1px solid rgba(199, 231, 216, 0.22);
  border-radius: 999px;
  color: #ddffed;
  background: rgba(255, 255, 255, 0.08);
  font-size: 0.86rem;
}

.coach-panel {
  border: 1px solid var(--coach-line);
  border-radius: 10px;
  padding: 18px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 12px 28px rgba(16, 37, 29, 0.05);
  margin-bottom: 14px;
}

.coach-panel h3 {
  margin: 0 0 8px;
  font-size: 1.05rem;
}

.coach-panel p {
  margin: 0;
  color: var(--coach-muted);
  font-size: 0.94rem;
}

.coach-steps {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 12px 0 22px;
}

.coach-step {
  border: 1px solid var(--coach-line);
  border-radius: 8px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.78);
}

.coach-step strong {
  display: block;
  color: var(--coach-ink);
  margin-bottom: 4px;
}

.coach-step span {
  color: var(--coach-muted);
  font-size: 0.88rem;
}

.coach-section-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin: 12px 0 10px;
}

.coach-section-title h2 {
  margin: 0;
  font-size: 1.45rem;
}

.coach-section-title span {
  color: var(--coach-muted);
  font-size: 0.92rem;
}

.coach-alert {
  border-left: 4px solid var(--coach-warm);
  background: rgba(242, 189, 61, 0.12);
  padding: 12px 14px;
  border-radius: 8px;
  color: #5b4613;
  margin: 10px 0;
}

.coach-small {
  color: var(--coach-muted);
  font-size: 0.9rem;
}

@media (max-width: 900px) {
  .coach-steps {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
"""


def apply_theme():
    st.markdown(APP_CSS, unsafe_allow_html=True)


def file_digest(data):
    return hashlib.sha1(data).hexdigest()[:12]


def save_uploaded_file(uploaded_file):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    data = uploaded_file.getvalue()
    suffix = Path(uploaded_file.name).suffix.lower()
    output_path = UPLOAD_DIR / f"{Path(uploaded_file.name).stem}_{file_digest(data)}{suffix}"
    output_path.write_bytes(data)
    return output_path


def read_first_frame_rgb(video_path):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return None
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def draw_bbox_preview(frame_rgb, bbox):
    if frame_rgb is None or bbox is None:
        return frame_rgb
    output = frame_rgb.copy()
    h, w = output.shape[:2]
    x1, y1, x2, y2 = bbox
    x1, x2 = sorted((int(x1 * w), int(x2 * w)))
    y1, y2 = sorted((int(y1 * h), int(y2 * h)))
    cv2.rectangle(output, (x1, y1), (x2, y2), (255, 75, 75), 4)
    cv2.putText(output, "Target player", (x1 + 8, max(28, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 75, 75), 2)
    return output


def canvas_size_for_frame(frame_rgb, max_width=900):
    h, w = frame_rgb.shape[:2]
    scale = min(float(max_width) / max(float(w), 1.0), 1.0)
    return max(1, int(w * scale)), max(1, int(h * scale))


def bbox_from_canvas_object(obj, canvas_w, canvas_h):
    left = float(obj.get("left", 0.0))
    top = float(obj.get("top", 0.0))
    width = float(obj.get("width", 0.0)) * float(obj.get("scaleX", 1.0))
    height = float(obj.get("height", 0.0)) * float(obj.get("scaleY", 1.0))
    if width <= 2 or height <= 2:
        return None
    x1 = np.clip(left / canvas_w, 0.0, 1.0)
    y1 = np.clip(top / canvas_h, 0.0, 1.0)
    x2 = np.clip((left + width) / canvas_w, 0.0, 1.0)
    y2 = np.clip((top + height) / canvas_h, 0.0, 1.0)
    x1, x2 = sorted((float(x1), float(x2)))
    y1, y2 = sorted((float(y1), float(y2)))
    return x1, y1, x2, y2


def render_target_bbox_selector(video_path, current_bbox=None):
    frame_rgb = read_first_frame_rgb(video_path)
    if frame_rgb is None:
        st.warning("无法读取视频首帧，暂时不能进行目标框选。")
        return current_bbox

    st.subheader("首帧框选目标球员")
    st.caption("在首帧上框住要分析的运动员，尽量包含躯干和双脚；系统会用这个框初始化并连续跟踪该球员。")

    if st_canvas is not None:
        canvas_w, canvas_h = canvas_size_for_frame(frame_rgb)
        background = Image.fromarray(frame_rgb).resize((canvas_w, canvas_h))
        canvas_result = st_canvas(
            fill_color="rgba(255, 75, 75, 0.20)",
            stroke_width=3,
            stroke_color="#ff4b4b",
            background_image=background,
            update_streamlit=True,
            height=canvas_h,
            width=canvas_w,
            drawing_mode="rect",
            display_toolbar=True,
            key=f"target_bbox_canvas_{Path(video_path).stem}",
        )
        objects = (canvas_result.json_data or {}).get("objects", []) if canvas_result is not None else []
        rects = [obj for obj in objects if obj.get("type") == "rect"]
        if rects:
            bbox = bbox_from_canvas_object(rects[-1], canvas_w, canvas_h)
            if bbox is not None:
                st.success("已读取目标框，点击开始分析即可使用该球员作为跟踪目标。")
                return bbox
        st.info("请在首帧上拖出一个矩形目标框。")
        return current_bbox

    st.warning("当前环境未安装 streamlit-drawable-canvas，暂时无法鼠标拖框。可先用下方滑块框选，安装依赖后即可直接拖框。")
    default = current_bbox or (0.35, 0.25, 0.65, 0.90)
    c1, c2 = st.columns(2)
    with c1:
        x1 = st.slider("目标框左边界 %", 0, 100, int(default[0] * 100), 1)
        y1 = st.slider("目标框上边界 %", 0, 100, int(default[1] * 100), 1)
    with c2:
        x2 = st.slider("目标框右边界 %", 0, 100, int(default[2] * 100), 1)
        y2 = st.slider("目标框下边界 %", 0, 100, int(default[3] * 100), 1)
    x1, x2 = sorted((x1 / 100.0, x2 / 100.0))
    y1, y2 = sorted((y1 / 100.0, y2 / 100.0))
    bbox = (x1, y1, x2, y2)
    st.image(draw_bbox_preview(frame_rgb, bbox), caption="目标框预览", use_container_width=True)
    return bbox


@st.cache_resource(show_spinner=False)
def cached_model(checkpoint_path, use_cpu):
    device = torch.device("cuda" if torch.cuda.is_available() and not use_cpu else "cpu")
    model, checkpoint, label_names = load_model(checkpoint_path, device)
    return model, checkpoint, label_names, str(device)


def load_pose_from_upload(uploaded_file):
    uploaded_file.seek(0)
    return np.load(uploaded_file)


def class_name(label, label_names):
    raw = label_names.get(label, str(label))
    return raw.split("_", 1)[1] if "_" in raw else raw


def format_windows(windows, label_names):
    rows = []
    for idx, window in enumerate(windows, start=1):
        label, confidence = window["top_predictions"][0]
        rows.append(
            {
                "片段": idx,
                "起始帧": window["start"],
                "结束帧": window["end"],
                "动作": class_name(label, label_names),
                "置信度": round(confidence, 4),
            }
        )
    return rows


def format_shot_events(events):
    rows = []
    for event in events:
        rows.append(
            {
                "拍次": event.get("index"),
                "时间": event.get("time_sec"),
                "片段": f"{event.get('clip_start_sec', 0):.2f}-{event.get('clip_end_sec', 0):.2f}s",
                "动作": event.get("shot_action") or event.get("predicted_action"),
                "置信度": event.get("shot_confidence") or event.get("confidence"),
                "质量分": event.get("quality_score"),
                "等级": event.get("quality_level"),
                "主要问题": "；".join(event.get("quality_issues", [])[:2]),
                "手腕速度": event.get("wrist_speed"),
                "惯用侧": event.get("dominant_side"),
            }
        )
    return rows


def render_app_header():
    st.markdown(
        """
        <section class="coach-hero">
          <div class="coach-hero-top">
            <div class="coach-brand">
              <span class="coach-brand-mark">羽</span>
              <span>羽动智练 Badminton Coach Agent</span>
            </div>
            <div class="coach-pills" style="margin-top:0;">
              <span class="coach-pill">AI 姿态识别</span>
              <span class="coach-pill">逐拍复盘</span>
              <span class="coach-pill">训练报告</span>
            </div>
          </div>
          <h1>羽毛球智能训练复盘台</h1>
          <p>
            上传训练或比赛视频，先锁定目标运动员，再生成动作识别、击球事件、步伐热力图和个性化训练建议。
            当前页面是可运行的分析工作台，不是静态展示页。
          </p>
          <div class="coach-pills">
            <span class="coach-pill">目标框选跟踪</span>
            <span class="coach-pill">同步标注视频</span>
            <span class="coach-pill">步伐映射</span>
            <span class="coach-pill">Qwen / 智谱AI 报告</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_strip():
    st.markdown(
        """
        <div class="coach-steps">
          <div class="coach-step"><strong>1. 上传视频</strong><span>支持训练片段、比赛片段或姿态文件。</span></div>
          <div class="coach-step"><strong>2. 锁定球员</strong><span>首帧框选目标，减少多人画面误跟踪。</span></div>
          <div class="coach-step"><strong>3. 自动分析</strong><span>提取姿态、识别动作、检测疑似击球点。</span></div>
          <div class="coach-step"><strong>4. 生成报告</strong><span>输出逐拍复盘、步伐指标和训练计划。</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upload_intro(input_mode, target_player):
    target_text = "已启用首帧框选" if target_player == "manual_box" else "可在侧边栏切换到首帧框选"
    mode_text = "视频分析" if input_mode == "视频文件" else "姿态文件分析"
    st.markdown(
        f"""
        <div class="coach-section-title">
          <h2>开始一次训练复盘</h2>
          <span>{mode_text} · {target_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_dashboard():
    left, middle, right = st.columns(3)
    with left:
        st.markdown(
            """
            <div class="coach-panel">
              <h3>目标球员跟踪</h3>
              <p>多人比赛画面建议使用“首帧目标框”，先框住要分析的运动员，再开始识别。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with middle:
        st.markdown(
            """
            <div class="coach-panel">
              <h3>同步标注视频</h3>
              <p>分析后会生成骨架、动作标签、击球事件和右侧步伐热力图的同步视频。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """
            <div class="coach-panel">
              <h3>训练报告</h3>
              <p>本地规则报告默认生成；配置 API Key 后可追加 Qwen 或智谱AI 教练反馈。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def confidence_level(value):
    if value >= 0.75:
        return "高"
    if value >= 0.45:
        return "中"
    return "低"


def render_quality_summary(report):
    summary = report.get("motion_summary", {})
    shot_events = report.get("shot_events", [])
    low_conf = [event for event in shot_events if (event.get("shot_confidence") or event.get("confidence") or 1.0) < 0.45]
    runtime = report.get("runtime", {})
    tracking_mode = runtime.get("target_player") or "-"
    calibration = "已标定" if runtime.get("court_corners") else "未标定"
    map_mode = runtime.get("footwork_map_mode") or "-"

    st.markdown(
        """
        <div class="coach-section-title">
          <h2>分析质量</h2>
          <span>用于判断本次报告哪些部分更可信</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("动作置信级别", confidence_level(float(report.get("confidence", 0.0))))
    q2.metric("低置信拍次", len(low_conf))
    q3.metric("跟踪方式", tracking_mode)
    q4.metric("球场标定", calibration)

    detection_rate = float(summary.get("detection_rate", 0.0))
    if detection_rate < 0.75 or low_conf or calibration == "未标定":
        warnings = []
        if detection_rate < 0.75:
            warnings.append("姿态检测率偏低，建议优先复核标注视频。")
        if low_conf:
            warnings.append(f"存在 {len(low_conf)} 个低置信击球片段，逐拍结论需要谨慎。")
        if calibration == "未标定":
            warnings.append(f"步伐热力图当前使用 {map_mode} 映射，不等同于真实球场坐标。")
        st.markdown(f"<div class='coach-alert'>{' '.join(warnings)}</div>", unsafe_allow_html=True)


def render_radar_chart(scores):
    labels = ["移动量", "启动爆发", "重心稳定", "回位能力", "覆盖范围", "步幅平衡"]
    keys = ["movement", "explosiveness", "stability", "recovery", "coverage", "balance"]
    values = [float(scores.get(key, 0.0)) for key in keys]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values_closed = values + values[:1]
    angles_closed = angles + angles[:1]

    fig, ax = plt.subplots(figsize=(5.6, 5.6), subplot_kw={"polar": True})
    ax.plot(angles_closed, values_closed, color="#ff4b4b", linewidth=2)
    ax.fill(angles_closed, values_closed, color="#ff4b4b", alpha=0.22)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=8)
    ax.grid(color="#d9dfe8")
    return fig


def render_project_overview():
    st.subheader("项目说明")
    st.write("羽动智练是一套面向羽毛球训练复盘的 AI 助手。系统从手机或比赛视频中提取人体姿态，锁定目标球员，检测疑似击球点，并生成逐拍动作识别、步伐热力图和训练建议。")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("输入", "视频 / 姿态")
    c2.metric("姿态", "YOLO-Pose")
    c3.metric("分类", "TCN-GRU")
    c4.metric("教练", "规则 / LLM")

    st.markdown("**分析流程**")
    st.write("1. 上传训练视频或姿态文件")
    st.write("2. 选择目标球员和分析 ROI，减少多人画面误跟踪")
    st.write("3. 使用姿态模型提取人体关键点，并生成骨架标注视频")
    st.write("4. 根据手腕速度峰值检测疑似击球点")
    st.write("5. 围绕每个击球点截取短片段，进行逐拍动作识别")
    st.write("6. 结合脚踝、髋部、手腕等姿态特征生成步伐热力图和质量建议")

    st.markdown("**当前功能**")
    st.write("- 目标球员跟踪：近端、远端、左右、自定义目标点")
    st.write("- ROI 区域过滤：半场、象限、自定义矩形")
    st.write("- 球场标定：支持手动四点标定，把脚步位置映射到固定半场面板")
    st.write("- 同步标注视频：骨架、动作标签、疑似击球点、步伐热力图")
    st.write("- 每拍复盘：逐拍动作、置信度、质量评分、问题标签和小片段导出")
    st.write("- 训练报告：整体概览、重点问题、后续训练计划")
    st.write("- 大模型教练反馈：可选接入 Qwen 或智谱AI，把结构化结果转成自然语言训练建议")

    st.markdown("**质量分析规则**")
    st.write("- 击球点高度：手腕相对肩部高度")
    st.write("- 挥拍速度：击球片段内手腕速度峰值")
    st.write("- 回位表现：击球后脚踝中心偏移")
    st.write("- 重心稳定：髋部移动抖动")
    st.write("- 脚步启动：击球前后脚步路径长度")

    st.markdown("**当前局限**")
    st.write("- 远端小人、遮挡、低清晰度视频会影响姿态检测")
    st.write("- 击球事件目前基于手腕速度峰值，无法保证等同真实球拍触球瞬间")
    st.write("- 手动四点标定依赖用户输入，球场线不清晰时映射仍会有误差")
    st.write("- 动作分类模型仍依赖现有姿态序列数据，低置信度片段需要人工复核")

    st.markdown("**下一步方向**")
    st.write("- 自动检测球场线，减少手动四点标定成本")
    st.write("- 对比更强姿态模型，提高远端球员关键点稳定性")
    st.write("- 重新构建单拍片段数据集，训练更适合逐拍识别的动作分类模型")


def build_markdown_report(report):
    lines = [
        "# 羽动智练训练报告",
        "",
        f"- 输入来源：{report.get('source')}",
        f"- 整体预测动作：{report.get('predicted_action')}",
        f"- 整体置信度：{report.get('confidence')}",
        f"- 姿态检测率：{report.get('motion_summary', {}).get('detection_rate')}",
        f"- 疑似击球数：{len(report.get('hit_events', []))}",
        "",
        "## 每拍动作识别",
        "",
    ]
    for event in report.get("shot_events", []):
        lines.extend(
            [
                f"### 第 {event.get('index')} 拍",
                f"- 时间：{event.get('time_sec')}s",
                f"- 动作：{event.get('shot_action')}",
                f"- 置信度：{event.get('shot_confidence')}",
                f"- 质量评分：{event.get('quality_score')}（{event.get('quality_level')}）",
                f"- 主要问题：{'；'.join(event.get('quality_issues', []))}",
                f"- 建议：{'；'.join(event.get('quality_advice', []))}",
                "",
            ]
        )

    coach = report.get("coach_report", {})
    if report.get("llm_coach_report"):
        lines.extend(["", "## 大模型教练反馈", "", report["llm_coach_report"], ""])
    if report.get("llm_coach_segments"):
        lines.extend(["", "## 大模型分段小结", ""])
        for segment in report["llm_coach_segments"]:
            lines.extend(
                [
                    f"### 第 {segment.get('index')} 组（拍次 {segment.get('range')}）",
                    "",
                    segment.get("content", ""),
                    "",
                ]
            )
    if report.get("llm_coach_error"):
        lines.extend(["", "## 大模型教练反馈错误", "", report["llm_coach_error"], ""])
    lines.extend(["## 本次概览", ""])
    lines.extend(f"- {item}" for item in coach.get("highlights", []))
    lines.extend(["", "## 重点问题", ""])
    lines.extend(f"- {item}" for item in coach.get("focus", []))
    lines.extend(["", "## 后续训练计划", ""])
    lines.extend(f"- {item}" for item in coach.get("training_plan", []))
    return "\n".join(lines).encode("utf-8")


def aggregate_predictions(windows, aggregate_probs, topk, num_classes, mode):
    if aggregate_probs is not None and mode == "平均整段":
        return topk_from_probs(aggregate_probs, topk=topk)

    if not windows:
        if aggregate_probs is None:
            return []
        return topk_from_probs(aggregate_probs, topk=topk)

    if mode == "最高置信片段":
        best_window = max(windows, key=lambda item: item["top_predictions"][0][1])
        return best_window["top_predictions"][:topk]

    if mode == "多数投票":
        scores = np.zeros(num_classes, dtype=np.float32)
        for window in windows:
            label, confidence = window["top_predictions"][0]
            scores[label] += confidence
        if np.sum(scores) > 0:
            scores = scores / np.sum(scores)
        return topk_from_probs(scores, topk=topk)

    return topk_from_probs(aggregate_probs, topk=topk)


def effective_pose_fps(sampled_indices, video_fps):
    if sampled_indices is None or len(sampled_indices) < 2:
        return float(video_fps or 30.0)
    frame_steps = np.diff(np.asarray(sampled_indices, dtype=np.float32))
    mean_step = float(np.mean(frame_steps[frame_steps > 0])) if np.any(frame_steps > 0) else 1.0
    return float(video_fps or 30.0) / max(mean_step, 1.0)


def generate_llm_report_compatible(report, provider, api_key, base_url, model, timeout, max_shots):
    kwargs = {
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
    }
    parameters = inspect.signature(generate_llm_coach_report).parameters
    if "timeout" in parameters:
        kwargs["timeout"] = timeout
    if "max_shots" in parameters:
        kwargs["max_shots"] = max_shots
    return generate_llm_coach_report(report, **kwargs)


def generate_segmented_llm_report_compatible(
    report,
    provider,
    api_key,
    base_url,
    model,
    timeout,
    shots_per_group,
    max_groups,
):
    generator = getattr(llm_coach_module, "generate_segmented_llm_coach_report", None)
    if generator is None:
        raise RuntimeError("当前大模型模块还没有加载全程分段总结函数，请重启 Streamlit 后再试。")

    kwargs = {
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
    }
    parameters = inspect.signature(generator).parameters
    if "timeout" in parameters:
        kwargs["timeout"] = timeout
    if "shots_per_group" in parameters:
        kwargs["shots_per_group"] = shots_per_group
    if "max_groups" in parameters:
        kwargs["max_groups"] = max_groups
    return generator(report, **kwargs)


def run_analysis(
    input_mode,
    uploaded_file,
    checkpoint_path,
    pose_model_path,
    max_frames,
    batch_size,
    conf_threshold,
    topk,
    use_cpu,
    window_size,
    stride,
    aggregation_mode,
    target_player,
    target_point,
    target_roi,
    target_bbox,
    court_corners,
    footwork_map_mode,
    llm_enabled,
    llm_provider,
    llm_api_key,
    llm_base_url,
    llm_model,
    llm_timeout,
    llm_max_shots,
    llm_mode="quick",
    llm_shots_per_group=8,
    llm_max_groups=None,
):
    if uploaded_file is None:
        st.warning("请先选择文件。")
        return None

    model, checkpoint, label_names, device_name = cached_model(str(checkpoint_path), use_cpu)
    device = torch.device(device_name)
    annotated_video = None
    tracking_video = None

    if input_mode == "姿态文件":
        pose_seq = load_pose_from_upload(uploaded_file)
        source = uploaded_file.name
        windows, aggregate_probs = predict_windows(
            model,
            checkpoint,
            pose_seq,
            device,
            window_size=window_size,
            stride=stride,
            topk=min(3, topk),
        )
        top_predictions = aggregate_predictions(
            windows,
            aggregate_probs,
            topk,
            int(checkpoint.get("num_classes", 18)),
            aggregation_mode,
        )
        summary = compute_motion_summary(pose_seq, conf_threshold=conf_threshold)
        report = build_report(source, top_predictions, label_names, summary)
        report["hit_events"] = detect_hit_events(
            pose_seq,
            windows=windows,
            label_names=label_names,
            fps=30.0,
        )
        report["shot_events"] = classify_hit_events(
            model,
            checkpoint,
            pose_seq,
            report["hit_events"],
            label_names,
            device,
            fps=30.0,
            topk=3,
        )
        report["footwork_scores"] = compute_footwork_scores(pose_seq)
        report["coach_report"] = build_coach_report(report)
    else:
        video_path = save_uploaded_file(uploaded_file)
        source = video_path
        pose_seq, _, sampled_indices, video_fps = extract_pose_and_frames_from_video(
            video_path,
            pose_model_path,
            conf_threshold=conf_threshold,
            max_frames=max_frames,
            batch_size=batch_size,
            target_player=target_player,
            target_point=target_point,
            target_roi=target_roi,
            target_bbox=target_bbox,
        )
        windows, aggregate_probs = predict_windows(
            model,
            checkpoint,
            pose_seq,
            device,
            window_size=window_size,
            stride=stride,
            topk=min(3, topk),
        )
        top_predictions = aggregate_predictions(
            windows,
            aggregate_probs,
            topk,
            int(checkpoint.get("num_classes", 18)),
            aggregation_mode,
        )
        summary = compute_motion_summary(pose_seq, conf_threshold=conf_threshold)
        report = build_report(source, top_predictions, label_names, summary)
        analysis_fps = effective_pose_fps(sampled_indices, video_fps)
        report["hit_events"] = detect_hit_events(
            pose_seq,
            windows=windows,
            label_names=label_names,
            fps=analysis_fps,
        )
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
        report["footwork_scores"] = compute_footwork_scores(pose_seq)
        report["coach_report"] = build_coach_report(report)
        annotated_video = ANNOTATED_DIR / f"{video_path.stem}_annotated.mp4"
        tracking_video = ANNOTATED_DIR / f"{video_path.stem}_tracking.mp4"
        status_text = f"Target: {target_player}"
        if target_point is not None:
            status_text += f" ({target_point[0]:.2f}, {target_point[1]:.2f})"
        if target_roi is not None:
            status_text += " ROI"
        if target_bbox is not None:
            status_text += " Box"
        if court_corners is not None:
            status_text += " Court"
        write_full_length_annotated_video(
            video_path,
            pose_seq,
            sampled_indices,
            windows,
            label_names,
            annotated_video,
            conf_threshold=conf_threshold,
            hit_events=report.get("shot_events") or report["hit_events"],
            status_text=status_text,
        )
        write_full_length_tracking_video(
            video_path,
            pose_seq,
            sampled_indices,
            windows,
            label_names,
            tracking_video,
            conf_threshold=conf_threshold,
            hit_events=report.get("shot_events") or report["hit_events"],
            status_text=status_text,
            court_corners=court_corners,
            footwork_map_mode=footwork_map_mode,
        )
        shot_clip_dir = SHOT_CLIP_DIR / video_path.stem
        report["shot_events"] = write_shot_clips(video_path, report["shot_events"], shot_clip_dir)

    report["windows"] = format_windows(windows, label_names)
    report["annotated_video"] = str(annotated_video) if annotated_video else None
    report["tracking_video"] = str(tracking_video) if tracking_video else None
    report["runtime"] = {
        "device": device_name,
        "checkpoint": str(checkpoint_path),
        "pose_model": str(pose_model_path) if input_mode == "视频文件" else None,
        "input_mode": input_mode,
        "aggregation_mode": aggregation_mode,
        "target_player": target_player,
        "target_point": target_point,
        "target_roi": target_roi,
        "target_bbox": target_bbox,
        "court_corners": court_corners,
        "footwork_map_mode": footwork_map_mode,
        "max_frames": max_frames,
        "full_frame_analysis": max_frames is None,
        "window_size": window_size,
        "stride": stride,
        "llm_enabled": llm_enabled,
        "llm_mode": llm_mode if llm_enabled else None,
        "llm_shots_per_group": llm_shots_per_group if llm_enabled else None,
        "llm_max_groups": llm_max_groups if llm_enabled else None,
    }
    if llm_enabled:
        try:
            if llm_mode == "segmented":
                segmented_result = generate_segmented_llm_report_compatible(
                    report,
                    provider=llm_provider,
                    api_key=llm_api_key,
                    base_url=llm_base_url,
                    model=llm_model,
                    timeout=llm_timeout,
                    shots_per_group=llm_shots_per_group,
                    max_groups=llm_max_groups,
                )
                report["llm_coach_mode"] = "segmented"
                report["llm_coach_report"] = segmented_result.get("summary", "")
                report["llm_coach_segments"] = segmented_result.get("segments", [])
            else:
                report["llm_coach_mode"] = "quick"
                report["llm_coach_report"] = generate_llm_report_compatible(
                    report,
                    provider=llm_provider,
                    api_key=llm_api_key,
                    base_url=llm_base_url,
                    model=llm_model,
                    timeout=llm_timeout,
                    max_shots=llm_max_shots,
                )
        except Exception as exc:
            report["llm_coach_error"] = str(exc)
    return report


def render_report(report):
    tab_overview, tab_video, tab_footwork, tab_report, tab_project = st.tabs(["总览", "标注视频", "步伐监测", "训练报告", "项目说明"])

    with tab_overview:
        st.subheader("分析结果")
        left, middle, right, fourth = st.columns(4)
        left.metric("预测动作", report["predicted_action"])
        middle.metric("置信度", f"{report['confidence']:.3f}")
        right.metric("检测率", f"{report['motion_summary']['detection_rate']:.3f}")
        fourth.metric("疑似击球", len(report.get("hit_events", [])))
        render_quality_summary(report)

        if report["confidence"] < 0.45:
            st.info("置信度较低时，通常说明长视频里混有多个动作、准备空档或相近动作。建议查看分段预测和标注视频。")

        top_rows = [
            {
                "label": item["label"],
                "动作": item["class_name"],
                "置信度": item["confidence"],
            }
            for item in report["top_predictions"]
        ]
        st.dataframe(top_rows, use_container_width=True, hide_index=True)

        summary = report["motion_summary"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("有效帧", f"{summary['valid_frames']}/{summary['frames']}")
        c2.metric("惯用侧估计", summary["dominant_side"])
        c3.metric("手腕峰值速度", f"{summary['max_wrist_speed']:.3f}")
        c4.metric("脚步移动量", f"{summary['footwork_distance']:.3f}")

        if report.get("shot_events"):
            st.subheader("每拍动作识别")
            st.dataframe(format_shot_events(report["shot_events"]), use_container_width=True, hide_index=True)

        if report.get("windows"):
            st.subheader("分段预测")
            st.dataframe(report["windows"], use_container_width=True, hide_index=True)

    with tab_video:
        if report.get("tracking_video"):
            tracking_path = Path(report["tracking_video"])
            if tracking_path.exists():
                st.subheader("同步标注 + 步伐热力图")
                tracking_bytes = tracking_path.read_bytes()
                st.video(tracking_bytes, format="video/mp4")
                st.download_button(
                    "下载同步监测视频",
                    tracking_bytes,
                    file_name=tracking_path.name,
                    mime="video/mp4",
                )

        if report.get("annotated_video"):
            annotated_path = Path(report["annotated_video"])
            if annotated_path.exists():
                st.subheader("原标注视频")
                video_bytes = annotated_path.read_bytes()
                st.video(video_bytes, format="video/mp4")
                st.download_button(
                    "下载标注视频",
                    video_bytes,
                    file_name=annotated_path.name,
                    mime="video/mp4",
                )
        if report.get("shot_events"):
            st.subheader("每拍动作识别")
            st.dataframe(format_shot_events(report["shot_events"]), use_container_width=True, hide_index=True)
            for event in report["shot_events"]:
                clip_path = event.get("clip_video")
                if not clip_path:
                    continue
                clip_path = Path(clip_path)
                if not clip_path.exists():
                    continue
                title = f"第 {event.get('index')} 拍 | {event.get('shot_action')} | {event.get('shot_confidence', 0):.2f}"
                with st.expander(title):
                    q1, q2 = st.columns(2)
                    q1.metric("质量评分", event.get("quality_score", "-"))
                    q2.metric("质量等级", event.get("quality_level", "-"))
                    if event.get("quality_issues"):
                        st.markdown("**问题提示**")
                        for item in event.get("quality_issues", []):
                            st.write(f"- {item}")
                    if event.get("quality_advice"):
                        st.markdown("**训练建议**")
                        for item in event.get("quality_advice", []):
                            st.write(f"- {item}")
                    if event.get("quality_metrics"):
                        st.dataframe(
                            [{"指标": key, "数值": value} for key, value in event["quality_metrics"].items()],
                            use_container_width=True,
                            hide_index=True,
                        )
                    clip_bytes = clip_path.read_bytes()
                    st.video(clip_bytes, format="video/mp4")
                    st.download_button(
                        "下载该拍片段",
                        clip_bytes,
                        file_name=clip_path.name,
                        mime="video/mp4",
                        key=f"download_clip_{event.get('index')}_{clip_path.name}",
                    )
        elif report.get("hit_events"):
            st.subheader("疑似击球事件")
            st.dataframe(report["hit_events"], use_container_width=True, hide_index=True)

    with tab_footwork:
        st.subheader("步伐监测指标")
        st.caption("实时热力图已放在“标注视频”面板的同步监测视频中；这里保留本次移动表现的汇总指标。")
        fig = render_radar_chart(report.get("footwork_scores", {}))
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        metric_names = {
            "movement": "移动量",
            "explosiveness": "启动爆发",
            "stability": "重心稳定",
            "recovery": "回位能力",
            "coverage": "覆盖范围",
            "balance": "步幅平衡",
        }
        rows = [
            {"指标": metric_names.get(key, key), "得分": round(value, 1)}
            for key, value in report.get("footwork_scores", {}).items()
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)

    with tab_report:
        st.subheader("训练报告")
        coach = report.get("coach_report", {})
        if report.get("llm_coach_report"):
            st.markdown("**大模型教练反馈**")
            st.markdown(report["llm_coach_report"])
        if report.get("llm_coach_segments"):
            with st.expander("查看分段教练小结", expanded=False):
                for segment in report["llm_coach_segments"]:
                    st.markdown(f"**第 {segment.get('index')} 组（拍次 {segment.get('range')}）**")
                    st.markdown(segment.get("content", ""))
        if report.get("llm_coach_error"):
            st.warning(f"大模型教练反馈生成失败：{report['llm_coach_error']}")
            st.caption("本地规则报告已正常生成。若是 read operation timed out，可提高“大模型超时秒数”、减少“发送给大模型的最多拍数”，或稍后重试。")
        st.markdown("**本次概览**")
        for item in coach.get("highlights", []):
            st.write(f"- {item}")
        st.markdown("**重点问题**")
        for item in coach.get("focus", []):
            st.write(f"- {item}")
        st.markdown("**后续训练计划**")
        for item in coach.get("training_plan", []):
            st.write(f"- {item}")
        st.markdown("**基础建议**")
        for item in report["training_advice"]:
            st.write(f"- {item}")
        st.download_button(
            "下载 Markdown 报告",
            build_markdown_report(report),
            file_name="badminton_training_report.md",
            mime="text/markdown",
        )

    with tab_project:
        render_project_overview()

    report_json = json.dumps(report, indent=2, ensure_ascii=False)
    st.download_button(
        "下载报告 JSON",
        report_json.encode("utf-8"),
        file_name="badminton_report.json",
        mime="application/json",
    )

    with st.expander("完整 JSON"):
        st.code(report_json, language="json")


def main():
    apply_theme()
    render_app_header()
    render_workflow_strip()

    with st.sidebar:
        st.header("配置")
        checkpoint_path = Path(st.text_input("分类模型", value=str(DEFAULT_CHECKPOINT)))
        pose_model_path = Path(st.text_input("姿态模型", value=str(DEFAULT_POSE_MODEL)))
        input_mode = st.radio("输入类型", ["视频文件", "姿态文件"], horizontal=True)
        preset = st.selectbox("分析精度", ["自适应最佳", "快速", "均衡", "细致", "完整逐帧"], index=0)
        preset_values = {
            "自适应最佳": {"max_frames": None, "window_size": 32, "stride": 8},
            "快速": {"max_frames": 300, "window_size": 64, "stride": 32},
            "均衡": {"max_frames": 600, "window_size": 32, "stride": 16},
            "细致": {"max_frames": 1200, "window_size": 24, "stride": 8},
            "完整逐帧": {"max_frames": None, "window_size": 24, "stride": 4},
        }[preset]
        if preset_values["max_frames"] is None:
            max_frames = None
            st.info("当前模式会分析原视频所有帧，时间最长，但标注最细。")
        else:
            max_frames = st.slider("最大抽帧数", min_value=60, max_value=1800, value=preset_values["max_frames"], step=60)
        batch_size = st.slider("姿态批大小", min_value=4, max_value=64, value=32, step=4)
        conf_threshold = st.slider("检测阈值", min_value=0.1, max_value=0.8, value=0.3, step=0.05)
        target_player_label = st.selectbox(
            "跟踪球员",
            ["近端球员", "远端球员", "画面左侧", "画面右侧", "自定义目标点", "首帧目标框", "最大框"],
            index=0,
            help="多人画面里用于固定跟踪目标，避免骨架和步伐热力图跳到对方球员身上。",
        )
        target_player = {
            "近端球员": "near",
            "远端球员": "far",
            "画面左侧": "left",
            "画面右侧": "right",
            "自定义目标点": "custom",
            "首帧目标框": "manual_box",
            "最大框": "largest",
        }[target_player_label]
        target_point = None
        target_bbox = None
        if target_player == "custom":
            target_x = st.slider("目标点 X(画面百分比)", min_value=0, max_value=100, value=65, step=1)
            target_y = st.slider("目标点 Y(画面百分比)", min_value=0, max_value=100, value=55, step=1)
            target_point = (target_x / 100.0, target_y / 100.0)
        if target_player == "manual_box":
            st.caption("上传视频后，页面会显示首帧框选区。直接框住目标球员即可。")
        roi_label = st.selectbox(
            "分析区域 ROI",
            ["全画面", "上半场", "下半场", "左半场", "右半场", "左上区域", "右上区域", "左下区域", "右下区域", "自定义矩形"],
            index=0,
            help="只在指定画面区域内优先选择球员，可减少误跟踪到对方或裁判观众。",
        )
        roi_presets = {
            "全画面": None,
            "上半场": (0.0, 0.0, 1.0, 0.55),
            "下半场": (0.0, 0.45, 1.0, 1.0),
            "左半场": (0.0, 0.0, 0.55, 1.0),
            "右半场": (0.45, 0.0, 1.0, 1.0),
            "左上区域": (0.0, 0.0, 0.58, 0.58),
            "右上区域": (0.42, 0.0, 1.0, 0.58),
            "左下区域": (0.0, 0.42, 0.58, 1.0),
            "右下区域": (0.42, 0.42, 1.0, 1.0),
        }
        target_roi = roi_presets.get(roi_label)
        if roi_label == "自定义矩形":
            roi_x1 = st.slider("ROI 左边界 %", min_value=0, max_value=100, value=45, step=1)
            roi_y1 = st.slider("ROI 上边界 %", min_value=0, max_value=100, value=35, step=1)
            roi_x2 = st.slider("ROI 右边界 %", min_value=0, max_value=100, value=100, step=1)
            roi_y2 = st.slider("ROI 下边界 %", min_value=0, max_value=100, value=75, step=1)
            x1, x2 = sorted((roi_x1 / 100.0, roi_x2 / 100.0))
            y1, y2 = sorted((roi_y1 / 100.0, roi_y2 / 100.0))
            target_roi = (x1, y1, x2, y2)
        calibration_mode = st.selectbox("球场标定", ["自动轨迹范围", "手动四点标定"], index=0)
        court_corners = None
        if calibration_mode == "手动四点标定":
            st.caption("按画面百分比输入目标半场四角：上左、上右、下左、下右。用于把步伐热力图映射到固定半场面板。")
            tlx = st.slider("上左 X %", 0, 100, 28, 1)
            tly = st.slider("上左 Y %", 0, 100, 35, 1)
            trx = st.slider("上右 X %", 0, 100, 75, 1)
            try_ = st.slider("上右 Y %", 0, 100, 35, 1)
            blx = st.slider("下左 X %", 0, 100, 20, 1)
            bly = st.slider("下左 Y %", 0, 100, 85, 1)
            brx = st.slider("下右 X %", 0, 100, 92, 1)
            bry = st.slider("下右 Y %", 0, 100, 85, 1)
            court_corners = {
                "top_left": (tlx / 100.0, tly / 100.0),
                "top_right": (trx / 100.0, try_ / 100.0),
                "bottom_left": (blx / 100.0, bly / 100.0),
                "bottom_right": (brx / 100.0, bry / 100.0),
            }
        footwork_map_label = st.selectbox(
            "步伐映射方式",
            ["画面坐标", "自动轨迹范围"],
            index=0,
            help="画面坐标更稳定，不会被少量异常脚点拉飞；自动轨迹范围会把当前轨迹拉伸到半场，适合看局部移动。手动四点标定开启后会优先使用球场映射。",
        )
        footwork_map_mode = "auto" if footwork_map_label == "自动轨迹范围" else "image"
        topk = st.slider("Top-K", min_value=1, max_value=10, value=5)
        window_size = st.slider("滑窗长度", min_value=8, max_value=96, value=preset_values["window_size"], step=8)
        stride = st.slider("滑窗步长", min_value=4, max_value=64, value=preset_values["stride"], step=4)
        aggregation_mode = st.selectbox("置信度聚合", ["平均整段", "最高置信片段", "多数投票"], index=1)
        use_cpu = st.checkbox("使用 CPU", value=False)
        st.divider()
        llm_enabled = st.checkbox("启用大模型教练反馈", value=False)
        llm_provider_label = st.selectbox("大模型服务", ["Qwen", "智谱AI"], index=0)
        llm_provider = "qwen" if llm_provider_label == "Qwen" else "zhipu"
        llm_defaults = provider_defaults(llm_provider)
        llm_model = st.text_input("大模型名称", value=llm_defaults["model"])
        llm_base_url = st.text_input("接口 Base URL", value=llm_defaults["base_url"])
        llm_api_key = st.text_input("API Key", value="", type="password", help="也可以用环境变量配置：DASHSCOPE_API_KEY / QWEN_API_KEY / ZHIPUAI_API_KEY")
        llm_timeout = st.slider("大模型超时秒数", min_value=30, max_value=240, value=120, step=30)
        llm_mode_label = st.selectbox("大模型反馈模式", ["全程分段总结", "快速总结"], index=0)
        llm_mode = "segmented" if llm_mode_label == "全程分段总结" else "quick"
        llm_max_shots = 5
        llm_shots_per_group = 8
        llm_max_groups = None
        if llm_mode == "quick":
            llm_max_shots = st.slider("发送给大模型的最多拍数", min_value=3, max_value=12, value=5, step=1)
            st.caption("快速总结只发送少量样本，适合快速验证接口是否可用。")
        else:
            llm_shots_per_group = st.slider("每组发送拍数", min_value=4, max_value=15, value=8, step=1)
            limit_groups = st.checkbox("限制发送分组数", value=False)
            if limit_groups:
                llm_max_groups = st.slider("最多发送分组", min_value=1, max_value=30, value=10, step=1)
            st.caption("全程分段总结会覆盖检测到的所有击球；视频越长，请求次数越多，耗时和 API 成本也会增加。")
        st.caption("想尽量不漏击球，请用“自适应最佳”或“完整逐帧”；想更快出结果，再切到快速/均衡。")

    render_upload_intro(input_mode, target_player)

    if input_mode == "视频文件":
        uploaded_file = st.file_uploader("上传视频", type=["mp4", "mov", "avi", "mkv", "mpeg"])
    else:
        uploaded_file = st.file_uploader("上传姿态文件", type=["npy"])

    if uploaded_file is not None and input_mode == "视频文件":
        preview_video_path = save_uploaded_file(uploaded_file)
        st.subheader("原始视频")
        st.video(uploaded_file)
        if target_player == "manual_box":
            target_bbox = render_target_bbox_selector(preview_video_path, target_bbox)

    if st.button("开始分析", type="primary", use_container_width=True):
        if not checkpoint_path.exists():
            st.error(f"分类模型不存在：{checkpoint_path}")
            return
        if input_mode == "视频文件" and not pose_model_path.exists():
            st.error(f"姿态模型不存在：{pose_model_path}")
            return
        if input_mode == "视频文件" and target_player == "manual_box" and target_bbox is None:
            st.error("请先在首帧上框选目标球员，再开始分析。")
            return

        with st.spinner("正在分析，长视频需要一点时间..."):
            try:
                report = run_analysis(
                    input_mode,
                    uploaded_file,
                    checkpoint_path,
                    pose_model_path,
                    max_frames,
                    batch_size,
                    conf_threshold,
                    topk,
                    use_cpu,
                    window_size,
                    stride,
                    aggregation_mode,
                    target_player,
                    target_point,
                    target_roi,
                    target_bbox,
                    court_corners,
                    footwork_map_mode,
                    llm_enabled,
                    llm_provider,
                    llm_api_key,
                    llm_base_url,
                    llm_model,
                    llm_timeout,
                    llm_max_shots,
                    llm_mode,
                    llm_shots_per_group,
                    llm_max_groups,
                )
            except Exception as exc:
                st.exception(exc)
                return

        if report is not None:
            render_report(report)
    else:
        render_empty_dashboard()
        render_project_overview()


if __name__ == "__main__":
    main()
