# Badminton AI Coach

<p align="center">
  <a href="./README.md"><img src="https://img.shields.io/badge/Language-Chinese-2ea44f?style=for-the-badge" alt="Chinese README"></a>
  <a href="./README_EN.md"><img src="https://img.shields.io/badge/Language-English-0969da?style=for-the-badge" alt="English README"></a>
  <img src="https://img.shields.io/badge/Web-FastAPI%20%2B%20HTML-14b8a6?style=for-the-badge" alt="Web">
  <img src="https://img.shields.io/badge/Mini%20Program-WeChat-07c160?style=for-the-badge" alt="WeChat Mini Program">
</p>

Badminton AI Coach is an AI-powered badminton training review system. It analyzes training or match videos, detects human pose keypoints, classifies badminton actions, extracts shot events, generates footwork heatmaps, creates training reports, and provides an AI coach experience across the web app and WeChat mini program.

The goal is to help badminton beginners, campus clubs, and amateur players get visual, data-driven, and personalized training feedback without relying on long-term one-on-one coaching.

## Demo

<p align="center">
  <img src="./badminton_from_2s_to_end.gif" alt="Badminton AI Coach video analysis demo" width="920">
</p>

The demo shows the workflow from video upload to annotated review, action recognition, and footwork heatmap generation.

## Highlights

- Upload a training or match video and analyze body keypoints, shot actions, and footwork movement.
- Support both close-range training clips and long-distance match footage.
- Generate annotated videos with pose skeletons, action labels, confidence scores, and shot events.
- Visualize target-player movement with a half-court footwork heatmap.
- Show each shot on an interactive timeline with timestamp, action type, confidence, and quality score.
- Generate training reports covering action quality, footwork, center-of-gravity stability, and wrist power.
- Provide an AI coach that can answer follow-up questions based on the latest training report.
- Connect the web account with the WeChat mini program for mobile access and history tracking.

## Web App

The web app is the main training review interface. It is designed for desktop-based video analysis, annotated playback, and report review.

### Real-Time Training Detection

- Upload badminton training or match videos.
- Run video quality checks before analysis.
- Track a selected target player to reduce multi-player tracking errors.
- Generate annotated videos, footwork heatmaps, and shot timelines.
- Use optimized long-distance match mode for faster preview generation.

### Action Analysis

- Display the main detected action and overall quality score.
- Evaluate swing fluency, hit-point accuracy, body coordination, footwork movement, wrist power, and center-of-gravity stability.
- Show detection history for reviewing each recognized shot.

### Training Report

- Summarize training duration, total actions, best action, and total analyzed frames.
- Provide an ability radar chart and prioritized issues.
- Generate follow-up training suggestions.
- Export the training report.

### AI Coach

- Answer general badminton questions.
- Continue the conversation based on the current training report.
- Support Qwen by default and keep a Zhipu AI provider option.
- Clean generated responses for a more product-ready reading experience.

### System Settings

- Support Chinese, English, Japanese, Korean, and Bahasa Indonesia.
- Support web login and WeChat mini program account binding.
- Hide complex model parameters in the delivery-oriented interface so end users can use the recommended defaults directly.

## WeChat Mini Program

The WeChat mini program is designed for mobile usage. Players can upload videos, check history, ask the AI coach, and bind their web account.

Main pages:

- Training: select or record a video and submit it for backend analysis.
- Analysis: view action results, scores, and training feedback.
- AI Coach: ask questions about badminton technique, footwork, training plans, and match review.
- Profile: view training data, history, language settings, and account binding status.

Account binding workflow:

1. Open System Settings in the web app.
2. Click Bind WeChat to generate a 6-digit binding code.
3. Open the Profile page in the mini program.
4. Tap Bind Web Account and enter the code.
5. After confirmation, the web app and mini program share the same account identity.

## Screenshots

### Web App

The training page provides shooting suggestions and video quality checks before backend analysis.

<p align="center">
  <img src="./docs/images/web/a4350beb-58f5-408a-ac12-7dbdc8accd59.png" alt="Web real-time training detection" width="920">
</p>

After analysis, the web app plays the annotated video and displays the half-court footwork heatmap, shot timeline, and live metrics.

