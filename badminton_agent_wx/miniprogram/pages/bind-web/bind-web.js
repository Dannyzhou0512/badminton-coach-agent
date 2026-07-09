const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    bindCode: '',
    loading: false
  },

  onCodeInput(e) {
    let value = e.detail.value || '';
    value = value.replace(/[^a-zA-Z0-9]/g, '').toUpperCase().slice(0, 6);
    this.setData({ bindCode: value });
  },

  confirmBind() {
    const code = this.data.bindCode;
    if (code.length !== 6) {
      wx.showToast({ title: '请输入6位绑定码', icon: 'none' });
      return;
    }
    if (this.data.loading) return;

    this.setData({ loading: true });

    wx.login({
      success: (res) => {
        if (!res.code) {
          this.setData({ loading: false });
          wx.showToast({ title: '获取微信授权失败', icon: 'none' });
          return;
        }
        const bindCode = res.code;
        api.confirmBind(code, bindCode)
          .then(() => {
            // 绑定完成后，使用新的 js_code 重新登录，获取网页账号的 token
            wx.login({
              success: (loginRes) => {
                if (!loginRes.code) {
                  this.setData({ loading: false });
                  wx.showToast({ title: '绑定成功，请重新登录', icon: 'success' });
                  setTimeout(() => wx.navigateBack(), 1500);
                  return;
                }
                api.wechatLogin(loginRes.code)
                  .then((data) => {
                    app.setAuth(data.token, data.user);
                    this.setData({ loading: false });
                    wx.showToast({ title: '绑定成功', icon: 'success' });
                    setTimeout(() => wx.navigateBack(), 1500);
                  })
                  .catch((err) => {
                    this.setData({ loading: false });
                    wx.showToast({ title: err.message || '登录失败，请重新登录', icon: 'none' });
                  });
              },
              fail: () => {
                this.setData({ loading: false });
                wx.showToast({ title: '绑定成功，请重新登录', icon: 'success' });
                setTimeout(() => wx.navigateBack(), 1500);
              }
            });
          })
          .catch((err) => {
            this.setData({ loading: false });
            wx.showToast({ title: err.message || '绑定失败', icon: 'none', duration: 3000 });
          });
      },
      fail: () => {
        this.setData({ loading: false });
        wx.showToast({ title: '微信登录失败', icon: 'none' });
      }
    });
  }
});
