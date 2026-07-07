const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    userInfo: null,
    greetingText: '开始训练',
    selectedVideo: '',
    videoPath: '',
    videoName: '',
    videoSize: '',
    videoDuration: '',
    analyzing: false,
    progress: 0,
    analyzingStage: '准备中...',
    presetIndex: 0,
    playerIndex: 0,
    presets: [
      { name: '自适应', value: 'adaptive' },
      { name: '比赛远景', value: 'match_far' },
      { name: '近景训练', value: 'training_close' },
      { name: '标准模式', value: 'standard' }
    ],
    playerOptions: [
      { name: '自动选择', value: 'largest' },
      { name: '最靠近镜头', value: 'closest' },
      { name: '左侧人物', value: 'left' },
      { name: '右侧人物', value: 'right' }
    ],
    presetNames: ['自适应', '比赛远景', '近景训练', '标准模式'],
    playerNames: ['自动选择', '最靠近镜头', '左侧人物', '右侧人物'],
    recentHistory: []
  },

  onLoad() {
    this.updateGreeting();
  },

  onShow() {
    if (!app.checkLogin()) {
      wx.reLaunch({ url: '/pages/login/login' });
      return;
    }
    this.setData({ userInfo: app.globalData.userInfo });
    this.updateGreeting();
    this.loadRecentHistory();
  },

  updateGreeting() {
    const user = app.globalData.userInfo;
    if (user && user.nickname) {
      this.setData({ greetingText: '你好，' + user.nickname });
    } else {
      this.setData({ greetingText: '开始训练' });
    }
  },

  loadRecentHistory() {
    api.getHistoryList()
      .then((data) => {
        if (data && data.items) {
          this.setData({
            recentHistory: data.items.slice(0, 3).map(item => {
              const shots = item.total_shots != null ? item.total_shots : 0;
              const dominant = item.dominant_action || '';
              let summary = '训练分析完成';
              if (dominant && shots > 0) {
                summary = '主要动作：' + dominant + '，共' + shots + '次击球';
              } else if (shots > 0) {
                summary = '共识别 ' + shots + ' 次击球';
              }
              return {
                id: item.id,
                date: this.formatDate(item.created_at),
                summary: summary
              };
            })
          });
        }
      })
      .catch(() => {});
  },

  formatDate(timestamp) {
    if (!timestamp) return '';
    let d;
    if (typeof timestamp === 'number') {
      d = new Date(timestamp * 1000);
    } else {
      d = new Date(timestamp.replace(' ', 'T'));
    }
    if (isNaN(d.getTime())) return '';
    const month = d.getMonth() + 1;
    const day = d.getDate();
    const hours = d.getHours();
    const mins = String(d.getMinutes()).padStart(2, '0');
    return month + '/' + day + ' ' + hours + ':' + mins;
  },

  chooseVideo() {
    if (this.data.analyzing) return;

    wx.showActionSheet({
      itemList: ['拍摄视频', '从相册选择'],
      success: (res) => {
        const sourceType = res.tapIndex === 0 ? ['camera'] : ['album'];
        this.doChooseVideo(sourceType);
      }
    });
  },

  doChooseVideo(sourceType) {
    const sourceName = sourceType[0] === 'camera' ? '拍摄' : '相册';

    wx.chooseVideo({
      sourceType: sourceType,
      compressed: false,
      maxDuration: 300,
      camera: 'back',
      success: (res) => {
        const sizeMB = (res.size / (1024 * 1024)).toFixed(1);
        const durSec = res.duration ? Math.round(res.duration) + '秒' : '';
        this.setData({
          selectedVideo: res.tempFilePath,
          videoPath: res.tempFilePath,
          videoName: '训练视频',
          videoSize: sizeMB + 'MB' + (durSec ? ' · ' + durSec : ''),
          videoDuration: durSec
        });
      },
      fail: (err) => {
        const isCancel = err && err.errMsg && (err.errMsg.indexOf('cancel') > -1 || err.errMsg.indexOf('fail cancel') > -1);
        if (!isCancel) {
          console.error('wx.chooseVideo fail:', err);
          this.tryChooseMedia(sourceType, sourceName);
        }
      }
    });
  },

  tryChooseMedia(sourceType, sourceName) {
    try {
      wx.chooseMedia({
        count: 1,
        mediaType: ['video'],
        sourceType: sourceType,
        maxDuration: 300,
        camera: 'back',
        success: (res) => {
          const file = res.tempFiles[0];
          const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
          const durSec = file.duration ? Math.round(file.duration / 1000) + '秒' : '';
          this.setData({
            selectedVideo: file.tempFilePath,
            videoPath: file.tempFilePath,
            videoName: '训练视频',
            videoSize: sizeMB + 'MB' + (durSec ? ' · ' + durSec : ''),
            videoDuration: durSec
          });
        },
        fail: (err2) => {
          console.error('wx.chooseMedia fail:', err2);
          const detail = (err2 && err2.errMsg) ? err2.errMsg : '未知错误';
          wx.showModal({
            title: '选择视频失败',
            content: '无法从' + sourceName + '选择视频。\n错误信息：' + detail + '\n\n请在真机或真机调试中测试此功能，模拟器可能不支持视频选择。',
            showCancel: false,
            confirmText: '知道了'
          });
        }
      });
    } catch (e) {
      console.error('chooseMedia exception:', e);
      wx.showModal({
        title: '选择视频失败',
        content: '当前环境不支持视频选择，请在真机中测试。',
        showCancel: false
      });
    }
  },

  onPresetChange(e) {
    this.setData({ presetIndex: parseInt(e.detail.value) });
  },

  onPlayerChange(e) {
    this.setData({ playerIndex: parseInt(e.detail.value) });
  },

  startAnalysis() {
    if (!this.data.selectedVideo || this.data.analyzing) return;

    this.setData({
      analyzing: true,
      progress: 3,
      analyzingStage: '正在上传视频...'
    });

    const fakeStages = [
      { p: 10, msg: '视频上传完成...' },
      { p: 20, msg: '读取视频元数据...' },
      { p: 35, msg: '正在提取姿态数据...' },
      { p: 55, msg: '正在识别击球动作...' },
      { p: 70, msg: '正在追踪步伐...' },
      { p: 82, msg: 'AI正在分析动作...' },
      { p: 92, msg: '生成分析报告...' }
    ];

    let fakeIdx = 0;
    const fakeTimer = setInterval(() => {
      if (fakeIdx < fakeStages.length && this.data.analyzing) {
        this.setData({
          progress: fakeStages[fakeIdx].p,
          analyzingStage: fakeStages[fakeIdx].msg
        });
        fakeIdx++;
      }
    }, 2500);

    api.analyzeVideo(
      this.data.videoPath,
      {
        analysis_preset: this.data.presets[this.data.presetIndex].value,
        target_player: this.data.playerOptions[this.data.playerIndex].value
      },
      (percent, msg) => {
        this.setData({ progress: Math.max(this.data.progress, percent) });
      }
    )
      .then((data) => {
        clearInterval(fakeTimer);
        this.setData({
          analyzing: false,
          progress: 100,
          analyzingStage: '分析完成',
          selectedVideo: '',
          videoPath: '',
          videoName: '',
          videoSize: ''
        });

        wx.showToast({ title: '分析完成', icon: 'success' });

        setTimeout(() => {
          this.loadRecentHistory();
          wx.switchTab({ url: '/pages/analysis/analysis' });
        }, 1000);
      })
      .catch((err) => {
        clearInterval(fakeTimer);
        this.setData({ analyzing: false });
        wx.showModal({
          title: '分析失败',
          content: err.message || '视频分析失败，请重试',
          showCancel: false
        });
      });
  },

  goToHistory() {
    wx.switchTab({ url: '/pages/analysis/analysis' });
  },

  goToResult(e) {
    const id = e.currentTarget.dataset.id;
    if (id) {
      wx.navigateTo({ url: '/pages/analysis/analysis?sessionId=' + id });
    }
  }
});
