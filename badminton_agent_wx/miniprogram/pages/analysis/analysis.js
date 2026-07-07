const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    hasData: false,
    loading: false,
    currentResult: null,
    report: null,
    apiBase: app.globalData.apiBase,
    heatmapData: [],
    hasFootwork: false,
    actionStats: [],
    shotEvents: [],
    coachReport: null,
    qualitySummary: null,
    footworkScores: null,
    videoMetadata: null,
    activeTab: 'overview',
    tabs: [
      { key: 'overview', name: '概览' },
      { key: 'shots', name: '击球' },
      { key: 'footwork', name: '步伐' },
      { key: 'coach', name: '教练报告' }
    ]
  },

  onLoad(options) {
    this.sessionId = (options && options.sessionId) ? parseInt(options.sessionId, 10) : null;
  },

  onShow() {
    if (!app.checkLogin()) {
      wx.reLaunch({ url: '/pages/login/login' });
      return;
    }
    if (this.sessionId) {
      this.loadDetail(this.sessionId);
    } else {
      this.loadLatestResult();
    }
  },

  loadDetail(sessionId) {
    this.setData({ loading: true });
    api.getHistoryDetail(sessionId)
      .then((detail) => {
        this.setData({ loading: false, hasData: true });
        this.processReport(detail);
      })
      .catch((err) => {
        this.setData({ loading: false, hasData: false });
        console.error('Load detail failed:', err);
        wx.showToast({ title: '加载详情失败', icon: 'none' });
      });
  },

  switchTab(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({ activeTab: key });
  },

  loadLatestResult() {
    this.setData({ loading: true });
    api.getHistoryList()
      .then((data) => {
        const items = data.items || [];
        if (items.length === 0) {
          this.setData({ hasData: false, loading: false });
          return;
        }
        const latest = items[0];
        return api.getHistoryDetail(latest.id);
      })
      .then((detail) => {
        if (!detail) return;
        this.setData({ loading: false, hasData: true });
        this.processReport(detail);
      })
      .catch((err) => {
        this.setData({ loading: false });
        console.error('Load latest result failed:', err);
      });
  },

  processReport(detail) {
    const report = detail.report || {};
    const apiBase = app.globalData.apiBase;

    const annotatedVideoUrl = detail.annotated_video_url
      ? (detail.annotated_video_url.indexOf('http') === 0 ? detail.annotated_video_url : apiBase + detail.annotated_video_url)
      : '';
    const annotatedPreviewUrl = detail.annotated_preview_url
      ? (detail.annotated_preview_url.indexOf('http') === 0 ? detail.annotated_preview_url : apiBase + detail.annotated_preview_url)
      : '';

    const vm = report.video_metadata || {};
    const durationSeconds = detail.duration_seconds != null ? detail.duration_seconds : (vm.duration_seconds || vm.duration_sec || 0);
    const qs = report.quality_summary || {};
    const totalShots = detail.total_shots != null ? detail.total_shots : (qs.shot_count || 0);
    const avgScore = detail.avg_quality_score != null ? detail.avg_quality_score : (qs.avg_quality_score || qs.overall_score || 0);
    const overallScore = qs.overall_score != null ? qs.overall_score : avgScore;

    this.setData({
      currentResult: {
        id: detail.id,
        videoName: detail.video_name || '训练视频',
        duration: durationSeconds > 0 ? Math.round(durationSeconds) + '秒' : '--',
        totalShots: totalShots,
        avgScore: avgScore > 0 ? Math.round(avgScore) : 0,
        overallScore: overallScore > 0 ? Math.round(overallScore) : 0,
        dominantAction: detail.dominant_action || '未知',
        annotatedVideoUrl: annotatedVideoUrl,
        annotatedPreviewUrl: annotatedPreviewUrl,
        createdAt: detail.created_at_display || detail.created_at || ''
      },
      report: report,
      qualitySummary: qs,
      footworkScores: report.footwork_scores || {},
      videoMetadata: vm
    });

    this.processFootworkTrace(report.footwork_trace || []);
    this.processShotEvents(report.shot_events || []);
    this.processCoachReport(report.coach_report || {});
  },

  processFootworkTrace(trace) {
    if (!trace || trace.length === 0) {
      this.setData({ heatmapData: [], hasFootwork: false });
      return;
    }

    const points = trace.map((p, idx) => ({
      x: p.x || 0,
      y: p.y || 0,
      time: p.time_sec || idx * 0.1,
      intensity: 0.3 + Math.min(0.7, idx / trace.length)
    }));

    this.setData({
      heatmapData: points.slice(-120),
      hasFootwork: true
    });

    // Draw canvas after DOM update
    setTimeout(() => {
      this.drawFootworkCanvas(points);
    }, 100);
  },

  drawFootworkCanvas(points) {
    const query = wx.createSelectorQuery().in(this);
    query.select('#footworkCanvas').fields({ node: true, size: true }).exec((res) => {
      if (!res || !res[0] || !res[0].node) {
        // Fallback to legacy canvas API
        this.drawLegacyFootworkCanvas(points);
        return;
      }
      const canvas = res[0].node;
      const ctx = canvas.getContext('2d');
      const width = res[0].width;
      const height = res[0].height;
      const dpr = wx.getSystemInfoSync().pixelRatio;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.scale(dpr, dpr);

      this.renderCourt(ctx, width, height);
      this.renderTrajectory(ctx, points, width, height);
      this.renderHeatPoints(ctx, points, width, height);
    });
  },

  drawLegacyFootworkCanvas(points) {
    const ctx = wx.createCanvasContext('footworkCanvas', this);
    const width = 320;
    const height = 360;
    this.renderCourt(ctx, width, height);
    this.renderTrajectory(ctx, points, width, height);
    this.renderHeatPoints(ctx, points, width, height);
    ctx.draw();
  },

  renderCourt(ctx, width, height) {
    // Clear
    ctx.clearRect(0, 0, width, height);

    // Background
    ctx.fillStyle = 'rgba(16, 42, 30, 0.7)';
    ctx.fillRect(0, 0, width, height);

    // Court border
    ctx.strokeStyle = 'rgba(94, 255, 159, 0.6)';
    ctx.lineWidth = 2;
    ctx.strokeRect(10, 10, width - 20, height - 20);

    // Service line (front service line ~ 1.98m from net in half court)
    ctx.strokeStyle = 'rgba(94, 255, 159, 0.35)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(10, height * 0.3);
    ctx.lineTo(width - 10, height * 0.3);
    ctx.stroke();

    // Doubles service line
    ctx.beginPath();
    ctx.moveTo(10, height * 0.55);
    ctx.lineTo(width - 10, height * 0.55);
    ctx.stroke();

    // Center line
    ctx.beginPath();
    ctx.moveTo(width / 2, 10);
    ctx.lineTo(width / 2, height - 10);
    ctx.stroke();

    // Labels
    ctx.fillStyle = 'rgba(94, 255, 159, 0.7)';
    ctx.font = '10px sans-serif';
    ctx.fillText('NET', 14, 24);
    ctx.fillText('FRONT', 14, height * 0.25);
    ctx.fillText('MID', 14, height * 0.45);
    ctx.fillText('BACK', 14, height * 0.85);
  },

  renderTrajectory(ctx, points, width, height) {
    if (points.length < 2) return;
    const marginX = 10;
    const marginY = 10;
    const courtW = width - marginX * 2;
    const courtH = height - marginY * 2;

    ctx.lineWidth = 2;
    for (let i = 1; i < points.length; i++) {
      const p1 = points[i - 1];
      const p2 = points[i];
      const alpha = Math.max(0.1, i / points.length);
      ctx.strokeStyle = `rgba(94, 255, 159, ${alpha})`;
      ctx.beginPath();
      ctx.moveTo(marginX + p1.x * courtW, marginY + p1.y * courtH);
      ctx.lineTo(marginX + p2.x * courtW, marginY + p2.y * courtH);
      ctx.stroke();
    }
  },

  renderHeatPoints(ctx, points, width, height) {
    const marginX = 10;
    const marginY = 10;
    const courtW = width - marginX * 2;
    const courtH = height - marginY * 2;

    for (let i = 0; i < points.length; i++) {
      const p = points[i];
      const x = marginX + p.x * courtW;
      const y = marginY + p.y * courtH;
      const radius = 3 + p.intensity * 5;
      const alpha = 0.2 + p.intensity * 0.5;

      const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
      gradient.addColorStop(0, `rgba(255, 100, 100, ${alpha})`);
      gradient.addColorStop(0.6, `rgba(255, 80, 80, ${alpha * 0.6})`);
      gradient.addColorStop(1, 'rgba(255, 60, 60, 0)');

      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fill();
    }
  },

  processShotEvents(shotEvents) {
    if (!shotEvents || shotEvents.length === 0) {
      this.setData({ shotEvents: [], actionStats: [] });
      return;
    }

    // Action counts
    const counts = {};
    shotEvents.forEach(s => {
      const name = s.shot_action || s.action_name || s.predicted_action || '未知动作';
      counts[name] = (counts[name] || 0) + 1;
    });

    const maxCount = Math.max(...Object.values(counts), 1);
    const actionStats = Object.keys(counts).map(name => ({
      name: name,
      count: counts[name],
      percent: Math.round((counts[name] / maxCount) * 100)
    }));

    // Recent shot events (last 20)
    const events = shotEvents.slice(-20).reverse().map((s, idx) => ({
      id: idx,
      time: s.time_sec !== undefined ? s.time_sec.toFixed(2) + 's' : '#',
      action: s.shot_action || s.action_name || s.predicted_action || '未知动作',
      quality: (s.quality && s.quality.overall != null) ? s.quality.overall : (s.quality_score || 0),
      confidence: s.confidence ? Math.round(s.confidence * 100) : 0
    }));

    this.setData({
      actionStats: actionStats,
      shotEvents: events
    });
  },

  processCoachReport(coachReport) {
    this.setData({ coachReport: coachReport });
  },

  previewAnnotatedVideo() {
    const url = this.data.currentResult && this.data.currentResult.annotatedVideoUrl;
    if (!url) {
      wx.showToast({ title: '标注视频未生成', icon: 'none' });
      return;
    }
    wx.previewMedia({
      sources: [{ url: url, type: 'video' }]
    });
  },

  goToTraining() {
    wx.switchTab({ url: '/pages/training/training' });
  },

  playVideo() {
    // Handled by video component controls
  },

  onVideoError(e) {
    console.error('Annotated video playback error:', e);
    wx.showModal({
      title: '视频播放失败',
      content: '标注视频可能因网络、域名白名单或编码格式无法播放。请确保开发工具已开启「不校验合法域名」，真机调试时请使用电脑局域网 IP 而非 127.0.0.1。',
      showCancel: false,
      confirmText: '知道了'
    });
  }
});