<p align="center">
  <img src="./docs/images/web/6ae47972-f9a9-4c0f-ad03-78478759863c.png" alt="Web shot timeline and live metrics" width="920">
</p>

The annotated review overlays action labels, confidence scores, pose skeletons, and the footwork heatmap.

<p align="center">
  <img src="./docs/images/web/db082873-8659-469c-b01e-635b87382c72.png" alt="Web annotated video and footwork heatmap" width="920">
</p>

The AI coach can answer badminton technique, footwork, training plan, and match review questions with report context.

<p align="center">
  <img src="./docs/images/web/b18f1a22-76ad-4e70-93aa-5d6ccb7ecba9.png" alt="Web AI coach" width="920">
</p>

The settings page includes account binding, language switching, and delivery-oriented default configuration.

<p align="center">
  <img src="./docs/images/web/5e9d1bd5-5ef4-4957-bd85-b58bd964b22e.png" alt="Web settings" width="920">
</p>

### WeChat Mini Program

The mini program can bind to the same web account through a 6-digit code.

<p align="center">
  <img src="./docs/images/wechat/41d3b8ec12b4c9bae537efa3e9e1cb75.jpg" alt="Mini program bind web account" width="360">
</p>

After binding, the Profile page shows training data, history, language settings, and account actions.

<p align="center">
  <img src="./docs/images/wechat/c142b2d0e000befde040d6eb6c068dcc.jpg" alt="Mini program profile page" width="360">
</p>

The mobile AI coach provides quick badminton Q&A.

<p align="center">
  <img src="./docs/images/wechat/baa7aacc45dcc2df0b0e87bce30e6879.jpg" alt="Mini program AI coach" width="360">
</p>

The mini program supports multiple display languages.

<p align="center">
  <img src="./docs/images/wechat/aa18615bb4c5dfcd97637f413fcacc33.jpg" alt="Mini program language settings" width="360">
</p>

## Architecture

```text
badminton-agent/
├─ frontend/                  # Web app
├─ badminton_agent_wx/         # WeChat mini program
├─ src/
│  ├─ api/                     # FastAPI backend service
│  ├─ inference/               # Pose detection, action classification, video annotation
│  ├─ action_classification/   # Training and model code for action classification
│  ├─ court/                   # Court mapping and coordinate conversion
│  ├─ data/                    # Data writing utilities
│  └─ detection/               # Detection extensions
├─ models/                     # Action classification model files
├─ outputs/                    # Runtime outputs, ignored by default
├─ start_web.bat               # One-click Windows startup script
├─ requirements.txt            # Python dependencies
├─ .env.example                # Environment variable example
├─ README.md                   # Chinese README
└─ README_EN.md                # English README
```

## Tech Stack

- FastAPI for backend APIs and static media serving.
- OpenCV for video reading, frame processing, and annotated video generation.
- Ultralytics YOLOv8-Pose for human pose keypoint detection.
- PyTorch for pose-sequence action classification.
- TCN + GRU for badminton pose-sequence classification.
- SQLite for users, training history, and report records.
- Qwen / Zhipu AI for AI coach and training suggestion generation.
- WeChat mini program for mobile training and account binding.

## Quick Start

### Option 1: One-Click Startup on Windows

Double-click:

```text
start_web.bat
```

Then open:

```text
http://127.0.0.1:8000/frontend/
```

### Option 2: Manual Startup

```powershell
pip install -r requirements.txt
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000/frontend/
```

## Environment Variables

Copy `.env.example` to `.env` and fill in keys as needed:

```env
DASHSCOPE_API_KEY=your_qwen_key
ZHIPUAI_API_KEY=your_zhipuai_key
```

Without LLM API keys, core video analysis still works. AI coach and LLM-generated training suggestions will be limited.

## Model Files

Before running the app, make sure these files exist:

```text
models/pose_sequence_tcn_gru.pt
yolov8s-pose.pt
```

## Notes

- `.env`, runtime outputs, model debug artifacts, and user databases are not committed.
- Video analysis speed depends on GPU, video length, resolution, and FFmpeg availability.
- AI coach suggestions are for training reference only and do not replace professional medical or rehabilitation advice.
