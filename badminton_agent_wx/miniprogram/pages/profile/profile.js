const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    userInfo: null,
    stats: null,
    currentLang: 'zh',
    currentLangName: '简体中文',
    displayNickname: '未登录',
    displayUsername: 'guest',
    languages: [
      { code: 'zh', name: '简体中文' },
      { code: 'en', name: 'English' },
      { code: 'ja', name: '日本語' },
      { code: 'ko', name: '한국어' },
      { code: 'id', name: 'Bahasa Indonesia' }
    ],
    editModalVisible: false,
    editNickname: '',
    editAvatar: '',
    editAvatarUrl: '',
    editLoading: false
  },

  onShow() {
    if (!app.checkLogin()) {
      wx.reLaunch({ url: '/pages/login/login' });
      return;
    }
    this.loadUserInfo();
    this.loadStats();
    const lang = app.globalData.language || 'zh';
    const langItem = this.data.languages.find(l => l.code === lang);
    this.setData({
      currentLang: lang,
      currentLangName: langItem ? langItem.name : '简体中文'
    });
  },

  getAvatarUrl(avatar) {
    if (!avatar) return '';
    if (avatar.indexOf('http') === 0) return avatar;
    return app.globalData.apiBase + avatar;
  },

  updateDisplayInfo(user) {
    if (user) {
      const nickname = user.nickname || user.username || '用户';
      this.setData({
        displayNickname: nickname,
        displayUsername: user.username || 'user',
        'userInfo.nicknameInitial': nickname ? nickname.charAt(0) : '🏸',
        'userInfo.avatarUrl': this.getAvatarUrl(user.avatar)
      });
    } else {
      this.setData({
        displayNickname: '未登录',
        displayUsername: 'guest'
      });
    }
  },

  loadUserInfo() {
    api.getUserInfo()
      .then((data) => {
        app.globalData.userInfo = data;
        wx.setStorageSync('userInfo', data);
        this.setData({ userInfo: data });
        this.updateDisplayInfo(data);
      })
      .catch(() => {});
  },

  loadStats() {
    api.getHistoryList()
      .then((data) => {
        const items = data.items || [];
        const totalShots = items.reduce((sum, item) => sum + (item.total_shots || 0), 0);
        const avgScore = items.length > 0
          ? Math.round(items.reduce((sum, item) => sum + (item.avg_quality_score || 80), 0) / items.length)
          : 0;
        this.setData({
          stats: {
            totalSessions: items.length,
            totalShots: totalShots,
            avgScore: avgScore
          }
        });
      })
      .catch(() => {
        this.setData({
          stats: {
            totalSessions: 0,
            totalShots: 0,
            avgScore: 0
          }
        });
      });
  },

  editProfile() {
    const user = this.data.userInfo;
    if (!user) return;
    this.setData({
      editModalVisible: true,
      editNickname: user.nickname || '',
      editAvatar: user.avatar || '',
      editAvatarUrl: this.getAvatarUrl(user.avatar)
    });
  },

  closeEditModal() {
    this.setData({ editModalVisible: false });
  },

  preventClose() {
    // Prevent modal mask tap from closing when tapping inside modal
  },

  onNicknameInput(e) {
    this.setData({ editNickname: e.detail.value });
  },

  chooseAvatarSource() {
    wx.showActionSheet({
      itemList: ['使用微信头像', '从相册上传'],
      success: (res) => {
        if (res.tapIndex === 0) {
          this.useWechatAvatar();
        } else {
          this.chooseAvatarFromAlbum();
        }
      }
    });
  },

  useWechatAvatar() {
    wx.getUserProfile({
      desc: '用于获取微信头像',
      success: (profileRes) => {
        const avatarUrl = profileRes.userInfo.avatarUrl;
        if (avatarUrl) {
          this.setData({ editAvatar: avatarUrl, editAvatarUrl: avatarUrl });
        }
      },
      fail: () => {
        wx.showToast({ title: '获取微信头像失败', icon: 'none' });
      }
    });
  },

  chooseAvatarFromAlbum() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album'],
      success: (res) => {
        const tempFilePath = res.tempFiles[0].tempFilePath;
        this.uploadAvatarFile(tempFilePath);
      },
      fail: () => {
        wx.showToast({ title: '选择图片失败', icon: 'none' });
      }
    });
  },

  uploadAvatarFile(filePath) {
    this.setData({ editLoading: true });
    api.uploadAvatar(filePath)
      .then((data) => {
        this.setData({
          editAvatar: data.avatar_url,
          editAvatarUrl: this.getAvatarUrl(data.avatar_url),
          editLoading: false
        });
        wx.showToast({ title: '头像上传成功', icon: 'success' });
      })
      .catch((err) => {
        this.setData({ editLoading: false });
        wx.showToast({ title: err.message || '上传失败', icon: 'none' });
      });
  },

  saveProfile() {
    const nickname = this.data.editNickname.trim();
    if (!nickname) {
      wx.showToast({ title: '昵称不能为空', icon: 'none' });
      return;
    }
    this.setData({ editLoading: true });
    api.updateProfile(nickname, this.data.editAvatar)
      .then((data) => {
        app.globalData.userInfo = data;
        wx.setStorageSync('userInfo', data);
        this.setData({
          userInfo: data,
          editModalVisible: false,
          editLoading: false
        });
        this.updateDisplayInfo(data);
        wx.showToast({ title: '保存成功', icon: 'success' });
      })
      .catch((err) => {
        this.setData({ editLoading: false });
        wx.showToast({ title: err.message || '保存失败', icon: 'none' });
      });
  },

  goToHistory() {
    wx.navigateTo({ url: '/pages/history/history' });
  },

  showLanguageSelector() {
    const names = this.data.languages.map(l => l.name);
    wx.showActionSheet({
      itemList: names,
      success: (res) => {
        const lang = this.data.languages[res.tapIndex];
        app.globalData.language = lang.code;
        wx.setStorageSync('language', lang.code);
        this.setData({
          currentLang: lang.code,
          currentLangName: lang.name
        });
        api.updateProfile(null, null)
          .then(() => {})
          .catch(() => {});
        wx.showToast({ title: '语言已切换', icon: 'success' });
      }
    });
  },

  showAbout() {
    wx.showModal({
      title: '关于羽动智练',
      content: '羽动智练是一款AI驱动的羽毛球智能训练助手，通过计算机视觉和深度学习技术，为羽毛球爱好者提供动作分析、步伐追踪、AI教练指导等功能。\n\n两端账号互通，网页版与小程序数据同步。',
      showCancel: false,
      confirmText: '知道了'
    });
  },

  bindWechat() {
    wx.login({
      success: (res) => {
        if (res.code) {
          api.bindWechat(res.code)
            .then((data) => {
              app.globalData.userInfo = data;
              wx.setStorageSync('userInfo', data);
              this.setData({ userInfo: data });
              this.updateDisplayInfo(data);
              wx.showToast({ title: '绑定成功', icon: 'success' });
            })
            .catch((err) => {
              wx.showToast({ title: err.message || '绑定失败', icon: 'none' });
            });
        }
      }
    });
  },

  unbindWechat() {
    wx.showModal({
      title: '解绑微信',
      content: '解绑后将无法使用微信一键登录，确定继续吗？',
      success: (res) => {
        if (res.confirm) {
          api.unbindWechat()
            .then((data) => {
              app.globalData.userInfo = data;
              wx.setStorageSync('userInfo', data);
              this.setData({ userInfo: data });
              this.updateDisplayInfo(data);
              wx.showToast({ title: '解绑成功', icon: 'success' });
            })
            .catch((err) => {
              wx.showToast({ title: err.message || '解绑失败', icon: 'none' });
            });
        }
      }
    });
  },

  switchAccount() {
    wx.showModal({
      title: '切换账号',
      content: '确定要切换账号吗？将返回登录页面。',
      success: (res) => {
        if (res.confirm) {
          app.clearAuth();
          wx.reLaunch({ url: '/pages/login/login' });
        }
      }
    });
  },

  logout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          api.logout()
            .catch(() => {})
            .then(() => {
              app.clearAuth();
              wx.reLaunch({ url: '/pages/login/login' });
            });
        }
      }
    });
  }
});
