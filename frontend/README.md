# 羽动智练前端工作台

这是从 Streamlit 原型拆出来的 HTML/CSS/JS 前端，用于后续产品落地。

## 启动方式

先启动 FastAPI 后端：

```bash
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000
```

然后打开：

```text
http://127.0.0.1:8000/frontend/
```

## 当前流程

1. 上传训练或比赛视频。
2. 系统用后端 OpenCV 自动抽取可见帧，避免浏览器原始视频黑屏影响框选。
3. 在抽帧画面上框选目标球员。
4. 点击“开始分析”，后端执行姿态识别、动作分类、击球事件检测、步伐分析和训练报告生成。
5. 默认调用侧边栏选择的大模型服务生成 AI 教练反馈；若 API Key 或网络不可用，会自动回退到本地规则报告。

## 大模型配置

前端只保留模型服务下拉框：

- Qwen 通义千问
- 智谱 AI GLM

API Key 建议放在项目根目录 `.env`：

```env
DASHSCOPE_API_KEY=你的QwenKey
QWEN_API_KEY=你的QwenKey
ZHIPUAI_API_KEY=你的智谱Key
```

## 接口

分析接口：

```text
POST /api/analyze
```

抽帧接口：

```text
POST /api/frame
```

前端会通过 `FormData` 发送视频和配置。
