# 羽动智练 Badminton AI Coach

羽动智练是一个面向羽毛球训练复盘的 AI 分析项目。当前仓库同时包含 Python 后端推理服务、独立 Web 前端、Streamlit 原型和微信小程序端，核心能力是上传训练或比赛视频后进行人体姿态提取、动作分类、击球事件检测、步伐分析、标注视频生成和 AI 教练反馈。

## 当前项目状态

项目已经从早期的姿态提取与模型训练脚本，发展为一个可端到端演示的应用：

- 后端：FastAPI 服务，提供视频预检、视频分析、历史记录、媒体播放、账号登录注册、微信小程序登录和 AI 教练问答接口。
- 模型：默认使用 `yolov8s-pose.pt` 做人体姿态估计，使用 `models/pose_sequence_tcn_gru.pt` 做羽毛球动作序列分类。
- Web 前端：`frontend/` 是独立 HTML/CSS/JS 工作台，可通过 FastAPI 静态服务访问。
- Streamlit 原型：`src/app/streamlit_app.py` 仍保留，用于快速测试视频分析流程。
- 微信小程序：`badminton_agent_wx/` 已包含登录、训练、分析、AI 教练、历史、个人中心等页面。
- 数据与输出：`data/` 保存特征和用户数据库，`outputs/` 保存上传视频、标注视频、片段、历史记录等运行产物。

## 目录结构

```text
badminton-agent/
├─ configs/                    # 数据集配置
│  └─ dataset.yaml
├─ data/                       # 本地数据与特征
│  ├─ raw_videos/              # 原始视频数据，按需放置
│  ├─ pose_features/           # YOLOv8-Pose 提取后的姿态序列
│  ├─ visualizations/          # 姿态可视化结果
│  ├─ badminton_features.json  # 手工/工程特征结果
│  └─ users.db                 # 用户账号数据库 SQLite
├─ frontend/                   # 独立 Web 前端工作台
│  ├─ index.html
│  ├─ styles.css
│  ├─ app.js
│  └─ assets/
├─ badminton_agent_wx/         # 微信小程序端
│  ├─ miniprogram/
│  │  ├─ app.js / app.json / app.wxss
│  │  ├─ utils/api.js
│  │  └─ pages/
│  │     ├─ login/             # 登录/注册/微信登录
│  │     ├─ training/          # 训练视频上传与分析入口
│  │     ├─ analysis/          # 分析结果展示
│  │     ├─ coach/             # AI 教练问答
│  │     ├─ history/           # 历史记录
│  │     └─ profile/           # 个人中心
│  └─ cloudfunctions/          # 微信云开发 quickstart 函数，目前不是主业务后端
├─ models/                     # 动作分类模型、标签和评估结果
│  ├─ pose_sequence_tcn_gru.pt
│  ├─ pose_sequence_labels.json
│  ├─ hierarchical*/
│  └─ evaluation/
├─ outputs/                    # 运行输出
│  ├─ api_uploads/             # API 上传的视频
│  ├─ api_annotated/           # 生成的完整标注视频
│  ├─ api_previews/            # 视频预览图
│  ├─ api_shot_clips/          # 逐拍复盘片段
│  ├─ avatars/                 # 用户头像
│  └─ history.db               # 训练历史 SQLite
├─ src/
│  ├─ api/
│  │  ├─ server.py             # FastAPI 主服务
│  │  └─ auth.py               # 用户、Token、微信登录与头像接口
│  ├─ app/
│  │  └─ streamlit_app.py      # Streamlit 测试页面
│  ├─ pose_estimation/         # 姿态提取与可视化
│  ├─ feature_engineering/     # 羽毛球专项特征提取
│  ├─ action_classification/   # 动作分类模型训练脚本
│  └─ inference/               # 视频推理、规则报告、LLM 教练
├─ requirements.txt
├─ test_setup.py
├─ yolov8s-pose.pt
└─ README.md
```

## 核心功能

### 视频分析

上传视频后，后端会执行以下流程：

1. 视频质量预检：分辨率、时长、清晰度、人物检测、人物大小和场景类型。
2. 姿态估计：使用 YOLOv8-Pose 提取人体关键点。
3. 球员选择与跟踪：支持近端、远端、左侧、右侧、最大人物、首帧框选和 ROI 限定。
4. 动作分类：基于姿态序列模型识别羽毛球动作类型。
5. 击球事件检测：识别疑似击球点并对逐拍片段分类。
6. 步伐分析：生成脚步轨迹、热力图和步伐评分。
7. 质量评估：输出动作质量、问题标签和训练建议。
8. 标注视频：生成带骨架、动作标签、置信度和击球事件标记的视频。
9. 历史记录：将分析结果写入 `outputs/history.db`，供 Web 和小程序查看。

### AI 教练

项目支持本地规则报告和可选的大模型教练反馈：

- Qwen / DashScope OpenAI-compatible 接口
- 智谱 AI GLM OpenAI-compatible 接口
- 支持普通问答和流式问答接口
- 可结合当前训练报告进行追问
- API Key 不应提交到 Git，建议放在 `.env`

### 账号体系

后端提供本地账号和微信小程序登录：

- 用户名/密码注册与登录
- Token 会话认证
- 头像上传
- 个人资料更新
- 微信小程序 `code2session` 登录
- 微信绑定/解绑

如果没有配置 `WECHAT_SECRET`，后端会使用开发模式 openid，方便本地联调。

## 后端接口概览

FastAPI 入口：`src/api/server.py`

常用接口：

```text
GET    /api/health
POST   /api/precheck
POST   /api/frame
POST   /api/analyze
GET    /api/history
GET    /api/history/{session_id}
DELETE /api/history/{session_id}
GET    /api/media/{filename}
POST   /api/coach/chat
POST   /api/coach/chat/stream
```

