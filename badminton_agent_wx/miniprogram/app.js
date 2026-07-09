// 真机预览/调试时，请把 API_BASE 改成你电脑的局域网 IP，例如 'http://192.168.1.5:8000'
// 电脑和手机必须连接同一个 WiFi；后端服务需要监听 0.0.0.0:8000
const API_BASE = 'http://10.236.186.180:8000';

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
