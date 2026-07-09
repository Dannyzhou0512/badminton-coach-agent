const app = getApp();

function request(options) {
  return new Promise((resolve, reject) => {
    const token = app.globalData.token || wx.getStorageSync('token');
    wx.request({
      url: app.globalData.apiBase + options.url,
      method: options.method || 'GET',
      timeout: options.timeout || 30000,
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': 'Bearer ' + token } : {}),
        ...(options.header || {})
      },
      success: (res) => {
        if (res.statusCode === 401) {
          app.clearAuth();
          wx.reLaunch({ url: '/pages/login/login' });
          reject(new Error('登录已过期，请重新登录'));
          return;
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject(new Error((res.data && res.data.detail) || '请求失败'));
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || '网络请求失败'));
      }
    });
  });
}

function parseSSEResponse(text) {
  // Split into SSE event blocks separated by blank lines
  const blocks = text.split('\n\n');
  let result = null;
  let error = null;
  let lastProgress = { percent: 0, message: '处理中...' };

  for (const block of blocks) {
    const lines = block.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    let eventName = '';
    let dataStr = '';

    for (const line of lines) {
      if (line.startsWith('event:')) {
        eventName = line.substring(6).trim();
      } else if (line.startsWith('data:')) {
        dataStr = line.substring(5).trim();
      }
    }

    if (!dataStr || dataStr === '[DONE]') continue;

    try {
      const payload = JSON.parse(dataStr);
      if (eventName === 'result') {
        result = payload;
      } else if (eventName === 'error') {
        error = (payload && payload.message) ? payload.message : '分析失败';
      } else if (eventName === 'progress') {
        lastProgress = payload;
      } else if (eventName === 'start') {
        lastProgress = { percent: 5, message: (payload && payload.message) ? payload.message : '开始分析...' };
      }
    } catch (e) {
      // ignore malformed json
    }
  }

  if (result) return { type: 'result', data: result };
  if (error) return { type: 'error', message: error };
  return { type: 'progress', data: lastProgress };
}

module.exports = {
  request,

  wechatLogin(jsCode, nickname, avatar) {
    return request({
      url: '/api/auth/wechat/miniprogram-login',
      method: 'POST',
      data: {
        js_code: jsCode,
        nickname: nickname || '',
        avatar: avatar || ''
      }
    });
  },

  login(username, password) {
    return request({
      url: '/api/auth/login',
      method: 'POST',
      data: { username, password }
    });
  },

  register(username, password, nickname, email) {
    return request({
      url: '/api/auth/register',
      method: 'POST',
      data: { username, password, nickname: nickname || '', email: email || '' }
    });
  },

  getUserInfo() {
    return request({ url: '/api/auth/me' });
  },

  updateProfile(nickname, avatar) {
    return request({
      url: '/api/auth/profile',
      method: 'PUT',
      data: { nickname: nickname, avatar: avatar || null, language: app.globalData.language }
    });
  },

  uploadAvatar(filePath) {
    return new Promise((resolve, reject) => {
      const token = app.globalData.token || wx.getStorageSync('token');
      wx.uploadFile({
        url: app.globalData.apiBase + '/api/auth/avatar',
        filePath: filePath,
        name: 'avatar',
        header: {
          ...(token ? { 'Authorization': 'Bearer ' + token } : {})
        },
        success: (res) => {
          if (res.statusCode === 401) {
            app.clearAuth();
            wx.reLaunch({ url: '/pages/login/login' });
            reject(new Error('登录已过期'));
            return;
          }
          try {
            const data = JSON.parse(res.data);
            if (res.statusCode >= 200 && res.statusCode < 300) {
              resolve(data);
            } else {
              reject(new Error(data.detail || '上传失败'));
            }
          } catch (e) {
            reject(new Error('响应解析失败'));
          }
        },
        fail: (err) => {
          reject(new Error(err.errMsg || '上传失败'));
        }
      });
    });
  },

  bindWechat(jsCode) {
    return request({
      url: '/api/auth/wechat/bind',
      method: 'POST',
      data: { js_code: jsCode }
    });
  },

  unbindWechat() {
    return request({ url: '/api/auth/wechat/unbind', method: 'POST' });
  },

  confirmBind(token, jsCode) {
    return request({
      url: '/api/auth/wechat/confirm-bind',
      method: 'POST',
      data: { token: token, js_code: jsCode }
    });
  },

  logout() {
    return request({ url: '/api/auth/logout', method: 'POST' });
  },

  analyzeVideo(filePath, config, onProgress) {
    return new Promise((resolve, reject) => {
      const token = app.globalData.token || wx.getStorageSync('token');
      const configStr = JSON.stringify({
        target_player: config.target_player || 'largest',
        analysis_preset: config.analysis_preset || 'adaptive',
        llm_provider: config.llm_provider || 'qwen',
        conf_threshold: config.conf_threshold || 0.3,
        annotated_output_fps: config.analysis_preset === 'match_far' ? 15 : null,
        reuse_annotated_video: true,
        write_shot_clips: false,
        generate_llm_report: false,
        language: app.globalData.language,
        ...(config.extra || {})
      });

      const uploadTask = wx.uploadFile({
        url: app.globalData.apiBase + '/api/analyze',
        filePath: filePath,
        name: 'video',
        formData: {
          config: configStr
        },
        header: {
          ...(token ? { 'Authorization': 'Bearer ' + token } : {})
        },
        success: (res) => {
          if (res.statusCode === 401) {
            app.clearAuth();
            wx.reLaunch({ url: '/pages/login/login' });
            reject(new Error('登录已过期'));
            return;
          }
          try {
            const parsed = parseSSEResponse(res.data);
            if (parsed.type === 'result') {
              resolve(parsed.data);
            } else if (parsed.type === 'error') {
              reject(new Error(parsed.message));
            } else {
              reject(new Error('分析未完成，请重试'));
            }
          } catch (e) {
            try {
              const data = JSON.parse(res.data);
              if (res.statusCode >= 200 && res.statusCode < 300) {
                resolve(data);
              } else {
                reject(new Error(data.detail || '分析失败'));
              }
            } catch (e2) {
              reject(new Error('响应解析失败'));
            }
          }
        },
        fail: (err) => {
          reject(new Error(err.errMsg || '上传失败，请检查网络'));
        }
      });

      if (onProgress) {
        uploadTask.onProgressUpdate((res) => {
          onProgress(Math.min(95, res.progress), '正在上传视频...');
        });
      }
    });
  },

  getHistoryList() {
    return request({ url: '/api/history?language=' + (app.globalData.language || 'zh') });
  },

  getHistoryDetail(id) {
    return request({ url: '/api/history/' + id + '?language=' + (app.globalData.language || 'zh') });
  },

  sendCoachMessage(question, useReport, llmProvider) {
    return request({
      url: '/api/coach/chat',
      method: 'POST',
      data: {
        question: question,
        use_report_context: useReport !== false,
        provider: llmProvider || 'qwen',
        language: app.globalData.language
      }
    });
  }
};