认证接口：

```text
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/wechat/miniprogram-login
GET    /api/auth/me
POST   /api/auth/logout
PUT    /api/auth/profile
POST   /api/auth/avatar
GET    /api/auth/avatar/{filename}
POST   /api/auth/change-password
POST   /api/auth/wechat/bind
POST   /api/auth/wechat/unbind
POST   /api/auth/logout-all
```

## 快速开始

### 1. 安装依赖

建议使用 Python 3.10+，并在虚拟环境中安装依赖：

```bash
cd D:\badminton-agent
pip install -r requirements.txt
```

主要依赖包括：FastAPI、Uvicorn、OpenCV、PyTorch、Ultralytics YOLO、Streamlit、scikit-learn 等。

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，按需填写大模型和微信配置：

```env
DASHSCOPE_API_KEY=
QWEN_API_KEY=
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus

ZHIPUAI_API_KEY=
ZHIPU_API_KEY=
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4-plus

WECHAT_APPID=wxa62a3ae0f2c7c0f4
WECHAT_SECRET=
```

`.env` 已加入 `.gitignore`，不要提交真实 API Key。

### 3. 启动 FastAPI 后端

本机 Web 调试：

```bash
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000
```

手机或微信小程序局域网调试：

```bash
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

启动后访问：

```text
http://127.0.0.1:8000/frontend/
```

健康检查：

```text
http://127.0.0.1:8000/api/health
```

### 4. 启动 Streamlit 原型

```bash
python -m streamlit run src/app/streamlit_app.py --server.port 8501 --server.address 127.0.0.1
```

访问：

```text
http://127.0.0.1:8501
```

### 5. 命令行推理

使用姿态序列文件：

```bash
python src/inference/predict_video.py --pose-file data/pose_features/14_Smash/example_pose.npy
```

直接分析视频：

```bash
python src/inference/predict_video.py --video demo.mp4 --output outputs/demo_report.json
```

### 6. 微信小程序调试

小程序目录：

```text
D:\badminton-agent\badminton_agent_wx
```

使用微信开发者工具导入该目录。当前小程序页面包括：

```text
pages/login/login
pages/training/training
pages/analysis/analysis
pages/coach/coach
pages/history/history
pages/profile/profile
```

调试前需要修改：

```text
badminton_agent_wx/miniprogram/app.js
```

将 `API_BASE` 改成你电脑的局域网地址，例如：

```js
const API_BASE = 'http://192.168.1.5:8000';
```

同时后端必须用 `0.0.0.0:8000` 启动，并保证手机和电脑在同一 WiFi。微信开发者工具里当前 `urlCheck` 为 `false`，便于本地调试；正式发布时需要配置合法域名和 HTTPS。

## 模型与训练脚本

当前主要模型：

- `yolov8s-pose.pt`：人体姿态估计模型。
- `models/pose_sequence_tcn_gru.pt`：默认动作序列分类模型。
- `models/pose_sequence_labels.json`：动作类别标签。
- `models/hierarchical*/`：分层动作分类实验模型。
- `models/evaluation/`：混淆矩阵、分类报告和每类指标。

训练与数据处理脚本：

```bash
python src/pose_estimation/extract_pose.py
python src/pose_estimation/visualize_pose.py --samples 2
python src/feature_engineering/extract_features.py
python src/action_classification/train_pose_sequence_classifier.py
python src/action_classification/train_hierarchical_classifier.py
```

`test_setup.py` 用于验证 YOLOv8-Pose 环境，但其中数据集路径目前指向 `G:/VideoBadminton_Dataset/VideoBadminton_Dataset`，在新机器上需要改成实际数据集路径。

## 前端说明

### Web 前端

`frontend/` 是完整的单页 Web 工作台。推荐通过 FastAPI 访问：

```text
http://127.0.0.1:8000/frontend/
```

它会调用：

- `POST /api/precheck`
- `POST /api/frame`
- `POST /api/analyze`
- `GET /api/history`
- `POST /api/coach/chat`
- `POST /api/coach/chat/stream`

### 微信小程序

小程序复用 FastAPI 后端接口，主要通过：

```text
badminton_agent_wx/miniprogram/utils/api.js
```

封装请求、登录、注册、视频上传分析、历史记录和教练问答。当前云函数目录仍是微信云开发 quickstart，不是主要业务服务。

## 当前注意事项

- 仓库里已有 `data/users.db` 和 `outputs/history.db` 等本地运行数据，提交代码前需要确认是否要保留。
- 多个源码文件中的中文字符串在当前环境显示为乱码，功能逻辑仍可读，但后续建议统一保存为 UTF-8。
- `.env` 中的真实 Key 不要提交。
- 小程序本地调试依赖局域网 IP，换网络后要更新 `API_BASE`。
- 上传视频分析会生成较多输出文件，主要位于 `outputs/api_*` 目录。
- `yolov8s-pose.pt` 和模型权重较大，若迁移仓库需确认是否使用 Git LFS 或外部下载方式。

## 后续建议

- 统一清理中文编码问题，保证 README、前端文案、后端错误信息均为 UTF-8。
- 将小程序 `API_BASE` 改为环境化配置，避免手动改源码。
- 梳理 `outputs/`、`data/*.db`、模型权重是否应纳入版本控制。
- 为 FastAPI 接口补充 OpenAPI 使用说明和示例请求。
- 为视频分析流程增加更小的 sample video 和 smoke test。
- 小程序正式发布前配置 HTTPS 域名、微信 AppSecret 和隐私合规说明。
