const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    historyList: [],
    loading: false
  },

  onShow() {
    if (!app.checkLogin()) {
      wx.reLaunch({ url: '/pages/login/login' });
      return;
    }
    this.loadHistory();
  },

  loadHistory() {
    this.setData({ loading: true });
    api.getHistoryList()
      .then((data) => {
        this.setData({ loading: false });
        const items = data.items || [];
        if (items.length === 0) {
          this.setData({ historyList: [] });
          return;
        }
        const list = items.map(item => {
          const durationSec = item.duration_seconds != null ? item.duration_seconds : 0;
          const durationText = durationSec > 0 ? Math.round(durationSec) + 's' : '--';
          const shots = item.total_shots != null ? item.total_shots : 0;
          const score = item.avg_quality_score != null ? Math.round(item.avg_quality_score) : 0;
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
            score: score,
            summary: summary,
            stats: {
              shots: shots,
              duration: durationText,
              movement: score > 0 ? score + '分' : '--'
            }
          };
        });
        this.setData({ historyList: list });
      })
      .catch((err) => {
        this.setData({ loading: false });
        console.error('Load history failed:', err);
        wx.showToast({ title: '加载失败', icon: 'none' });
      });
  },

  formatDate(timestamp) {
    if (!timestamp) {
      const d = new Date();
      return (d.getMonth() + 1) + '月' + d.getDate() + '日 ' + d.getHours() + ':' + String(d.getMinutes()).padStart(2, '0');
    }
    let d;
    if (typeof timestamp === 'number') {
      d = new Date(timestamp * 1000);
    } else {
      d = new Date(timestamp.replace(' ', 'T'));
    }
    if (isNaN(d.getTime())) {
      d = new Date();
    }
    return (d.getMonth() + 1) + '月' + d.getDate() + '日 ' + d.getHours() + ':' + String(d.getMinutes()).padStart(2, '0');
  },

  viewDetail(e) {
    const id = e.currentTarget.dataset.id;
    if (id) {
      wx.navigateTo({ url: '/pages/analysis/analysis?sessionId=' + id });
    }
  }
});
