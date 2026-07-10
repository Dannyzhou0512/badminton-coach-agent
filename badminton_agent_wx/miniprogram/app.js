// 公网体验地址（cpolar内网穿透）- 任何人任何网络都能访问
const API_BASE = 'https://16456551.r18.vip.cpolar.cn';
// 局域网调试地址（手机和电脑连同一WiFi时使用）
// const API_BASE = 'http://10.236.186.180:8000';

App({
  globalData: {
    userInfo: null,
    token: null,
    apiBase: API_BASE,
    language: 'zh'
  },

  onLaunch() {
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('userInfo');
    const language = wx.getStorageSync('language');
    if (token) {
      this.globalData.token = token;
    }
    if (userInfo) {
      this.globalData.userInfo = userInfo;
    }
    if (language) {
      this.globalData.language = language;
    }
  },

  checkLogin() {
    return !!this.globalData.token;
  },

  setAuth(token, user) {
    this.globalData.token = token;
    this.globalData.userInfo = user;
    wx.setStorageSync('token', token);
    wx.setStorageSync('userInfo', user);
  },

  clearAuth() {
    this.globalData.token = null;
    this.globalData.userInfo = null;
    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
  }
});
