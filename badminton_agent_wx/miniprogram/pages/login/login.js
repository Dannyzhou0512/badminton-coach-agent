const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    activeTab: 'wechat',
    username: '',
    password: '',
    errorMsg: '',
    loading: false,
    loadingText: ''
  },

  onLoad() {
    if (app.checkLogin()) {
      wx.switchTab({ url: '/pages/training/training' });
    }
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({
      activeTab: tab,
      errorMsg: ''
    });
  },

  onUsernameInput(e) {
    this.setData({ username: e.detail.value });
  },

  onPasswordInput(e) {
    this.setData({ password: e.detail.value });
  },

  handleWechatLogin() {
    if (this.data.loading) return;

    this.setData({ loading: true, loadingText: '正在登录...' });

    wx.login({
      success: (res) => {
        if (res.code) {
          this.doWechatLogin(res.code);
        } else {
          this.setData({ loading: false });
          wx.showToast({ title: '获取微信授权失败', icon: 'none' });
        }
      },
      fail: () => {
        this.setData({ loading: false });
        wx.showToast({ title: '微信登录失败', icon: 'none' });
      }
    });
  },

  doWechatLogin(code) {
    let nickname = '';
    let avatar = '';

    wx.getUserProfile({
      desc: '用于完善用户资料',
      success: (profileRes) => {
        nickname = profileRes.userInfo.nickName;
        avatar = profileRes.userInfo.avatarUrl;
        this.sendWechatLoginRequest(code, nickname, avatar);
      },
      fail: () => {
        this.sendWechatLoginRequest(code, '', '');
      }
    });
  },

  sendWechatLoginRequest(code, nickname, avatar) {
    api.wechatLogin(code, nickname, avatar)
      .then((data) => {
        app.setAuth(data.token, data.user);
        wx.showToast({ title: '登录成功', icon: 'success' });
        setTimeout(() => {
          wx.switchTab({ url: '/pages/training/training' });
        }, 500);
      })
      .catch((err) => {
        this.setData({ loading: false });
        wx.showToast({ title: err.message || '登录失败', icon: 'none' });
      });
  },

  handleAccountLogin() {
    if (this.data.loading) return;

    const { username, password } = this.data;
    if (!username.trim() || !password) {
      this.setData({ errorMsg: '请输入用户名和密码' });
      return;
    }

    this.setData({ loading: true, errorMsg: '', loadingText: '正在登录...' });

    api.login(username, password)
      .then((data) => {
        app.setAuth(data.token, data.user);
        wx.showToast({ title: '登录成功', icon: 'success' });
        setTimeout(() => {
          wx.switchTab({ url: '/pages/training/training' });
        }, 500);
      })
      .catch((err) => {
        this.setData({ loading: false, errorMsg: err.message || '登录失败' });
      });
  },

  goToRegister() {
    wx.showModal({
      title: '注册账号',
      editable: true,
      placeholderText: '请输入用户名',
      success: (res) => {
        if (res.confirm && res.content) {
          this.showRegisterPasswordModal(res.content);
        }
      }
    });
  },

  showRegisterPasswordModal(username) {
    wx.showModal({
      title: '设置密码',
      editable: true,
      placeholderText: '请输入密码（至少6位）',
      success: (res) => {
        if (res.confirm && res.content && res.content.length >= 6) {
          this.doRegister(username, res.content);
        } else if (res.confirm) {
          wx.showToast({ title: '密码至少6位', icon: 'none' });
        }
      }
    });
  },

  doRegister(username, password) {
    this.setData({ loading: true, loadingText: '正在注册...' });

    api.register(username, password, username)
      .then((data) => {
        app.setAuth(data.token, data.user);
        wx.showToast({ title: '注册成功', icon: 'success' });
        setTimeout(() => {
          wx.switchTab({ url: '/pages/training/training' });
        }, 500);
      })
      .catch((err) => {
        this.setData({ loading: false });
        wx.showToast({ title: err.message || '注册失败', icon: 'none' });
      });
  }
});
