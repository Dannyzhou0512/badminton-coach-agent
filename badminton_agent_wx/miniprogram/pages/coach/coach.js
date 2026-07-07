const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    userInfo: null,
    messages: [],
    inputText: '',
    sending: false
  },

  onShow() {
    if (!app.checkLogin()) {
      wx.reLaunch({ url: '/pages/login/login' });
      return;
    }
    this.setData({ userInfo: app.globalData.userInfo });
  },

  onInputChange(e) {
    this.setData({ inputText: e.detail.value });
  },

  sendQuickQuestion(e) {
    const q = e.currentTarget.dataset.q;
    this.setData({ inputText: q }, () => {
      this.sendMessage();
    });
  },

  sendMessage() {
    const text = this.data.inputText.trim();
    if (!text || this.data.sending) return;

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: text
    };

    this.setData({
      messages: [...this.data.messages, userMsg],
      inputText: '',
      sending: true
    });

    api.sendCoachMessage(text, true, 'qwen')
      .then((data) => {
        const coachMsg = {
          id: Date.now() + 1,
          role: 'assistant',
          content: data.answer || data.response || data.message || '抱歉，我暂时无法回答这个问题。'
        };
        this.setData({
          messages: [...this.data.messages, coachMsg],
          sending: false
        });
      })
      .catch((err) => {
        const errorMsg = {
          id: Date.now() + 1,
          role: 'assistant',
          content: err.message || '网络错误，请稍后再试。'
        };
        this.setData({
          messages: [...this.data.messages, errorMsg],
          sending: false
        });
      });
  }
});
