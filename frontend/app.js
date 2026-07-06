/* ============================================================
   羽动智练 — Badminton Smart Training System
   Application Logic (Dark Theme)
   ============================================================ */

(function () {
  "use strict";

  // ---- State ----
  const state = {
    connected: false,
    detecting: false,
    realVideoLoaded: false,
    videoFile: null,
    precheckPassed: false,
    precheckResult: null,
    analysisReport: null,
    frameImage: null,
    bbox: null,
    detections: 0,
    fps: 0,
    latency: 0,
    avgConf: 0,
    history: [],
    radarData: [0, 0, 0, 0, 0, 0],
    footworkTrace: [],
    shotEvents: [],
    playbackDuration: 0,
    coachHistory: [],
    analysisTimerId: null,
    analysisStartedAt: 0,
    courtAnimationFrame: null,
    analysisVideoObjectUrl: null,
  };

  // ---- DOM Elements ----
  const elements = {
    statusIndicator: document.getElementById("statusIndicator"),
    statusText: document.querySelector(".status-text"),

    // Tabs
    mainTabs: document.getElementById("mainTabs"),
    panels: {
      training: document.getElementById("panel-training"),
      analysis: document.getElementById("panel-analysis"),
      report: document.getElementById("panel-report"),
      coach: document.getElementById("panel-coach"),
      history: document.getElementById("panel-history"),
      settings: document.getElementById("panel-settings"),
    },

    // Canvas
    frameCanvas: document.getElementById("frameCanvas"),
    frameCanvasWrap: document.getElementById("frameCanvasWrap"),
    analysisVideo: document.getElementById("analysisVideo"),
    videoActions: document.getElementById("videoActions"),
    videoStatusText: document.getElementById("videoStatusText"),
    downloadVideoLink: document.getElementById("downloadVideoLink"),
    emptyMedia: document.getElementById("emptyMedia"),
    videoUploadInput: document.getElementById("videoUploadInput"),
    analysisTimer: document.getElementById("analysisTimer"),
    analysisStage: document.getElementById("analysisStage"),
    analysisElapsed: document.getElementById("analysisElapsed"),
    shotTimeline: document.getElementById("shotTimeline"),
    shotTimelineEmpty: document.getElementById("shotTimelineEmpty"),
    shotTimelineSummary: document.getElementById("shotTimelineSummary"),
    courtCanvas: document.getElementById("courtCanvas"),
    radarCanvas: document.getElementById("radarCanvas"),

    // Controls
    btnStart: document.getElementById("btnStart"),
    btnStop: document.getElementById("btnStop"),
    btnReset: document.getElementById("btnReset"),
    btnSettings: document.getElementById("btnSettings"),
    btnExport: document.getElementById("btnExport"),
    btnSaveSettings: document.getElementById("btnSaveSettings"),
    btnResetSettings: document.getElementById("btnResetSettings"),

    // Shooting guide & precheck
    guideToggle: document.getElementById("guideToggle"),
    shootingGuide: document.getElementById("shootingGuide"),
    precheckPanel: document.getElementById("precheckPanel"),
    precheckStatus: document.getElementById("precheckStatus"),
    precheckItems: document.getElementById("precheckItems"),
    precheckActions: document.getElementById("precheckActions"),
    btnProceedAnalyze: document.getElementById("btnProceedAnalyze"),
    btnReupload: document.getElementById("btnReupload"),

    // History page
    historyList: document.getElementById("historyList"),
    historyTotalSessions: document.getElementById("historyTotalSessions"),
    historyAvgScore: document.getElementById("historyAvgScore"),
    historyTotalShots: document.getElementById("historyTotalShots"),
    historyLastDate: document.getElementById("historyLastDate"),
    trendChart: document.getElementById("trendChart"),
    btnRefreshHistory: document.getElementById("btnRefreshHistory"),

    // Inputs
    modelSelect: document.getElementById("modelSelect"),
    confThreshold: document.getElementById("confThreshold"),
    videoSource: document.getElementById("videoSource"),
    inferenceBackend: document.getElementById("inferenceBackend"),
    computeDevice: document.getElementById("computeDevice"),
    inputResolution: document.getElementById("inputResolution"),
    modelPrecision: document.getElementById("modelPrecision"),
    frameRate: document.getElementById("frameRate"),
    frameSkip: document.getElementById("frameSkip"),
    roiX1: document.getElementById("roiX1"),
    roiY1: document.getElementById("roiY1"),
    roiX2: document.getElementById("roiX2"),
    roiY2: document.getElementById("roiY2"),
    saveDetection: document.getElementById("saveDetection"),
    configOutput: document.getElementById("configOutput"),

    // Metrics
    metricFps: document.getElementById("metricFps"),
    metricDetections: document.getElementById("metricDetections"),
    metricConf: document.getElementById("metricConf"),
    metricLatency: document.getElementById("metricLatency"),

    // Analysis
    actionType: document.getElementById("actionType"),
    actionScore: document.getElementById("actionScore"),
    powerLevel: document.getElementById("powerLevel"),
    qualitySmooth: document.getElementById("qualitySmooth"),
    qualityAccuracy: document.getElementById("qualityAccuracy"),
    qualityCoord: document.getElementById("qualityCoord"),
    qualityFoot: document.getElementById("qualityFoot"),
    qualityWrist: document.getElementById("qualityWrist"),
    qualityBalance: document.getElementById("qualityBalance"),
    barSmooth: document.getElementById("barSmooth"),
    barAccuracy: document.getElementById("barAccuracy"),
    barCoord: document.getElementById("barCoord"),
    barFoot: document.getElementById("barFoot"),
    barWrist: document.getElementById("barWrist"),
    barBalance: document.getElementById("barBalance"),
    historyTable: document.getElementById("historyTable"),

    // Report
    totalSessions: document.getElementById("totalSessions"),
    avgScore: document.getElementById("avgScore"),
    bestAction: document.getElementById("bestAction"),
    totalFrames: document.getElementById("totalFrames"),
    reportDate: document.getElementById("reportDate"),
    reportDuration: document.getElementById("reportDuration"),
    reportActions: document.getElementById("reportActions"),
    reportHighlights: document.getElementById("reportHighlights"),
    reportIssues: document.getElementById("reportIssues"),
    reportSuggestions: document.getElementById("reportSuggestions"),
    reportPlan: document.getElementById("reportPlan"),
    reportReview: document.getElementById("reportReview"),

    // AI Coach
    coachProvider: document.getElementById("coachProvider"),
    coachMessages: document.getElementById("coachMessages"),
    coachQuestion: document.getElementById("coachQuestion"),
    btnCoachSend: document.getElementById("btnCoachSend"),
    coachUseReport: document.getElementById("coachUseReport"),
    coachContextStatus: document.getElementById("coachContextStatus"),
  };

  const ctx = elements.frameCanvas.getContext("2d");
  const courtCtx = elements.courtCanvas.getContext("2d");
  const radarCtx = elements.radarCanvas.getContext("2d");
  const API_BASE = window.location.protocol.startsWith("http")
    ? window.location.origin
    : "http://127.0.0.1:8000";
  const DELIVERY_ANALYSIS_CONFIG = Object.freeze({
    target_player: "largest",
    target_bbox: null,
    target_roi: "full",
    analysis_preset: "adaptive",
    conf_threshold: 0.3,
    footwork_map_mode: "image",
    llm_provider: "qwen",
    llm_timeout: 120,
    llm_shots_per_group: 8,
    use_cpu: false,
  });

  function apiUrl(path) {
    return `${API_BASE}${path}`;
  }

  // ---- Tab Switching ----
  function switchTab(tabName) {
    // Tabs
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.classList.toggle("active", tab.dataset.tab === tabName);
    });
    // Sidebar nav
    document.querySelectorAll(".nav-item").forEach((item) => {
      item.classList.toggle("active", item.dataset.tab === tabName);
    });
    // Panels
    Object.entries(elements.panels).forEach(([key, panel]) => {
      panel.classList.toggle("active", key === tabName);
    });
    // Update topbar title
    const titles = {
      training: "训练检测",
      analysis: "动作分析",
      report: "训练报告",
      coach: "AI教练",
      history: "训练历史",
      settings: "系统设置",
    };
    document.querySelector(".topbar-left h1").textContent = titles[tabName] || "羽动智练";
  }

  // Tab click handlers
  elements.mainTabs.addEventListener("click", (e) => {
    const tab = e.target.closest(".tab");
    if (tab && tab.dataset.tab) {
      switchTab(tab.dataset.tab);
      if (tab.dataset.tab === "history") loadHistoryList();
    }
  });

  document.querySelector(".sidebar-nav").addEventListener("click", (e) => {
    const item = e.target.closest(".nav-item");
    if (item && item.dataset.tab) {
      switchTab(item.dataset.tab);
      if (item.dataset.tab === "history") loadHistoryList();
    }
  });

  elements.btnSettings.addEventListener("click", () => switchTab("settings"));

  // ---- Connection Status ----
  function setConnected(connected) {
    state.connected = connected;
    const indicator = elements.statusIndicator;
    const statusText = indicator.querySelector(".status-text");
    indicator.classList.remove("connected", "error");
    if (connected) {
      indicator.classList.add("connected");
      statusText.textContent = "已连接";
    } else {
      statusText.textContent = "未连接";
    }
  }

  // ---- Drawing Functions ----
  function drawFrame(previewBox = null) {
    if (!state.frameImage) return;
    ctx.clearRect(0, 0, elements.frameCanvas.width, elements.frameCanvas.height);
    ctx.drawImage(state.frameImage, 0, 0, elements.frameCanvas.width, elements.frameCanvas.height);

    const box = previewBox || state.bbox;
    if (!box) return;

    const x1 = box.x1 * elements.frameCanvas.width;
    const y1 = box.y1 * elements.frameCanvas.height;
    const x2 = box.x2 * elements.frameCanvas.width;
    const y2 = box.y2 * elements.frameCanvas.height;
    ctx.save();
    ctx.fillStyle = "rgba(94, 255, 159, 0.15)";
    ctx.strokeStyle = "#5eff9f";
    ctx.lineWidth = 3;
    ctx.fillRect(x1, y1, x2 - x1, y2 - y1);
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    ctx.fillStyle = "#5eff9f";
    ctx.font = "bold 14px JetBrains Mono, monospace";
    ctx.fillText("TARGET", x1 + 8, Math.max(20, y1 - 8));
    ctx.restore();
  }

  function showUploadHint(text) {
    if (!elements.emptyMedia) return;
    elements.frameCanvasWrap.style.display = "none";
    if (elements.analysisVideo) {
      elements.analysisVideo.hidden = true;
      elements.analysisVideo.removeAttribute("src");
    }
    if (elements.videoActions) {
      elements.videoActions.hidden = true;
    }
    elements.emptyMedia.style.display = "flex";
    elements.emptyMedia.innerHTML = `<span>${text}</span>`;
  }

  function drawUploadedVideoFrame(video) {
    const canvas = elements.frameCanvas;
    const sourceW = video.videoWidth || 640;
    const sourceH = video.videoHeight || 480;
    const targetW = 640;
    const targetH = Math.max(360, Math.round((targetW * sourceH) / sourceW));
    canvas.width = targetW;
    canvas.height = targetH;
    ctx.clearRect(0, 0, targetW, targetH);
    ctx.drawImage(video, 0, 0, targetW, targetH);

    const img = new Image();
    img.onload = () => {
      state.frameImage = img;
      state.bbox = null;
      elements.emptyMedia.style.display = "none";
      elements.frameCanvasWrap.style.display = "block";
      if (elements.analysisVideo) {
        elements.analysisVideo.hidden = true;
        elements.analysisVideo.removeAttribute("src");
      }
      if (elements.videoActions) {
        elements.videoActions.hidden = true;
      }
      elements.frameCanvas.hidden = false;
      drawFrame();
      setConnected(true);
    };
    img.src = canvas.toDataURL("image/jpeg", 0.9);
  }

  function drawFrameBlob(blob) {
    const imageUrl = URL.createObjectURL(blob);
    const img = new Image();
    img.onload = () => {
      const sourceW = img.naturalWidth || 640;
      const sourceH = img.naturalHeight || 480;
      const targetW = 640;
      const targetH = Math.max(360, Math.round((targetW * sourceH) / sourceW));
      elements.frameCanvas.width = targetW;
      elements.frameCanvas.height = targetH;
      state.frameImage = img;
      state.bbox = null;
      elements.emptyMedia.style.display = "none";
      elements.frameCanvasWrap.style.display = "block";
      if (elements.analysisVideo) {
        elements.analysisVideo.hidden = true;
        elements.analysisVideo.removeAttribute("src");
      }
      if (elements.videoActions) {
        elements.videoActions.hidden = true;
      }
      elements.frameCanvas.hidden = false;
      drawFrame();
      setConnected(true);
      URL.revokeObjectURL(imageUrl);
    };
    img.onerror = () => {
      URL.revokeObjectURL(imageUrl);
      showUploadHint("抽帧图片加载失败，请换一个视频重试");
    };
    img.src = imageUrl;
  }

  async function loadFrameFromBackend(file) {
    const form = new FormData();
    form.append("video", file);
    form.append("time_sec", "3");
    const response = await fetch(apiUrl("/api/frame"), {
      method: "POST",
      body: form,
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    drawFrameBlob(await response.blob());
  }

  async function loadUploadedVideo(file) {
    if (!file) return;
    stopCourtPlaybackLoop();
    if (state.analysisTimerId) {
      window.clearInterval(state.analysisTimerId);
      state.analysisTimerId = null;
    }
    if (elements.analysisTimer) elements.analysisTimer.hidden = true;
    state.videoFile = file;
    state.analysisReport = null;
    state.realVideoLoaded = true;
    state.bbox = null;
    state.precheckPassed = false;
    state.precheckResult = null;
    hidePrecheckPanel();
    showUploadHint("正在读取视频画面...");
    if (window.location.protocol.startsWith("http")) {
      try {
        await loadFrameFromBackend(file);
        await runPrecheck(file);
        return;
      } catch (error) {
        showUploadHint(`后端抽帧失败：${formatFetchError(error)}，正在尝试浏览器预览...`);
      }
    }
    const url = URL.createObjectURL(file);
    const video = document.createElement("video");
    video.preload = "metadata";
    video.muted = true;
    video.playsInline = true;
    video.src = url;

    const cleanup = () => URL.revokeObjectURL(url);
    video.addEventListener("loadedmetadata", () => {
      const duration = Number.isFinite(video.duration) ? video.duration : 0;
      video.currentTime = duration > 2 ? Math.min(Math.max(duration * 0.12, 1), 5) : 0;
    });
    video.addEventListener("seeked", () => {
      drawUploadedVideoFrame(video);
      cleanup();
    }, { once: true });
    video.addEventListener("loadeddata", () => {
      if (!Number.isFinite(video.duration) || video.duration <= 2) {
        drawUploadedVideoFrame(video);
        cleanup();
      }
    }, { once: true });
    video.addEventListener("error", () => {
      cleanup();
      showUploadHint("视频读取失败，请换一个 MP4 文件重试");
    }, { once: true });
  }

  function showPrecheckPanel() {
    if (elements.precheckPanel) elements.precheckPanel.hidden = false;
  }

  function hidePrecheckPanel() {
    if (elements.precheckPanel) {
      elements.precheckPanel.hidden = true;
      elements.precheckItems.innerHTML = "";
      elements.precheckActions.hidden = true;
    }
  }

  function renderPrecheckResult(result) {
    state.precheckResult = result;
    showPrecheckPanel();
    const statusEl = elements.precheckStatus;
    statusEl.className = "precheck-status " + (result.overall || (result.ok ? "pass" : "fail"));
    const scene = result.scene_type;
    if (result.overall === "pass" || result.ok) {
      if (scene === "match_wide") {
        statusEl.textContent = "检测到比赛远景视频，可以分析";
      } else {
        statusEl.textContent = "视频质量良好，可以分析";
      }
    } else if (result.overall === "warn") {
      if (scene === "match_wide") {
        statusEl.textContent = "比赛远景视频，将自动适配参数进行分析";
      } else {
        statusEl.textContent = "视频存在小问题，仍可分析，部分精度可能受影响";
      }
    } else {
      statusEl.textContent = "视频质量不佳，请检查后重新上传";
    }

    elements.precheckItems.innerHTML = "";
    (result.items || []).forEach((item) => {
      const div = document.createElement("div");
      div.className = "precheck-item";
      const iconMap = { pass: "✅", warn: "⚠️", fail: "❌" };
      div.innerHTML = `
        <span class="check-icon ${item.status}">${iconMap[item.status] || "•"}</span>
        <span class="check-label">${item.name}</span>
        <span class="check-value">${item.value || ""}</span>
        ${item.detail ? `<div class="check-detail">${item.detail}</div>` : ""}
      `;
      elements.precheckItems.appendChild(div);
    });

    elements.precheckActions.hidden = false;
    state.precheckPassed = result.ok || result.overall !== "fail";
    if (elements.btnProceedAnalyze) {
      if (result.overall === "pass") {
        elements.btnProceedAnalyze.textContent = "开始分析";
      } else if (result.scene_type === "match_wide") {
        elements.btnProceedAnalyze.textContent = "开始分析（比赛远景模式）";
      } else {
        elements.btnProceedAnalyze.textContent = "继续分析";
      }
      elements.btnProceedAnalyze.disabled = !state.precheckPassed;
    }
  }

  async function runPrecheck(file) {
    if (!window.location.protocol.startsWith("http")) return;
    showPrecheckPanel();
    elements.precheckStatus.textContent = "检测中...";
    elements.precheckStatus.className = "precheck-status";
    elements.precheckItems.innerHTML = '<div class="precheck-item"><span class="check-icon">⏳</span><span class="check-label">正在检测视频质量...</span></div>';
    elements.precheckActions.hidden = true;

    try {
      const fd = new FormData();
      fd.append("video", file);
      const resp = await fetch("/api/precheck", { method: "POST", body: fd });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(err.detail || "Precheck failed");
      }
      const result = await resp.json();
      renderPrecheckResult(result);
    } catch (err) {
      elements.precheckStatus.textContent = "检测失败，可直接尝试分析";
      elements.precheckStatus.className = "precheck-status warn";
      elements.precheckItems.innerHTML = `<div class="precheck-item"><span class="check-icon warn">⚠️</span><span class="check-label">预检失败</span><span class="check-value">${err.message}</span></div>`;
      elements.precheckActions.hidden = false;
      state.precheckPassed = true;
      if (elements.btnProceedAnalyze) elements.btnProceedAnalyze.disabled = false;
    }
  }

  function buildAnalyzeConfig() {
    return { ...DELIVERY_ANALYSIS_CONFIG };
  }

  function formatElapsed(ms) {
    const seconds = Math.max(0, Number(ms || 0) / 1000);
    if (seconds < 60) return `${seconds.toFixed(1)} 秒`;
    const minutes = Math.floor(seconds / 60);
    const remain = Math.floor(seconds % 60);
    return `${minutes} 分 ${String(remain).padStart(2, "0")} 秒`;
  }

  function startAnalysisTimer(startedAt = performance.now()) {
    state.analysisStartedAt = startedAt;
    if (state.analysisTimerId) {
      window.clearInterval(state.analysisTimerId);
      state.analysisTimerId = null;
    }
    if (elements.analysisTimer) elements.analysisTimer.hidden = false;
    if (elements.analysisStage) elements.analysisStage.textContent = "上传视频并准备姿态分析";
    if (elements.analysisElapsed) elements.analysisElapsed.textContent = "0.0 秒";
    state.analysisTimerId = window.setInterval(() => {
      const elapsed = performance.now() - state.analysisStartedAt;
      if (elements.analysisElapsed) elements.analysisElapsed.textContent = formatElapsed(elapsed);
      if (elements.analysisStage) {
        if (elapsed > 45000) elements.analysisStage.textContent = "生成标注视频与训练报告";
        else if (elapsed > 15000) elements.analysisStage.textContent = "识别人体姿态和步伐轨迹";
        else if (elapsed > 5000) elements.analysisStage.textContent = "抽帧并加载动作识别模型";
      }
    }, 100);
  }

  function stopAnalysisTimer(statusText, elapsedMs = null) {
    if (state.analysisTimerId) {
      window.clearInterval(state.analysisTimerId);
      state.analysisTimerId = null;
    }
    const elapsed = elapsedMs == null ? performance.now() - state.analysisStartedAt : elapsedMs;
    if (elements.analysisTimer) elements.analysisTimer.hidden = false;
    if (elements.analysisStage) elements.analysisStage.textContent = statusText;
    if (elements.analysisElapsed) elements.analysisElapsed.textContent = formatElapsed(elapsed);
  }

  async function runBackendAnalysis() {
    if (!state.videoFile) {
      showUploadHint("请先点击这里上传视频，再开始分析");
      return;
    }

    state.detecting = true;
    setConnected(true);
    elements.btnStart.classList.add("btn-secondary");
    elements.btnStart.classList.remove("btn-primary");
    elements.btnStart.textContent = "分析中...";
    showUploadHint("正在调用后端分析，生成标注视频...");

    const startedAt = performance.now();
    startAnalysisTimer(startedAt);
    const form = new FormData();
    form.append("video", state.videoFile);
    form.append("config", JSON.stringify(buildAnalyzeConfig()));

    try {
      await ensureBackendReady();
      const response = await fetch(apiUrl("/api/analyze"), {
        method: "POST",
        body: form,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const report = await response.json();
      const elapsedMs = performance.now() - startedAt;
      state.analysisReport = report;
      stopAnalysisTimer("分析完成，已生成训练结果", elapsedMs);
      renderBackendReport(report, elapsedMs);
      loadHistoryList();
    } catch (error) {
      setConnected(false);
      stopAnalysisTimer("分析失败，请检查后端服务或视频格式");
      showUploadHint(`分析失败：${formatFetchError(error)}`);
    } finally {
      state.detecting = false;
      elements.btnStart.classList.remove("btn-secondary");
      elements.btnStart.classList.add("btn-primary");
      elements.btnStart.textContent = "开始检测";
    }
  }

  async function ensureBackendReady() {
    try {
      const response = await fetch(apiUrl("/api/health"), { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`后端健康检查失败：HTTP ${response.status}`);
      }
    } catch (error) {
      throw new Error(`无法连接后端 ${API_BASE}，请确认 uvicorn 正在运行，并通过 http://127.0.0.1:8000/frontend/ 打开页面`);
    }
  }

  function formatFetchError(error) {
    if (!error || !error.message) return "未知网络错误";
    if (error.message === "Failed to fetch") {
      return `无法连接后端 ${API_BASE}。请确认页面地址是 http://127.0.0.1:8000/frontend/，并查看 PowerShell 是否有 /api/analyze 请求日志。`;
    }
    return error.message;
  }

  function renderBackendReport(report, elapsedMs) {
    const annotatedUrl = report.annotated_video_url || report.raw_annotated_video_url;
    const previewUrl = report.annotated_preview_url
      ? `${report.annotated_preview_url}${report.annotated_preview_url.includes("?") ? "&" : "?"}t=${Date.now()}`
      : null;
    const videoUrl = annotatedUrl
      ? `${annotatedUrl}${annotatedUrl.includes("?") ? "&" : "?"}t=${Date.now()}`
      : null;

    const videoWarning = report.video_warning || null;
    if (videoUrl && elements.analysisVideo) {
      setupVideoActions(videoUrl, videoWarning);
      showAnalysisVideo(videoUrl, previewUrl, videoWarning);
    } else if (previewUrl) {
      showGeneratedPoster(previewUrl, videoWarning || "标注预览图已生成，视频文件暂未返回。");
    }

    state.fps = 0;
    state.detections = Number(report.hit_count || 0);
    state.latency = Math.max(1, Math.round(elapsedMs));
    state.avgConf = Number((Number(report.confidence || 0) * 100).toFixed(1));
    state.footworkTrace = Array.isArray(report.footwork_trace) ? report.footwork_trace : [];
    state.shotEvents = normalizeShotEvents(report.shot_events || report.report?.shot_events || []);
    state.playbackDuration = Number(report.video_metadata?.duration_sec || 0);
    renderShotTimeline();
    updatePlaybackMetrics(0, false);

    elements.actionType.textContent = report.predicted_action || "--";
    const confidencePercent = report.confidence == null ? null : Math.round(Number(report.confidence) * 100);

    const scores = report.footwork_scores || {};
    const scoreOf = (...keys) => {
      for (const key of keys) {
        const value = Number(scores[key]);
        if (Number.isFinite(value)) return Math.max(0, Math.min(100, value));
      }
      return 0;
    };
    const movement = scoreOf("移动量", "movement");
    const explosiveness = scoreOf("启动爆发", "explosiveness");
    const stability = scoreOf("重心稳定", "stability");
    const recovery = scoreOf("回位能力", "recovery");
    const coverage = scoreOf("覆盖范围", "coverage");
    const balance = scoreOf("步幅平衡", "balance");
    const coordination = scoreOf("身体协调", "coordination") || Math.max(0, Math.min(100, stability * 0.4 + balance * 0.35 + recovery * 0.25));
    const confidenceScore = report.confidence == null ? 0 : Math.max(0, Math.min(100, Number(report.confidence) * 100));
    const smoothness = Math.max(0, Math.min(100, recovery * 0.35 + balance * 0.35 + coverage * 0.3));
    const values = [
      smoothness,
      confidenceScore,
      coordination,
      movement,
      explosiveness,
      stability,
    ];
    const qualitySummary = report.quality_summary || {};
    const fallbackOverall = Math.max(0, Math.min(100, values.reduce((sum, value) => sum + value, 0) / Math.max(values.length, 1)));
    const overallScore = Number.isFinite(Number(qualitySummary.overall_score))
      ? Number(qualitySummary.overall_score)
      : fallbackOverall;
    const avgQualityScore = Number.isFinite(Number(qualitySummary.avg_quality_score))
      ? Number(qualitySummary.avg_quality_score)
      : overallScore;
    const scoreSource = Number.isFinite(Number(qualitySummary.overall_score))
      ? `质量分 ${Number(overallScore).toFixed(1)}`
      : `综合估算 ${Number(overallScore).toFixed(1)}`;

    elements.actionScore.textContent = Math.round(overallScore);
    elements.powerLevel.textContent = confidencePercent == null ? scoreSource : `${scoreSource} · 识别置信度 ${confidencePercent}%`;

    [
      [elements.qualitySmooth, elements.barSmooth, values[0]],
      [elements.qualityAccuracy, elements.barAccuracy, values[1]],
      [elements.qualityCoord, elements.barCoord, values[2]],
      [elements.qualityFoot, elements.barFoot, values[3]],
      [elements.qualityWrist, elements.barWrist, values[4]],
      [elements.qualityBalance, elements.barBalance, values[5]],
    ].forEach(([label, bar, value]) => {
      label.textContent = value.toFixed(1);
      bar.style.width = `${value}%`;
    });
    state.radarData = values;
    drawRadar(state.radarData);

    const historyRows = (report.shot_events || [])
      .slice(0, 20)
      .map((event, index) => {
        const time = Number(event.time_sec ?? event.time ?? 0);
        const action = event.shot_action || event.action || event.predicted_action || "击球片段";
        const confidence = Number(event.shot_confidence ?? event.confidence ?? 0);
        const quality = Number(event.quality_score);
        const qualityText = Number.isFinite(quality) ? quality.toFixed(1) : "--";
        return `<tr><td>${time > 0 ? `${time.toFixed(1)}s` : index + 1}</td><td>${action}</td><td>${(confidence * 100).toFixed(1)}%</td><td>${qualityText}</td><td>${event.quality_level || "--"}</td></tr>`;
      });
    elements.historyTable.innerHTML = historyRows.join("") || '<tr><td colspan="5" style="text-align:center; color:var(--muted); padding:32px;">暂无逐拍检测记录</td></tr>';

    const coach = report.coach_report || {};
    elements.totalSessions.textContent = "1";
    elements.avgScore.textContent = Math.round(avgQualityScore);
    elements.bestAction.textContent = report.predicted_action || "--";
    elements.totalFrames.textContent = report.report?.motion_summary?.valid_frames || "--";
    elements.reportDate.textContent = new Date().toLocaleString();
    elements.reportDuration.textContent = formatDuration(report.video_metadata?.duration_sec);
    elements.reportActions.textContent = `${report.hit_count || 0} 次`;
    elements.reportHighlights.textContent = buildHighlightText(report, coach);
    elements.reportIssues.textContent = buildIssueText(report, coach);
    elements.reportSuggestions.textContent = buildSuggestionText(report, coach);
    elements.reportPlan.textContent = buildPlanText(report, coach);
    elements.reportReview.textContent = buildReviewText(report);
    drawCourt(values, state.footworkTrace, 1);
    updateCoachContextStatus();
  }

  function setupVideoActions(videoUrl) {
    if (!elements.videoActions) return;
    elements.videoActions.hidden = false;
    elements.videoStatusText.textContent = "标注视频已生成，可在页面中播放。";
    elements.downloadVideoLink.href = videoUrl;
  }

  function showAnalysisVideo(videoUrl, previewUrl = null) {
    let settled = false;
    const markPlayable = () => {
      settled = true;
      elements.videoStatusText.textContent = "标注视频已生成，可播放或下载。";
    };
    const markProblem = () => {
      elements.videoStatusText.textContent = "浏览器未能播放当前视频，请下载视频查看，或重新分析生成新视频。";
      if (previewUrl) {
        showGeneratedPoster(previewUrl, "浏览器未能播放标注视频，已切换为预览图。可下载视频查看。");
      }
    };

    elements.analysisVideo.onloadeddata = markPlayable;
    elements.analysisVideo.oncanplay = markPlayable;
    elements.analysisVideo.onerror = markProblem;
    elements.analysisVideo.onstalled = markProblem;
    elements.analysisVideo.ontimeupdate = () => {
      updatePlaybackMetrics(elements.analysisVideo.currentTime || 0, true);
    };
    elements.analysisVideo.onloadedmetadata = () => {
      if (!state.playbackDuration && Number.isFinite(elements.analysisVideo.duration)) {
        state.playbackDuration = elements.analysisVideo.duration;
      }
      updatePlaybackMetrics(elements.analysisVideo.currentTime || 0, true);
    };
    elements.frameCanvas.hidden = true;
    elements.analysisVideo.pause();
    elements.analysisVideo.removeAttribute("src");
    elements.analysisVideo.load();
    elements.analysisVideo.src = videoUrl;
    if (previewUrl) {
      elements.analysisVideo.poster = previewUrl;
    } else {
      elements.analysisVideo.removeAttribute("poster");
    }
    elements.analysisVideo.hidden = false;
    elements.frameCanvasWrap.style.display = "block";
    elements.emptyMedia.style.display = "none";
    elements.analysisVideo.load();
    window.setTimeout(() => {
      if (!settled && elements.analysisVideo && !elements.analysisVideo.hidden) {
        markProblem();
      }
    }, 4500);
  }

  function formatDuration(durationSec) {
    const seconds = Number(durationSec || 0);
    if (!Number.isFinite(seconds) || seconds <= 0) return "--";
    const minutes = Math.floor(seconds / 60);
    const remain = Math.round(seconds % 60);
    return minutes > 0 ? `${minutes} 分 ${remain} 秒` : `${remain} 秒`;
  }

  function showGeneratedPoster(previewUrl, message) {
    if (!previewUrl) return;
    const img = new Image();
    img.onload = () => {
      const sourceW = img.naturalWidth || 640;
      const sourceH = img.naturalHeight || 480;
      const targetW = 640;
      const targetH = Math.max(360, Math.round((targetW * sourceH) / sourceW));
      elements.frameCanvas.width = targetW;
      elements.frameCanvas.height = targetH;
      ctx.clearRect(0, 0, targetW, targetH);
      ctx.drawImage(img, 0, 0, targetW, targetH);
      state.frameImage = img;
      elements.frameCanvas.hidden = false;
      if (elements.analysisVideo) {
        stopCourtPlaybackLoop();
        elements.analysisVideo.pause();
        elements.analysisVideo.hidden = true;
      }
      elements.frameCanvasWrap.style.display = "block";
      elements.emptyMedia.style.display = "none";
      if (elements.videoStatusText && message) {
        elements.videoStatusText.textContent = message;
      }
    };
    img.src = previewUrl;
  }

  function setupVideoActions(videoUrl, warning = null) {
    if (!elements.videoActions) return;
    elements.videoActions.hidden = false;
    if (elements.videoStatusText) {
      elements.videoStatusText.textContent = warning || "标注视频已生成，正在准备页面播放。";
    }
    elements.downloadVideoLink.href = videoUrl;
  }

  function showAnalysisVideo(videoUrl, previewUrl = null, warning = null) {
    const video = elements.analysisVideo;
    const status = elements.videoStatusText;
    if (!video) return;

    let settled = false;
    let fallbackShown = false;
    let triedBlobFallback = false;

    const mediaDebug = () => {
      const errorCode = video.error ? video.error.code : "none";
      return `readyState=${video.readyState}, networkState=${video.networkState}, error=${errorCode}`;
    };

    const setStatus = (text) => {
      if (status) status.textContent = text;
    };

    const markPlayable = () => {
      settled = true;
      fallbackShown = false;
      setStatus("标注视频已生成，可在页面播放，也可以下载。");
    };

    const markWaiting = () => {
      if (settled || fallbackShown) return;
      setStatus("视频仍在加载，若长时间没有画面，可以先下载视频查看。");
    };

    const markProblem = (reason = "浏览器解码失败") => {
      if (fallbackShown) return;
      fallbackShown = true;
      const hint = warning || `${reason}，已保留下载入口。`;
      setStatus(`${hint} ${mediaDebug()}`);
      video.hidden = false;
      elements.frameCanvas.hidden = true;
    };

    const loadVideoBlobFallback = async () => {
      if (triedBlobFallback) return false;
      triedBlobFallback = true;
      try {
        setStatus("正在准备稳定播放源，请稍候...");
        const response = await fetch(videoUrl, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const blob = await response.blob();
        if (state.analysisVideoObjectUrl) {
          URL.revokeObjectURL(state.analysisVideoObjectUrl);
        }
        state.analysisVideoObjectUrl = URL.createObjectURL(new Blob([blob], { type: "video/mp4" }));
        video.pause();
        video.removeAttribute("src");
        video.load();
        video.src = state.analysisVideoObjectUrl;
        video.hidden = false;
        elements.frameCanvas.hidden = true;
        video.load();
        setStatus("稳定播放源已准备好，可直接播放，也可以下载视频。");
        return true;
      } catch (error) {
        setStatus(`稳定播放源准备失败，正在尝试后端直连播放。${error.message || error}`);
        return false;
      }
    };

    let sourceReadyForEvents = false;

    video.onloadedmetadata = () => {
      settled = true;
      if (!state.playbackDuration && Number.isFinite(video.duration)) {
        state.playbackDuration = video.duration;
      }
      updatePlaybackMetrics(video.currentTime || 0, true);
      setStatus("标注视频元数据已加载，点击播放即可查看。");
    };
    video.onloadeddata = markPlayable;
    video.oncanplay = markPlayable;
    video.onplay = startCourtPlaybackLoop;
    video.onplaying = () => {
      markPlayable();
      startCourtPlaybackLoop();
    };
    video.onpause = stopCourtPlaybackLoop;
    video.onended = stopCourtPlaybackLoop;
    video.onerror = async () => {
      if (!sourceReadyForEvents) return;
      const recovered = await loadVideoBlobFallback();
      if (!recovered) markProblem("浏览器无法解码当前标注视频");
    };
    video.onstalled = markWaiting;
    video.onwaiting = markWaiting;
    video.ontimeupdate = () => updatePlaybackMetrics(video.currentTime || 0, true);

    elements.frameCanvas.hidden = true;
    video.pause();
    video.preload = "auto";
    video.controls = true;
    video.removeAttribute("src");
    video.load();
    if (previewUrl) {
      video.poster = previewUrl;
    } else {
      video.removeAttribute("poster");
    }
    video.hidden = false;
    elements.frameCanvasWrap.style.display = "block";
    elements.emptyMedia.style.display = "none";
    setStatus("正在准备本地缓存播放源...");
    loadVideoBlobFallback().then((loaded) => {
      if (loaded) {
        sourceReadyForEvents = true;
        return;
      }
      video.pause();
      video.removeAttribute("src");
      video.load();
      video.src = videoUrl;
      sourceReadyForEvents = true;
      video.load();
    });

    window.setTimeout(() => {
      if (!settled && video && !video.hidden) {
        if (video.networkState === HTMLMediaElement.NETWORK_NO_SOURCE || video.error) {
          markProblem("浏览器没有拿到可播放的视频源");
        } else {
          markWaiting();
        }
      }
    }, 12000);
  }

  function showGeneratedPoster(previewUrl, message) {
    if (!previewUrl) return;
    const img = new Image();
    img.onload = () => {
      const sourceW = img.naturalWidth || 640;
      const sourceH = img.naturalHeight || 480;
      const targetW = 640;
      const targetH = Math.max(360, Math.round((targetW * sourceH) / sourceW));
      elements.frameCanvas.width = targetW;
      elements.frameCanvas.height = targetH;
      ctx.clearRect(0, 0, targetW, targetH);
      ctx.drawImage(img, 0, 0, targetW, targetH);
      state.frameImage = img;
      elements.frameCanvas.hidden = false;
      if (elements.analysisVideo) {
        elements.analysisVideo.pause();
        elements.analysisVideo.hidden = true;
      }
      elements.frameCanvasWrap.style.display = "block";
      elements.emptyMedia.style.display = "none";
      if (elements.videoStatusText && message) {
        elements.videoStatusText.textContent = message;
      }
    };
    img.onerror = () => {
      if (elements.videoStatusText) {
        elements.videoStatusText.textContent = "标注视频已生成，但页面预览图加载失败；请点击下载视频查看。";
      }
      if (elements.videoActions) {
        elements.videoActions.hidden = false;
      }
    };
    img.src = previewUrl;
  }

  function cleanCoachText(text) {
    return String(text || "")
      .replace(/#{1,6}\s*/g, "")
      .replace(/\*\*/g, "")
      .replace(/`+/g, "")
      .replace(/你好[，,！!。]?\s*我是[^。！!\n]*[。！!]?\s*/g, "")
      .replace(/作为[^，,。]*AI[^，,。]*[，,。]\s*/g, "")
      .replace(/根据本次训练的视觉模型数据和分段复盘[，,。]\s*/g, "")
      .replace(/\n{2,}/g, "\n")
      .trim();
  }

  function firstUsefulSentence(text, fallback = "--") {
    const cleaned = cleanCoachText(text);
    if (!cleaned) return fallback;
    const sentences = cleaned
      .split(/[。！？\n]/)
      .map((item) => item.trim())
      .filter(Boolean)
      .filter((item) => !/^(本次训练|训练报告|总体概览|概览|建议|重点问题)[:：]?$/.test(item));
    return sentences[0] ? `${sentences[0]}。` : fallback;
  }

  function buildHighlightText(report, coach) {
    const action = report.predicted_action || "主要动作";
    const confidence = report.confidence == null ? null : Math.round(Number(report.confidence) * 100);
    const hitCount = Number(report.hit_count || 0);
    const localHighlight = [
      `${action}${confidence == null ? "" : ` 置信度约 ${confidence}%`}，本次共识别 ${hitCount} 个疑似击球片段`,
      `姿态检测率约 ${Math.round(Number(report.detection_rate || 0) * 100)}%，可作为本次复盘的数据可靠性参考`,
    ];
    if (report.llm_coach_report) {
      const llmLine = firstUsefulSentence(report.llm_coach_report, "");
      return normalizeList([llmLine, ...(coach.highlights || [])], localHighlight, 4);
    }
    return normalizeList(coach.highlights || [], localHighlight, 4);
  }

  function buildSuggestionText(report, coach) {
    const fallback = [
      "优先复看低置信片段，确认动作类别是否被相近动作混淆",
      "结合标注视频检查击球后回位、重心稳定和手腕发力节奏",
      "若视频中多人交叉或远近切换明显，下一次建议先截取更清晰的单人训练片段",
    ];
    return normalizeList([...(coach.focus || []), ...(coach.training_plan || [])], fallback, 4);
  }

  function normalizeList(items, fallbackItems, limit = 4) {
    const source = Array.isArray(items) && items.length ? items : fallbackItems;
    return source
      .map((item) => cleanCoachText(item))
      .filter(Boolean)
      .slice(0, limit)
      .map((item, index) => `${index + 1}. ${item.replace(/[。；;]$/, "")}`)
      .join("\n");
  }

  function buildIssueText(report, coach) {
    const lowConfidence = Number(report.low_confidence_shots || 0);
    const fallback = [
      lowConfidence > 0
        ? `有 ${lowConfidence} 个低置信击球片段，建议优先人工复核`
        : "当前主要风险在于姿态跟踪稳定性，需要结合标注视频确认",
      "重点观察击球后回位速度、重心稳定和连续移动后的步幅一致性",
    ];
    return normalizeList(coach.focus || [], fallback, 4);
  }

  function buildPlanText(report, coach) {
    const fallback = [
      "进行 3 组启动步 + 回位训练，每组 30 秒，关注击球后第一步是否及时",
      "选择 3-5 个低置信片段慢放复盘，检查击球点高度、挥拍路线和身体重心",
      "下一次拍摄保持固定机位，并尽量让目标球员完整进入画面",
    ];
    return normalizeList(coach.training_plan || [], fallback, 4);
  }

  function buildReviewText(report) {
    const top = (report.top_predictions || [])
      .slice(0, 3)
      .map(([action, confidence]) => `${action} ${Math.round(Number(confidence || 0) * 100)}%`)
      .join(" / ");
    const fallback = [
      top ? `Top 动作分布：${top}` : "复核 Top 动作分布，确认是否与实际训练内容一致",
      "若标注视频中出现跟踪跳人，下一次请优先使用清晰单人片段或缩短视频时长",
      "报告建议用于训练参考，关键动作仍建议结合慢放视频人工确认",
    ];
    return normalizeList([], fallback, 4);
  }

  function cleanTrace(trace) {
    const cleaned = [];
    let previous = null;
    (trace || []).forEach((point) => {
      const current = {
        x: Number.isFinite(Number(point.x)) ? Number(point.x) : 0.5,
        y: Number.isFinite(Number(point.y)) ? Number(point.y) : 0.5,
      };
      if (previous) {
        const jump = Math.hypot(current.x - previous.x, current.y - previous.y);
        if (jump > 0.16) return;
      }
      cleaned.push(current);
      previous = current;
    });
    if (cleaned.length < 5) return cleaned;
    return cleaned.map((point, index) => {
      if (index < 2 || index > cleaned.length - 3) return point;
      const window = cleaned.slice(index - 2, index + 3);
      return {
        x: window.reduce((sum, item) => sum + item.x, 0) / window.length,
        y: window.reduce((sum, item) => sum + item.y, 0) / window.length,
      };
    });
  }

  function smoothCourtPoints(points, passes = 2) {
    if (!points || points.length < 3) return points || [];
    let smoothed = points.map((point) => ({ ...point }));
    for (let pass = 0; pass < passes; pass += 1) {
      smoothed = smoothed.map((point, index, list) => {
        if (index === 0 || index === list.length - 1) return point;
        const prev = list[index - 1];
        const next = list[index + 1];
        return {
          x: point.x * 0.5 + (prev.x + next.x) * 0.25,
          y: point.y * 0.5 + (prev.y + next.y) * 0.25,
        };
      });
    }
    return smoothed;
  }

  function densifyCourtPoints(points, maxDistance = 8) {
    if (!points || points.length < 2) return points || [];
    const dense = [points[0]];
    for (let index = 1; index < points.length; index += 1) {
      const prev = points[index - 1];
      const next = points[index];
      const distance = Math.hypot(next.x - prev.x, next.y - prev.y);
      const steps = Math.max(1, Math.ceil(distance / maxDistance));
      for (let step = 1; step <= steps; step += 1) {
        const t = step / steps;
        dense.push({
          x: prev.x + (next.x - prev.x) * t,
          y: prev.y + (next.y - prev.y) * t,
        });
      }
    }
    return dense;
  }

  function traceSmoothPath(ctx, points) {
    if (!points || points.length < 2) return;
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let index = 1; index < points.length - 1; index += 1) {
      const midpoint = {
        x: (points[index].x + points[index + 1].x) / 2,
        y: (points[index].y + points[index + 1].y) / 2,
      };
      ctx.quadraticCurveTo(points[index].x, points[index].y, midpoint.x, midpoint.y);
    }
    const last = points[points.length - 1];
    ctx.lineTo(last.x, last.y);
  }

  function drawFootworkTrail(ctx, points) {
    if (!points || points.length < 2) return;
    ctx.save();
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    ctx.shadowColor = "rgba(94, 255, 159, 0.24)";
    ctx.shadowBlur = 10;
    ctx.strokeStyle = "rgba(94, 255, 159, 0.16)";
    ctx.lineWidth = 7;
    traceSmoothPath(ctx, points);
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.strokeStyle = "rgba(232, 255, 244, 0.72)";
    ctx.lineWidth = 2.2;
    traceSmoothPath(ctx, points);
    ctx.stroke();

    const tail = Math.min(points.length - 1, 28);
    for (let index = 1; index <= tail; index += 1) {
      const point = points[points.length - index];
      const alpha = 0.08 + (1 - index / tail) * 0.18;
      ctx.fillStyle = `rgba(232, 255, 244, ${alpha})`;
      ctx.beginPath();
      ctx.arc(point.x, point.y, 2.2, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  function drawCourt(values = null, trace = state.footworkTrace, progressRatio = 1) {
    const canvas = elements.courtCanvas;
    const w = canvas.width;
    const h = canvas.height;
    courtCtx.clearRect(0, 0, w, h);

    // Background
    courtCtx.fillStyle = "#0a1f16";
    courtCtx.fillRect(0, 0, w, h);

    // Half-court outline for target-player footwork density.
    courtCtx.strokeStyle = "#254b3e";
    courtCtx.lineWidth = 2;
    const marginX = 78;
    const marginY = 42;
    const left = marginX;
    const top = marginY;
    const right = w - marginX;
    const bottom = h - marginY;
    const courtW = right - left;
    const courtH = bottom - top;
    courtCtx.strokeRect(left, top, courtW, courtH);

    // Net and service lines
    courtCtx.strokeStyle = "#5eff9f";
    courtCtx.setLineDash([6, 4]);
    courtCtx.lineWidth = 1.5;
    courtCtx.beginPath();
    courtCtx.moveTo(left, top);
    courtCtx.lineTo(right, top);
    courtCtx.stroke();
    courtCtx.setLineDash([]);

    courtCtx.strokeStyle = "#254b3e";
    courtCtx.lineWidth = 1;
    courtCtx.beginPath();
    courtCtx.moveTo(left, top + courtH * 0.34);
    courtCtx.lineTo(right, top + courtH * 0.34);
    courtCtx.stroke();
    courtCtx.beginPath();
    courtCtx.moveTo(left, top + courtH * 0.62);
    courtCtx.lineTo(right, top + courtH * 0.62);
    courtCtx.stroke();
    courtCtx.beginPath();
    courtCtx.moveTo(w / 2, top + courtH * 0.34);
    courtCtx.lineTo(w / 2, bottom);
    courtCtx.stroke();
    courtCtx.beginPath();
    courtCtx.moveTo(left + courtW * 0.12, top);
    courtCtx.lineTo(left + courtW * 0.12, bottom);
    courtCtx.stroke();
    courtCtx.beginPath();
    courtCtx.moveTo(right - courtW * 0.12, top);
    courtCtx.lineTo(right - courtW * 0.12, bottom);
    courtCtx.stroke();

    // Labels
    courtCtx.fillStyle = "#a8c9bb";
    courtCtx.font = "12px JetBrains Mono, monospace";
    courtCtx.textAlign = "center";
    courtCtx.fillText("目标球员半场步伐热区", w / 2, h - 16);

    if (!trace || trace.length < 2) {
      courtCtx.fillStyle = "rgba(168, 201, 187, 0.78)";
      courtCtx.font = "13px Microsoft YaHei, sans-serif";
      courtCtx.fillText("分析完成后显示目标球员步伐热力分布", w / 2, h / 2);
      return;
    }

    const cleanedTrace = cleanTrace(trace);
    if (cleanedTrace.length < 2) return;
    const safeProgress = Math.max(0.02, Math.min(1, Number(progressRatio || 1)));
    const exactIndex = Math.max(1, (cleanedTrace.length - 1) * safeProgress);
    const baseIndex = Math.max(1, Math.min(cleanedTrace.length - 1, Math.floor(exactIndex)));
    const fraction = Math.max(0, Math.min(1, exactIndex - baseIndex));
    const visible = cleanedTrace.slice(0, baseIndex + 1);
    if (fraction > 0 && cleanedTrace[baseIndex + 1]) {
      const from = cleanedTrace[baseIndex];
      const to = cleanedTrace[baseIndex + 1];
      visible.push({
        x: from.x + (to.x - from.x) * fraction,
        y: from.y + (to.y - from.y) * fraction,
      });
    }
    const points = visible.map((point) => {
      const x = Number.isFinite(Number(point.x)) ? Number(point.x) : 0.5;
      const y = Number.isFinite(Number(point.y)) ? Number(point.y) : 0.5;
      return {
        x: left + (0.16 + x * 0.68) * courtW,
        y: top + (0.18 + y * 0.72) * courtH,
      };
    });

    // Heat layer
    const heatCols = 14;
    const heatRows = 10;
    const heat = new Array(heatCols * heatRows).fill(0);
    points.forEach((point) => {
      const gx = Math.max(0, Math.min(heatCols - 1, Math.round(((point.x - left) / courtW) * (heatCols - 1))));
      const gy = Math.max(0, Math.min(heatRows - 1, Math.round(((point.y - top) / courtH) * (heatRows - 1))));
      for (let yy = -1; yy <= 1; yy += 1) {
        for (let xx = -1; xx <= 1; xx += 1) {
          const nx = gx + xx;
          const ny = gy + yy;
          if (nx < 0 || nx >= heatCols || ny < 0 || ny >= heatRows) continue;
          heat[ny * heatCols + nx] += xx === 0 && yy === 0 ? 3 : 1;
        }
      }
    });
    const maxHeat = Math.max(1, ...heat);
    for (let gy = 0; gy < heatRows; gy += 1) {
      for (let gx = 0; gx < heatCols; gx += 1) {
        const value = heat[gy * heatCols + gx] / maxHeat;
        if (value <= 0.04) continue;
        const cellW = courtW / heatCols;
        const cellH = courtH / heatRows;
        const cellX = left + gx * cellW;
        const cellY = top + gy * cellH;
        const alpha = 0.08 + value * 0.46;
        const hue = 155 - value * 105;
        courtCtx.fillStyle = `hsla(${hue}, 95%, ${48 + value * 12}%, ${alpha})`;
        const rx = cellX - cellW * 0.12;
        const ry = cellY - cellH * 0.12;
        const rw = cellW * 1.24;
        const rh = cellH * 1.24;
        courtCtx.beginPath();
        if (typeof courtCtx.roundRect === "function") {
          courtCtx.roundRect(rx, ry, rw, rh, 12);
        } else {
          courtCtx.rect(rx, ry, rw, rh);
        }
        courtCtx.fill();
      }
    }

    // Recent trajectory only, smoothed and interpolated for a stable playback trail.
    const recent = densifyCourtPoints(smoothCourtPoints(points.slice(-48), 3), 7);
    drawFootworkTrail(courtCtx, recent);

    const current = recent[recent.length - 1] || points[points.length - 1];
    if (current) {
      const pulse = 10 + Math.sin(Date.now() / 180) * 2;
      courtCtx.fillStyle = "rgba(255, 223, 112, 0.20)";
      courtCtx.beginPath();
      courtCtx.arc(current.x, current.y, pulse, 0, Math.PI * 2);
      courtCtx.fill();
      courtCtx.fillStyle = "#ffdf70";
      courtCtx.beginPath();
      courtCtx.arc(current.x, current.y, 6, 0, Math.PI * 2);
      courtCtx.fill();
    }

    const movement = values?.[0] || 0;
    const recovery = values?.[3] || 0;
    const coverage = values?.[4] || 0;
    const summary = `热区 ${points.length} 点 · 覆盖 ${coverage.toFixed(0)} · 移动 ${movement.toFixed(0)} · 回位 ${recovery.toFixed(0)}`;
    courtCtx.fillStyle = "#d9f7e8";
    courtCtx.font = "13px Microsoft YaHei, sans-serif";
    courtCtx.fillText(summary, w / 2, 24);
  }

  function drawRadar(data) {
    const canvas = elements.radarCanvas;
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const r = Math.min(cx, cy) - 30;

    radarCtx.clearRect(0, 0, w, h);

    // Background
    radarCtx.fillStyle = "#0a1f16";
    radarCtx.fillRect(0, 0, w, h);

    const labels = ["挥拍流畅", "击球精准", "身体协调", "步法移动", "手腕发力", "重心稳定"];
    const n = labels.length;

    // Grid rings
    for (let ring = 1; ring <= 5; ring++) {
      const ringR = (r / 5) * ring;
      radarCtx.beginPath();
      for (let i = 0; i <= n; i++) {
        const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
        const x = cx + Math.cos(angle) * ringR;
        const y = cy + Math.sin(angle) * ringR;
        if (i === 0) radarCtx.moveTo(x, y);
        else radarCtx.lineTo(x, y);
      }
      radarCtx.strokeStyle = "rgba(37, 75, 62, 0.6)";
      radarCtx.lineWidth = 1;
      radarCtx.stroke();
    }

    // Axis lines
    for (let i = 0; i < n; i++) {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      radarCtx.beginPath();
      radarCtx.moveTo(cx, cy);
      radarCtx.lineTo(cx + Math.cos(angle) * r, cy + Math.sin(angle) * r);
      radarCtx.strokeStyle = "rgba(37, 75, 62, 0.5)";
      radarCtx.lineWidth = 1;
      radarCtx.stroke();
    }

    // Data polygon
    radarCtx.beginPath();
    for (let i = 0; i <= n; i++) {
      const idx = i % n;
      const angle = (Math.PI * 2 * idx) / n - Math.PI / 2;
      const val = (data[idx] || 0) / 100;
      const x = cx + Math.cos(angle) * r * val;
      const y = cy + Math.sin(angle) * r * val;
      if (i === 0) radarCtx.moveTo(x, y);
      else radarCtx.lineTo(x, y);
    }
    radarCtx.fillStyle = "rgba(94, 255, 159, 0.18)";
    radarCtx.fill();
    radarCtx.strokeStyle = "#5eff9f";
    radarCtx.lineWidth = 2;
    radarCtx.stroke();

    // Data points
    for (let i = 0; i < n; i++) {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const val = (data[i] || 0) / 100;
      const x = cx + Math.cos(angle) * r * val;
      const y = cy + Math.sin(angle) * r * val;
      radarCtx.beginPath();
      radarCtx.arc(x, y, 4, 0, Math.PI * 2);
      radarCtx.fillStyle = "#5eff9f";
      radarCtx.fill();
    }

    // Labels
    radarCtx.fillStyle = "#a8c9bb";
    radarCtx.font = "11px JetBrains Mono, monospace";
    radarCtx.textAlign = "center";
    radarCtx.textBaseline = "middle";
    for (let i = 0; i < n; i++) {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const lx = cx + Math.cos(angle) * (r + 20);
      const ly = cy + Math.sin(angle) * (r + 20);
      radarCtx.fillText(labels[i], lx, ly);
    }
  }

  // ---- Update UI Helpers ----
  function normalizeShotEvents(events) {
    return (events || [])
      .map((event, index) => ({
        index: Number(event.index || index + 1),
        time: Number(event.time_sec ?? event.time ?? 0),
        frame: Number(event.frame ?? 0),
        action: event.shot_action || event.action || event.predicted_action || "击球片段",
        confidence: Number(event.shot_confidence ?? event.confidence ?? 0),
        quality: Number(event.quality_score),
        qualityLevel: event.quality_level || "",
      }))
      .filter((event) => Number.isFinite(event.time))
      .sort((a, b) => a.time - b.time);
  }

  function timelineEventClass(event) {
    const quality = Number(event.quality);
    const confidence = Number(event.confidence || 0) * 100;
    const score = Number.isFinite(quality) ? quality : confidence;
    if (score >= 75) return "is-good";
    if (score >= 50) return "is-mid";
    return "is-low";
  }

  function seekToShot(event) {
    const video = elements.analysisVideo;
    const seekTime = Math.max(0, Number(event.time || 0) - 0.35);
    updatePlaybackMetrics(seekTime, true);
    document.querySelectorAll(".timeline-shot.active").forEach((node) => node.classList.remove("active"));
    const button = elements.shotTimeline?.querySelector(`[data-shot-index="${event.index}"]`);
    if (button) button.classList.add("active");
    if (!video || video.hidden) return;
    try {
      video.currentTime = seekTime;
      video.focus({ preventScroll: true });
    } catch (error) {
      console.warn("Unable to seek video", error);
    }
  }

  function renderShotTimeline() {
    const timeline = elements.shotTimeline;
    if (!timeline) return;
    timeline.querySelectorAll(".timeline-shot").forEach((node) => node.remove());

    const duration = state.playbackDuration || Number(state.analysisReport?.video_metadata?.duration_sec || 0);
    const events = state.shotEvents || [];
    if (!events.length) {
      if (elements.shotTimelineEmpty) elements.shotTimelineEmpty.hidden = false;
      if (elements.shotTimelineSummary) elements.shotTimelineSummary.textContent = "暂无逐拍事件";
      return;
    }

    if (elements.shotTimelineEmpty) elements.shotTimelineEmpty.hidden = true;
    if (elements.shotTimelineSummary) {
      const first = events[0]?.time || 0;
      const last = events[events.length - 1]?.time || 0;
      elements.shotTimelineSummary.textContent = `${events.length} 次击球 · ${formatClock(first)} - ${formatClock(last)}`;
    }

    events.forEach((event) => {
      const position = duration > 0
        ? Math.max(0, Math.min(100, (Number(event.time || 0) / duration) * 100))
        : Math.max(0, Math.min(100, (event.index / Math.max(events.length, 1)) * 100));
      const confidence = Number(event.confidence || 0) * 100;
      const quality = Number(event.quality);
      const scoreText = Number.isFinite(quality)
        ? `质量 ${quality.toFixed(1)}`
        : `置信 ${confidence.toFixed(1)}%`;

      const button = document.createElement("button");
      button.type = "button";
      button.className = `timeline-shot ${timelineEventClass(event)}`;
      button.style.left = `${position}%`;
      button.style.top = `${event.index % 2 === 0 ? 82 : 44}px`;
      button.dataset.shotIndex = String(event.index);
      button.title = `${formatClock(event.time)} · ${event.action} · ${scoreText}`;
      button.innerHTML = `
        <span class="shot-pin">${event.index}</span>
        <span class="shot-label">
          <b>${event.action}</b>
          <small>${formatClock(event.time)} · ${scoreText}</small>
        </span>
      `;
      button.addEventListener("click", () => seekToShot(event));
      timeline.appendChild(button);
    });
  }

  function formatClock(seconds) {
    const safe = Math.max(0, Number(seconds || 0));
    const minutes = Math.floor(safe / 60);
    const remain = Math.floor(safe % 60);
    return `${minutes}:${String(remain).padStart(2, "0")}`;
  }

  function stopCourtPlaybackLoop() {
    if (state.courtAnimationFrame) {
      window.cancelAnimationFrame(state.courtAnimationFrame);
      state.courtAnimationFrame = null;
    }
  }

  function startCourtPlaybackLoop() {
    stopCourtPlaybackLoop();
    const video = elements.analysisVideo;
    const tick = () => {
      if (!video || video.hidden || video.paused || video.ended) {
        stopCourtPlaybackLoop();
        return;
      }
      updatePlaybackMetrics(video.currentTime || 0, true);
      state.courtAnimationFrame = window.requestAnimationFrame(tick);
    };
    state.courtAnimationFrame = window.requestAnimationFrame(tick);
  }

  function updatePlaybackMetrics(currentTime = 0, animateCourt = false) {
    const duration = state.playbackDuration || Number(state.analysisReport?.video_metadata?.duration_sec || 0);
    const totalEvents = state.shotEvents.length || Number(state.analysisReport?.hit_count || 0);
    const passedEvents = state.shotEvents.filter((event) => event.time <= currentTime + 0.15);
    const currentEvent = [...passedEvents].reverse()[0] || state.shotEvents[0] || null;
    const progressRatio = duration > 0 ? Math.max(0, Math.min(1, currentTime / duration)) : 1;

    elements.metricFps.textContent = duration > 0
      ? `${formatClock(currentTime)} / ${formatClock(duration)}`
      : "总览";
    elements.metricDetections.textContent = `${passedEvents.length}/${totalEvents || 0}`;
    elements.metricConf.textContent = currentEvent && currentEvent.confidence
      ? `${(currentEvent.confidence * 100).toFixed(1)}%`
      : `${state.avgConf.toFixed(1)}%`;
    elements.metricLatency.textContent = currentEvent ? currentEvent.action : (state.analysisReport?.predicted_action || "--");

    if (elements.shotTimeline) {
      elements.shotTimeline.querySelectorAll(".timeline-shot.active").forEach((node) => node.classList.remove("active"));
      if (currentEvent) {
        const currentButton = elements.shotTimeline.querySelector(`[data-shot-index="${currentEvent.index}"]`);
        if (currentButton) currentButton.classList.add("active");
      }
    }

    if (animateCourt && state.footworkTrace.length) {
      drawCourt(state.radarData, state.footworkTrace, progressRatio);
    }
  }

  function updateMetrics() {
    elements.metricFps.textContent = state.fps;
    elements.metricDetections.textContent = state.detections;
    elements.metricConf.textContent = state.avgConf.toFixed(1) + "%";
    elements.metricLatency.textContent = `${state.latency}ms`;
  }

  function updateAnalysis() {
    // Generate random scores for demo
    const scores = {
      smooth: 70 + Math.floor(Math.random() * 25),
      accuracy: 65 + Math.floor(Math.random() * 30),
      coord: 60 + Math.floor(Math.random() * 35),
      foot: 55 + Math.floor(Math.random() * 40),
      wrist: 65 + Math.floor(Math.random() * 30),
      balance: 70 + Math.floor(Math.random() * 25),
    };

    elements.qualitySmooth.textContent = scores.smooth;
    elements.qualityAccuracy.textContent = scores.accuracy;
    elements.qualityCoord.textContent = scores.coord;
    elements.qualityFoot.textContent = scores.foot;
    elements.qualityWrist.textContent = scores.wrist;
    elements.qualityBalance.textContent = scores.balance;

    elements.barSmooth.style.width = scores.smooth + "%";
    elements.barAccuracy.style.width = scores.accuracy + "%";
    elements.barCoord.style.width = scores.coord + "%";
    elements.barFoot.style.width = scores.foot + "%";
    elements.barWrist.style.width = scores.wrist + "%";
    elements.barBalance.style.width = scores.balance + "%";

    state.radarData = [
      scores.smooth,
      scores.accuracy,
      scores.coord,
      scores.foot,
      scores.wrist,
      scores.balance,
    ];
    drawRadar(state.radarData);

    const totalScore = Math.round(
      (scores.smooth + scores.accuracy + scores.coord + scores.foot + scores.wrist + scores.balance) / 6
    );
    elements.actionScore.textContent = totalScore;
    elements.actionType.textContent = "高远球";

    const powerLevels = ["弱", "中等", "强", "极强"];
    elements.powerLevel.textContent = powerLevels[Math.floor(Math.random() * powerLevels.length)];
  }

  function addHistoryEntry() {
    const actions = ["高远球", "杀球", "吊球", "网前挑球", "平抽球", "搓球"];
    const now = new Date();
    const timeStr = now.toLocaleTimeString("zh-CN");
    const action = actions[Math.floor(Math.random() * actions.length)];
    const conf = (70 + Math.random() * 28).toFixed(1);
    const score = 60 + Math.floor(Math.random() * 38);
    const powers = ["弱", "中等", "强", "极强"];
    const power = powers[Math.floor(Math.random() * powers.length)];

    state.history.unshift({ timeStr, action, conf, score, power });
    if (state.history.length > 50) state.history.pop();

    const tbody = elements.historyTable;
    tbody.innerHTML = state.history
      .map(
        (h) => `<tr>
        <td>${h.timeStr}</td>
        <td>${h.action}</td>
        <td>${h.conf}%</td>
        <td>${h.score}</td>
        <td>${h.power}</td>
      </tr>`
      )
      .join("");
  }

  function updateReport() {
    elements.totalSessions.textContent = Math.floor(Math.random() * 20) + 1;
    elements.avgScore.textContent = (70 + Math.floor(Math.random() * 25));
    elements.bestAction.textContent = "杀球";
    elements.totalFrames.textContent = state.detections;

    const now = new Date();
    elements.reportDate.textContent = now.toLocaleDateString("zh-CN");
    elements.reportDuration.textContent = Math.floor(Math.random() * 60 + 15) + " 分钟";
    elements.reportActions.textContent = state.history.length + " 次";
    elements.reportHighlights.textContent = "杀球动作评分达到 95 分";
    elements.reportSuggestions.textContent = "建议加强网前小球的练习，提升搓球精度。";
  }

  function updateConfigOutput() {
    const config = {
      model: elements.modelSelect.value,
      confidence: parseFloat(elements.confThreshold.value),
      videoSource: elements.videoSource.value,
      inferenceBackend: elements.inferenceBackend.value,
      computeDevice: elements.computeDevice.value,
      inputResolution: parseInt(elements.inputResolution.value),
      modelPrecision: elements.modelPrecision.value,
      frameRate: parseInt(elements.frameRate.value),
      frameSkip: parseInt(elements.frameSkip.value),
      roi: {
        x1: parseInt(elements.roiX1.value),
        y1: parseInt(elements.roiY1.value),
        x2: parseInt(elements.roiX2.value),
        y2: parseInt(elements.roiY2.value),
      },
      saveDetection: elements.saveDetection.value === "true",
    };
    elements.configOutput.textContent = JSON.stringify(config, null, 2);
  }

  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    let container = document.querySelector(".toast-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "toast-container";
      document.body.appendChild(container);
    }
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  function downloadTextFile(filename, content, mimeType = "text/markdown;charset=utf-8") {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function safeReportText(element, fallback = "--") {
    return (element?.textContent || "").trim() || fallback;
  }

  function buildMarkdownReport() {
    const report = state.analysisReport || {};
    const topPredictions = (report.top_predictions || [])
      .map(([action, confidence], index) => `${index + 1}. ${action} - ${(Number(confidence || 0) * 100).toFixed(1)}%`)
      .join("\n");
    const shotEvents = (report.shot_events || [])
      .slice(0, 20)
      .map((event, index) => {
        const time = Number(event.time_sec || event.time || 0).toFixed(2);
        const action = event.shot_action || event.action || "击球片段";
        const confidence = event.shot_confidence ?? event.confidence;
        const score = event.quality_score != null ? `，质量 ${event.quality_score}` : "";
        const confText = confidence != null ? `，置信度 ${(Number(confidence) * 100).toFixed(1)}%` : "";
        return `${index + 1}. ${time}s：${action}${confText}${score}`;
      })
      .join("\n");
    const footwork = report.footwork_scores || {};
    const footworkText = Object.entries(footwork)
      .map(([name, value]) => `- ${name}: ${Number(value || 0).toFixed(1)}`)
      .join("\n");
    const generatedAt = new Date().toLocaleString("zh-CN");

    return `# 羽动智练训练报告

生成时间：${generatedAt}

## 本次概览

- 主要动作：${safeReportText(elements.bestAction)}
- 平均评分：${safeReportText(elements.avgScore)}
- 总动作数：${safeReportText(elements.reportActions)}
- 有效帧数：${safeReportText(elements.totalFrames)}
- 训练时长：${safeReportText(elements.reportDuration)}

## 本次亮点

${safeReportText(elements.reportHighlights)}

## 重点问题

${safeReportText(elements.reportIssues)}

## 改进建议

${safeReportText(elements.reportSuggestions)}

## 训练计划

${safeReportText(elements.reportPlan)}

## 复核建议

${safeReportText(elements.reportReview)}

## 动作 Top 分布

${topPredictions || "暂无动作分布数据"}

## 逐拍复盘

${shotEvents || "暂无逐拍数据"}

## 步伐评分

${footworkText || "暂无步伐评分数据"}
`;
  }

  function exportTrainingReport() {
    if (!state.analysisReport) {
      showToast("请先完成一次视频分析，再导出报告", "error");
      return;
    }
    const now = new Date();
    const stamp = [
      now.getFullYear(),
      String(now.getMonth() + 1).padStart(2, "0"),
      String(now.getDate()).padStart(2, "0"),
      String(now.getHours()).padStart(2, "0"),
      String(now.getMinutes()).padStart(2, "0"),
    ].join("");
    downloadTextFile(`badminton-training-report-${stamp}.md`, buildMarkdownReport());
    showToast("训练报告已生成并开始下载", "info");
  }

  function updateCoachContextStatus() {
    if (!elements.coachContextStatus) return;
    if (!state.analysisReport) {
      elements.coachContextStatus.textContent = "暂无训练报告";
      return;
    }
    const action = state.analysisReport.predicted_action || "已完成分析";
    const hits = state.analysisReport.hit_count || state.shotEvents.length || 0;
    elements.coachContextStatus.textContent = `${action} · ${hits} 次击球`;
  }

  function appendCoachMessage(role, content) {
    if (!elements.coachMessages) return null;
    const row = document.createElement("div");
    row.className = `coach-message ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "coach-avatar";
    avatar.textContent = role === "user" ? "我" : "教";

    const bubble = document.createElement("div");
    bubble.className = "coach-bubble";
    bubble.textContent = content;

    row.appendChild(avatar);
    row.appendChild(bubble);
    elements.coachMessages.appendChild(row);
    elements.coachMessages.scrollTop = elements.coachMessages.scrollHeight;
    return row;
  }

  function setCoachBusy(busy) {
    if (!elements.btnCoachSend) return;
    elements.btnCoachSend.disabled = busy;
    elements.btnCoachSend.textContent = busy ? "思考中..." : "发送";
  }

  function cleanCoachAnswer(text) {
    return String(text || "")
      .replace(/```[\s\S]*?```/g, "")
      .replace(/^#{1,6}\s*/gm, "")
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/\*(.*?)\*/g, "$1")
      .replace(/`([^`]*)`/g, "$1")
      .replace(/^\s*[-*]\s+/gm, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  function renderCoachStreamingBubble(bubble, steps, answer) {
    if (!bubble) return;
    const stepText = steps.length
      ? `思考进度：\n${steps.map((item) => `· ${item}`).join("\n")}\n\n`
      : "";
    const answerText = cleanCoachAnswer(answer);
    bubble.textContent = `${stepText}${answerText || "正在生成回答..."}`;
    elements.coachMessages.scrollTop = elements.coachMessages.scrollHeight;
  }

  async function readCoachStream(response, pendingBubble) {
    const reader = response.body?.getReader();
    if (!reader) {
      const data = await response.json().catch(() => ({}));
      return data.answer || "";
    }

    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let answer = "";
    let visibleAnswer = "";
    let queuedAnswer = "";
    const steps = [];
    let typeTimer = null;

    const startTyping = () => {
      if (typeTimer) return;
      typeTimer = window.setInterval(() => {
        if (!queuedAnswer) {
          window.clearInterval(typeTimer);
          typeTimer = null;
          return;
        }
        const take = Math.min(3, queuedAnswer.length);
        visibleAnswer += queuedAnswer.slice(0, take);
        queuedAnswer = queuedAnswer.slice(take);
        renderCoachStreamingBubble(pendingBubble, steps, visibleAnswer);
      }, 28);
    };

    const flushTyping = async () => {
      while (queuedAnswer) {
        const take = Math.min(8, queuedAnswer.length);
        visibleAnswer += queuedAnswer.slice(0, take);
        queuedAnswer = queuedAnswer.slice(take);
        renderCoachStreamingBubble(pendingBubble, steps, visibleAnswer);
        await new Promise((resolve) => window.setTimeout(resolve, 10));
      }
      if (typeTimer) {
        window.clearInterval(typeTimer);
        typeTimer = null;
      }
    };

    const handleEvent = (event, data) => {
      if (event === "status" && data.text) {
        steps.push(data.text);
        renderCoachStreamingBubble(pendingBubble, steps, visibleAnswer);
      } else if (event === "delta" && data.text) {
        answer += data.text;
        queuedAnswer += data.text;
        startTyping();
      } else if (event === "error") {
        throw new Error(data.message || "AI 教练生成失败");
      }
    };

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const packets = buffer.split("\n\n");
      buffer = packets.pop() || "";
      for (const packet of packets) {
        let event = "message";
        let dataText = "";
        packet.split("\n").forEach((line) => {
          if (line.startsWith("event:")) event = line.slice(6).trim();
          if (line.startsWith("data:")) dataText += line.slice(5).trim();
        });
        if (!dataText) continue;
        handleEvent(event, JSON.parse(dataText));
      }
    }
    await flushTyping();
    return cleanCoachAnswer(answer);
  }

  async function sendCoachQuestion(questionText = null) {
    const question = (questionText || elements.coachQuestion?.value || "").trim();
    if (!question) {
      showToast("请输入想问 AI 教练的问题", "error");
      return;
    }

    appendCoachMessage("user", question);
    state.coachHistory.push({ role: "user", content: question });
    if (elements.coachQuestion) elements.coachQuestion.value = "";

    const pending = appendCoachMessage("assistant", "思考进度：\n· 正在理解你的问题");
    const pendingBubble = pending?.querySelector(".coach-bubble");
    setCoachBusy(true);

    try {
      await ensureBackendReady();
      const response = await fetch(apiUrl("/api/coach/chat/stream"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: elements.coachProvider?.value || "qwen",
          question,
          history: state.coachHistory.slice(-8),
          report: state.analysisReport,
          use_report_context: Boolean(elements.coachUseReport?.checked),
          timeout: 90,
        }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
      const answer = await readCoachStream(response, pendingBubble) || "我暂时没有生成有效回答。";
      if (pendingBubble) pendingBubble.textContent = answer;
      state.coachHistory.push({ role: "assistant", content: answer });
    } catch (error) {
      const message = `AI教练暂时不可用：${formatFetchError(error)}`;
      if (pendingBubble) pendingBubble.textContent = message;
      state.coachHistory.push({ role: "assistant", content: message });
    } finally {
      setCoachBusy(false);
    }
  }

  // ---- Simulation: Start Detection ----
  let simInterval = null;

  elements.btnStart.addEventListener("click", async () => {
    if (state.detecting) return;
    if (!state.precheckPassed && state.precheckResult && state.precheckResult.overall === "fail") {
      showUploadHint("视频预检未通过，请重新拍摄后上传，或点击\"继续分析\"强制分析");
      return;
    }
    await runBackendAnalysis();
  });

  if (elements.btnProceedAnalyze) {
    elements.btnProceedAnalyze.addEventListener("click", async () => {
      if (state.detecting) return;
      await runBackendAnalysis();
    });
  }

  if (elements.btnReupload) {
    elements.btnReupload.addEventListener("click", () => {
      elements.videoUploadInput.click();
    });
  }

  if (elements.guideToggle && elements.shootingGuide) {
    elements.guideToggle.addEventListener("click", () => {
      elements.shootingGuide.classList.toggle("collapsed");
    });
  }

  if (elements.btnRefreshHistory) {
    elements.btnRefreshHistory.addEventListener("click", loadHistoryList);
  }

  elements.emptyMedia.addEventListener("click", () => {
    if (elements.videoSource.value === "camera") {
      showUploadHint("当前演示版暂未接入摄像头，请先选择文件上传");
      return;
    }
    elements.videoUploadInput.click();
  });

  elements.frameCanvasWrap.addEventListener("click", () => {
    if (!state.frameImage && elements.videoSource.value === "file") {
      elements.videoUploadInput.click();
    }
  });

  elements.emptyMedia.addEventListener("dragover", (event) => {
    event.preventDefault();
    elements.emptyMedia.classList.add("drag-over");
  });

  elements.emptyMedia.addEventListener("dragleave", () => {
    elements.emptyMedia.classList.remove("drag-over");
  });

  elements.emptyMedia.addEventListener("drop", (event) => {
    event.preventDefault();
    elements.emptyMedia.classList.remove("drag-over");
    const [file] = event.dataTransfer.files || [];
    loadUploadedVideo(file);
  });

  elements.videoUploadInput.addEventListener("change", (event) => {
    const [file] = event.target.files || [];
    loadUploadedVideo(file);
    event.target.value = "";
  });

  elements.btnStop.addEventListener("click", () => {
    if (!state.detecting) return;
    state.detecting = false;
    clearInterval(simInterval);
    simInterval = null;
    elements.btnStart.classList.remove("btn-secondary");
    elements.btnStart.classList.add("btn-primary");
    elements.btnStart.textContent = "开始检测";
  });

  elements.btnReset.addEventListener("click", () => {
    stopCourtPlaybackLoop();
    if (state.analysisTimerId) {
      window.clearInterval(state.analysisTimerId);
      state.analysisTimerId = null;
    }
    if (elements.analysisTimer) elements.analysisTimer.hidden = true;
    if (state.detecting) {
      clearInterval(simInterval);
      simInterval = null;
      state.detecting = false;
    }
    state.detections = 0;
    state.fps = 0;
    state.latency = 0;
    state.avgConf = 0;
    state.bbox = null;
    state.realVideoLoaded = false;
    state.frameImage = null;
    state.history = [];
    state.analysisReport = null;
    state.coachHistory = [];
    state.shotEvents = [];
    state.footworkTrace = [];
    state.radarData = [0, 0, 0, 0, 0, 0];
    state.precheckPassed = false;
    state.precheckResult = null;
    state.videoFile = null;

    hidePrecheckPanel();
    updateMetrics();
    elements.historyTable.innerHTML =
      '<tr><td colspan="5" style="text-align:center; color:var(--muted); padding:32px;">暂无检测记录</td></tr>';

    ctx.clearRect(0, 0, elements.frameCanvas.width, elements.frameCanvas.height);
    elements.emptyMedia.style.display = "flex";
    elements.frameCanvasWrap.style.display = "none";
    drawRadar(state.radarData);
    renderShotTimeline();

    elements.btnStart.classList.remove("btn-secondary");
    elements.btnStart.classList.add("btn-primary");
    elements.btnStart.textContent = "开始检测";
    setConnected(false);
    updateCoachContextStatus();
  });

  // ---- Config Events ----
  [
    elements.modelSelect,
    elements.confThreshold,
    elements.videoSource,
    elements.inferenceBackend,
    elements.computeDevice,
    elements.inputResolution,
    elements.modelPrecision,
    elements.frameRate,
    elements.frameSkip,
    elements.roiX1, elements.roiY1, elements.roiX2, elements.roiY2,
    elements.saveDetection,
  ].forEach((el) => {
    el.addEventListener("change", updateConfigOutput);
  });

  elements.btnSaveSettings.addEventListener("click", () => {
    updateConfigOutput();
    // Simulate save
    const toast = document.createElement("div");
    toast.className = "toast toast-success";
    toast.textContent = "设置已保存";
    let container = document.querySelector(".toast-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "toast-container";
      document.body.appendChild(container);
    }
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  });

  elements.btnResetSettings.addEventListener("click", () => {
    elements.modelSelect.value = "yolov8";
    elements.confThreshold.value = 0.5;
    elements.videoSource.value = "file";
    elements.inferenceBackend.value = "onnx";
    elements.computeDevice.value = "cpu";
    elements.inputResolution.value = "640";
    elements.modelPrecision.value = "fp32";
    elements.frameRate.value = "30";
    elements.frameSkip.value = "1";
    elements.roiX1.value = "0";
    elements.roiY1.value = "0";
    elements.roiX2.value = "640";
    elements.roiY2.value = "480";
    elements.saveDetection.value = "false";
    updateConfigOutput();
  });

  elements.btnExport.addEventListener("click", () => {
    exportTrainingReport();
  });

  if (elements.btnCoachSend) {
    elements.btnCoachSend.addEventListener("click", () => {
      sendCoachQuestion();
    });
  }

  if (elements.coachQuestion) {
    elements.coachQuestion.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        sendCoachQuestion();
      }
    });
  }

  document.querySelectorAll(".coach-prompt").forEach((button) => {
    button.addEventListener("click", () => {
      const prompt = button.dataset.prompt || button.textContent || "";
      if (elements.coachQuestion) {
        elements.coachQuestion.value = prompt;
        elements.coachQuestion.focus();
      }
    });
  });

  // ---- Sample Frame Generator ----
  function generateSampleFrame() {
    const canvas = elements.frameCanvas;
    const w = canvas.width;
    const h = canvas.height;

    // Dark background
    ctx.fillStyle = "#0d2219";
    ctx.fillRect(0, 0, w, h);

    // Court floor
    ctx.fillStyle = "#132e25";
    ctx.fillRect(60, 40, w - 120, h - 80);

    // Court lines
    ctx.strokeStyle = "#254b3e";
    ctx.lineWidth = 1.5;
    ctx.strokeRect(60, 40, w - 120, h - 80);
    ctx.beginPath();
    ctx.moveTo(w / 2, 40);
    ctx.lineTo(w / 2, h - 40);
    ctx.stroke();

    // Simulated person silhouette
    ctx.fillStyle = "#1a4035";
    ctx.beginPath();
    ctx.arc(w / 2, h * 0.35, 18, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillRect(w / 2 - 10, h * 0.38, 20, h * 0.28);

    // Racket
    ctx.strokeStyle = "#5eff9f";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(w / 2 + 12, h * 0.4);
    ctx.lineTo(w / 2 + 40, h * 0.25);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(w / 2 + 44, h * 0.23, 10, 0, Math.PI * 2);
    ctx.stroke();

    // Shuttlecock
    ctx.fillStyle = "#ffdf70";
    ctx.beginPath();
    ctx.arc(w / 2 + 80, h * 0.18, 5, 0, Math.PI * 2);
    ctx.fill();

    // Store as image for drawFrame
    const img = new Image();
    img.src = canvas.toDataURL();
    state.frameImage = img;
    state.bbox = { x1: 0.35, y1: 0.25, x2: 0.65, y2: 0.7 };
    drawFrame();
  }

  // ---- Init ----
  async function loadHistoryList() {
    if (!window.location.protocol.startsWith("http")) return;
    try {
      const resp = await fetch("/api/history?limit=50");
      if (!resp.ok) throw new Error("Failed to load history");
      const data = await resp.json();
      renderHistoryList(data.items || []);
      drawTrendChart(data.items || []);
    } catch (err) {
      console.error("Load history failed:", err);
    }
  }

  function renderHistoryList(items) {
    // Summary stats
    const totalSessions = items.length;
    const scores = items.filter((i) => i.avg_quality_score != null).map((i) => i.avg_quality_score);
    const avgScore = scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : "--";
    const totalShots = items.reduce((sum, i) => sum + (i.total_shots || 0), 0);
    const lastDate = items.length > 0 ? (items[0].created_at_display || items[0].created_at || "").slice(5, 16) : "--";

    elements.historyTotalSessions.textContent = totalSessions;
    elements.historyAvgScore.textContent = avgScore;
    elements.historyTotalShots.textContent = totalShots;
    elements.historyLastDate.textContent = lastDate;

    // List
    if (items.length === 0) {
      elements.historyList.innerHTML = '<div class="history-empty">暂无训练记录，完成一次视频分析后会显示在这里。</div>';
      return;
    }

    elements.historyList.innerHTML = "";
    items.forEach((item) => {
      const score = item.avg_quality_score;
      let scoreClass = "mid";
      if (score >= 75) scoreClass = "high";
      else if (score < 55) scoreClass = "low";
      const scoreDisplay = score != null ? Math.round(score) : "--";
      const duration = item.duration_seconds ? `${item.duration_seconds.toFixed(0)}秒` : "";
      const dateStr = (item.created_at_display || item.created_at || "").slice(5, 16);

      const div = document.createElement("div");
      div.className = "history-item";
      div.innerHTML = `
        <div class="history-item-date">${dateStr}</div>
        <div class="history-item-info">
          <div class="history-item-title">${item.video_name || "训练视频"}</div>
          <div class="history-item-meta">
            <span>击球 ${item.total_shots || 0} 次</span>
            ${duration ? `<span>时长 ${duration}</span>` : ""}
            ${item.dominant_action ? `<span>主要动作 ${item.dominant_action}</span>` : ""}
          </div>
        </div>
        <div class="history-item-score ${scoreClass}">${scoreDisplay}</div>
      `;
      if (item.annotated_video_url) {
        div.style.cursor = "pointer";
        div.addEventListener("click", () => {
          switchTab("report");
        });
      }
      elements.historyList.appendChild(div);
    });
  }

  function drawTrendChart(items) {
    const canvas = elements.trendChart;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = 200 * dpr;
    canvas.style.height = "200px";
    ctx.scale(dpr, dpr);
    const w = rect.width;
    const h = 200;
    const pad = { top: 20, right: 20, bottom: 30, left: 40 };
    const cw = w - pad.left - pad.right;
    const ch = h - pad.top - pad.bottom;

    ctx.clearRect(0, 0, w, h);

    // Background grid
    ctx.strokeStyle = "rgba(94,255,159,0.08)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = pad.top + (ch / 4) * i;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(pad.left + cw, y);
      ctx.stroke();
    }

    // Y-axis labels
    ctx.fillStyle = "#a8c9bb";
    ctx.font = '11px "JetBrains Mono", monospace';
    ctx.textAlign = "right";
    for (let i = 0; i <= 4; i++) {
      const val = 100 - i * 25;
      const y = pad.top + (ch / 4) * i;
      ctx.fillText(String(val), pad.left - 8, y + 4);
    }

    const scoredItems = items.filter((i) => i.avg_quality_score != null).reverse();
    if (scoredItems.length < 2) {
      ctx.fillStyle = "#a8c9bb";
      ctx.font = "13px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("完成至少2次训练后显示评分趋势", w / 2, h / 2);
      return;
    }

    const n = scoredItems.length;
    const points = scoredItems.map((item, idx) => {
      const x = pad.left + (cw / Math.max(n - 1, 1)) * idx;
      const score = Math.max(0, Math.min(100, item.avg_quality_score));
      const y = pad.top + ch - (ch * score / 100);
      return { x, y, score, item };
    });

    // Gradient fill
    const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + ch);
    grad.addColorStop(0, "rgba(94,255,159,0.3)");
    grad.addColorStop(1, "rgba(94,255,159,0.0)");
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.moveTo(points[0].x, pad.top + ch);
    points.forEach((p) => ctx.lineTo(p.x, p.y));
    ctx.lineTo(points[points.length - 1].x, pad.top + ch);
    ctx.closePath();
    ctx.fill();

    // Line
    ctx.strokeStyle = "#5eff9f";
    ctx.lineWidth = 2;
    ctx.beginPath();
    points.forEach((p, i) => {
      if (i === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    });
    ctx.stroke();

    // Points
    points.forEach((p) => {
      ctx.fillStyle = "#07130f";
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#5eff9f";
      ctx.lineWidth = 2;
      ctx.stroke();
    });

    // X-axis labels (dates)
    ctx.fillStyle = "#a8c9bb";
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.textAlign = "center";
    const labelStep = Math.max(1, Math.floor(n / 6));
    points.forEach((p, i) => {
      if (i % labelStep === 0 || i === n - 1) {
        const dateStr = (p.item.created_at_display || "").slice(5, 10);
        ctx.fillText(dateStr, p.x, h - 8);
      }
    });
  }

  function init() {
    drawCourt();
    drawRadar(state.radarData);
    updateConfigOutput();
    elements.emptyMedia.style.display = "flex";
    elements.frameCanvasWrap.style.display = "none";
    updateCoachContextStatus();
  }

  init();
})();
