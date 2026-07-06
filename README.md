# 羽动智练 - Badminton AI Coach

基于 YOLOv8-Pose 的羽毛球姿态分析与动作识别项目。

## 项目结构

```
badminton-agent/
├── configs/              # 配置文件
│   └── dataset.yaml      # 数据集配置
├── data/                 # 数据目录
│   ├── pose_features/    # 姿态关键点特征 (NPY)
│   └── visualizations/   # 可视化结果
├── src/                  # 源代码
│   ├── pose_estimation/  # 姿态估计
│   │   ├── extract_pose.py     # 批量提取姿态
│   │   └── visualize_pose.py   # 姿态可视化
│   ├── feature_engineering/    # 特征工程
│   │   └── extract_features.py # 羽毛球专项特征提取
│   └── action_classification/  # 动作分类（待实现）
├── models/               # 模型权重保存目录
├── notebooks/            # Jupyter 分析笔记本
├── requirements.txt      # 依赖
├── test_setup.py         # 环境验证
└── README.md             # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

YOLOv8s-Pose 模型会在首次运行时自动下载。

### 2. 验证环境（30 秒）

```bash
python test_setup.py
```

### 3. 提取姿态关键点

```bash
python src/pose_estimation/extract_pose.py
```

处理全部 7822 个视频，输出 `.npy` 文件到 `data/pose_features/`。

### 4. 可视化验证

```bash
python src/pose_estimation/visualize_pose.py --samples 2
```

### 5. 提取羽毛球专项特征

```bash
python src/feature_engineering/extract_features.py
```

输出 `data/badminton_features.json`。

### 6. 单视频/姿态文件推理

使用当前最佳姿态序列模型生成动作识别结果和训练建议：

```bash
python src/inference/predict_video.py --pose-file data/pose_features/14_Smash/example_pose.npy
```

也可以直接输入视频，脚本会先调用 YOLOv8-Pose 提取关键点：

```bash
python src/inference/predict_video.py --video demo.mp4 --output outputs/demo_report.json
```

输出包含预测动作、Top-K 置信度、姿态检测率、动作摘要和中文训练建议。

### 7. Streamlit 测试页面

```bash
python -m streamlit run src/app/streamlit_app.py --server.port 8501 --server.address 127.0.0.1
```

打开 `http://127.0.0.1:8501`，可上传视频或 `.npy` 姿态文件进行测试。
视频模式会生成带人体骨架、分段动作标签、置信度和疑似击球点标记的标注视频。
页面还会生成“同步标注 + 步伐热力图”视频：左侧是标注画面，右侧是半场矩形步伐地图，播放时实时显示脚步轨迹和热力变化。
多人画面可在侧边栏选择“跟踪球员”，用于锁定近端、远端、左侧或右侧球员，减少误跟踪到对方。
如果选择“首帧目标框”，页面会在上传视频后显示首帧，支持直接拖出目标球员矩形框；系统会用该框初始化目标并做连续跟踪。若未安装 `streamlit-drawable-canvas`，页面会自动退回到带预览图的滑块框选。
可通过“分析区域 ROI”限定上半场、下半场、左右半场或自定义矩形区域，让多人比赛画面优先跟踪目标区域内的球员。
步伐热力图支持自动轨迹范围和手动四点球场标定；手动标定后会将脚步位置映射到固定半场面板。
系统会围绕疑似击球点截取短片段并进行逐拍动作识别，在总览和标注视频面板中展示每拍时间、动作类别和置信度。
逐拍结果会附带质量评分、问题标签和训练建议，例如击球点偏低、挥拍加速不足、回位慢或重心稳定性不足。
视频模式还会导出每拍复盘小片段，可在页面中逐拍播放和下载。
页面包含总览、标注视频、步伐监测和训练报告四个面板；步伐监测会基于脚踝、髋部和重心变化生成汇总指标。
页面内置项目说明页，便于展示系统流程、核心算法、当前局限和后续方向；训练报告支持 JSON 和 Markdown 导出。
可选启用大模型教练反馈，当前预留 Qwen 和智谱AI OpenAI-compatible 接口；可在页面输入 API Key，或设置 `DASHSCOPE_API_KEY` / `QWEN_API_KEY` / `ZHIPUAI_API_KEY`。
大模型反馈支持两种模式：“快速总结”只发送少量代表性拍次，适合调试接口；“全程分段总结”会按拍次分组生成小结，再汇总成完整训练报告，更适合正式复盘长视频。
页面默认使用“自适应最佳”模式，会尽量逐帧分析以减少漏检；长视频处理较慢时可切换为快速/均衡模式。

### 7.1 独立 HTML 前端

项目已提供独立前端工作台，便于后续产品落地和接入 Web 后端：

```text
frontend/index.html
```

直接在浏览器打开即可体验上传视频、首帧框选、分析状态、结果面板和训练报告的前端流程。当前默认使用前端演示数据；后续可通过 `POST /api/analyze` 接入 FastAPI/Flask 后端，接口说明见：

```text
frontend/README.md
```

也可以启动内置 FastAPI 后端，直接用真实模型分析视频：

```bash
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000
```

然后打开：

```text
http://127.0.0.1:8000/frontend/
```

### 8. 大模型配置

项目会自动读取根目录 `.env` 中的大模型配置。可参考 `.env.example` 填写：

```bash
DASHSCOPE_API_KEY=你的通义千问Key
QWEN_MODEL=qwen-plus
ZHIPUAI_API_KEY=你的智谱AI Key
ZHIPU_MODEL=glm-4-plus
```

`.env` 已加入 `.gitignore`，不要提交真实 API Key。

如果页面提示大模型反馈 `read operation timed out`，说明视觉分析和本地规则报告已完成，只是外部大模型接口超时。可在侧边栏提高“大模型超时秒数”、切换为“快速总结”、限制全程分段总结的分组数，或稍后重试。

## 下一步

- [ ] 训练动作分类模型（Video Swin / TimeSformer）
- [ ] 构建标准动作模板库
- [ ] 实现动作质量评分（DTW 对比）
- [x] 接入 LLM 生成训练建议
- [x] 开发前端界面
