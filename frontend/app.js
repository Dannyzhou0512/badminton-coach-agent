/* ============================================================
   羽动智练 — Badminton Smart Training System
   Application Logic (Dark Theme)
   ============================================================ */

(function () {
  "use strict";

  // ---- Global i18n Dictionary ----
  const GLOBAL_I18N = {
    zh: {
      pageTitle: "羽动智练 — 羽毛球智能训练系统",
      brandName: "羽动智练",
      creditText: "Powered by 羽动智练",
      navTraining: "训练检测",
      navAnalysis: "动作分析",
      navReport: "训练报告",
      navCoach: "AI教练",
      navHistory: "训练历史",
      navSettings: "系统设置",
      tabRealtime: "实时检测",
      statusDisconnected: "未连接",
      statusConnected: "已连接",
      statusConnecting: "连接中...",
      trainingTitle: "实时训练检测",
      trainingDesc: "上传或录制羽毛球训练视频，AI 将实时检测动作、追踪球轨迹并评估姿势。",
      trainingNotice: "当前页面已接入后端分析流程：上传视频后先进行视频质量预检，再调用 /api/analyze 生成标注视频、动作结果和训练报告。",
      shootingGuideTitle: "拍摄建议",
      guideLandscapeTitle: "横屏拍摄",
      guideLandscapeDesc: "请使用手机横屏拍摄，画面更稳定，人物更完整",
      guideDistanceTitle: "拍摄距离",
      guideDistanceDesc: "距离场地边线3-5米，确保人物全身在画面中",
      guideAngleTitle: "拍摄角度",
      guideAngleDesc: "站在场地侧面拍摄，与球网平行，不要正面或太斜",
      guideLightTitle: "光线充足",
      guideLightDesc: "确保场地光线明亮，避免逆光拍摄",
      guideStableTitle: "画面稳定",
      guideStableDesc: "使用支架固定手机，避免手持晃动",
      guideDurationTitle: "时长建议",
      guideDurationDesc: "建议10秒-3分钟片段，包含完整的击球动作",
      precheckTitle: "视频质量检测",
      precheckChecking: "检测中...",
      precheckPassed: "检测通过",
      precheckWarning: "存在警告",
      precheckFailed: "检测未通过",
      btnProceed: "继续分析",
      btnReupload: "重新上传",
      processingTitle: "视频分析处理中",
      processingStage1: "上传视频并准备姿态分析",
      detectControls: "检测控制",
      detectControlsDesc: "系统已内置推荐分析配置，会根据客户电脑环境自动使用 GPU 或 CPU。",
      btnStart: "开始检测",
      btnStop: "停止",
      btnReset: "重置",
      btnSend: "发送",
      btnRefresh: "刷新",
      btnExport: "导出报告",
      btnSaveSettings: "保存设置",
      btnResetSettings: "恢复默认",
      videoReady: "标注视频已生成，可在页面中播放。",
      downloadVideo: "下载视频",
      dropUpload: "点击上传视频或将视频拖到这里",
      shotTimelineTitle: "逐拍时间轴",
      waitingAnalysis: "等待分析结果",
      timelineEmpty: "分析完成后会在这里显示每一次击球，点击可跳转到视频对应片段。",
      liveMetrics: "实时指标",
      metricProgress: "播放进度",
      metricProgressUnit: "当前 / 总时长",
      metricShots: "已过击球",
      metricShotsUnit: "当前 / 总计",
      metricConf: "当前置信",
      metricConfUnit: "当前片段",
      metricAction: "当前动作",
      metricActionUnit: "随播放更新",
      analysisTitle: "动作分析",
      analysisDesc: "对检测到的羽毛球动作进行分类与质量评估，包括挥拍类型、力量分析和动作评分。",
      actionTypeLabel: "动作类型",
      actionScoreLabel: "动作质量评分",
      powerLevelLabel: "力量等级",
      qualityBreakdown: "动作质量评分",
      qSmooth: "挥拍流畅度",
      qAccuracy: "击球点精准度",
      qCoord: "身体协调性",
      qFoot: "步法移动",
      qWrist: "手腕发力",
      qBalance: "重心稳定性",
      detectionHistory: "检测历史记录",
      thTime: "时间",
      thAction: "动作",
      thConf: "置信度",
      thScore: "评分",
      thPower: "力量",
      noDetectionRecords: "暂无检测记录",
      reportTitle: "训练报告",
      reportDesc: "查看整体训练数据统计、雷达图分析及详细报告。支持导出训练报告。",
      scoreSummary: "训练评分概览",
      totalSessions: "总训练次数",
      avgScore: "平均评分",
      bestAction: "最佳动作",
      totalFrames: "总检测帧数",
      reportDate: "训练日期",
      reportDuration: "训练时长",
      reportActions: "总动作数",
      reportHighlights: "本次亮点",
      reportIssues: "重点问题",
      reportSuggestions: "改进建议",
      reportPlan: "训练计划",
      reportReview: "复核建议",
      coachTitle: "AI教练问答",
      coachDesc: "围绕羽毛球技术、步伐、训练计划、比赛复盘和运动安全进行问答。完成一次视频分析后，可以带着本次训练报告继续追问。",
      coachChatTitle: "训练教练",
      coachModelLabel: "模型",
      coachZhipu: "智谱AI",
      coachPlaceholder: "例如：我后场杀球总是发不上力，应该怎么练？",
      coachConfigTitle: "教练配置",
      coachUseReport: "结合本次训练分析",
      coachContextLabel: "当前上下文",
      coachNoReport: "暂无训练报告",
      coachContextDesc: "完成一次视频分析后，AI 教练会自动读取动作、击球片段、置信度和步伐评分，用于回答追问。",
      historyTitle: "训练历史",
      historyDesc: "查看过往训练记录，追踪动作质量变化趋势，对比进步情况。",
      histSessions: "训练次数",
      histAvgScore: "平均评分",
      histTotalShots: "总击球数",
      histLastDate: "最近训练",
      trendChart: "评分趋势",
      sessionList: "训练记录",
      noHistory: "暂无训练记录，完成一次视频分析后会显示在这里。",
      settingsTitle: "系统设置",
      settingsDesc: "配置界面语言、检测模型参数、视频处理选项和系统偏好。",
      langSettings: "语言设定",
      langSettingsDesc: "选择界面显示语言，设置将自动保存并应用到全站。",
      modelConfig: "模型配置",
      inferenceBackend: "推理后端",
      computeDevice: "设备",
      inputResolution: "输入分辨率",
      modelPrecision: "模型精度",
      fp32: "FP32 (高精度)",
      fp16: "FP16 (均衡)",
      int8: "INT8 (快速)",
      videoConfig: "视频处理",
      frameRate: "帧率",
      frameSkip: "跳帧间隔",
      roiArea: "区域",
      saveDetection: "保存检测结果",
      dontSave: "不保存",
      saveJson: "保存为 JSON",
      actions: "操作",
      precheckPassMsg: "视频质量良好，可以分析",
      precheckPassMatchMsg: "检测到比赛远景视频，可以分析",
      precheckWarnMsg: "视频存在小问题，仍可分析，部分精度可能受影响",
      precheckWarnMatchMsg: "比赛远景视频，将自动适配参数进行分析",
      precheckFailMsg: "视频质量不佳，请检查后重新上传",
      btnLogin: "登录 / 注册",
      login: "登录",
      register: "注册",
      logout: "退出登录",
      switchAccount: "切换账号",
      username: "用户名",
      usernameOrEmail: "用户名/邮箱",
      nickname: "昵称",
      email: "邮箱",
      password: "密码",
      avatarUrl: "头像URL",
      editProfile: "编辑资料",
      save: "保存",
      cancel: "取消",
      accountSettings: "账号设置",
      notLoggedIn: "您还未登录",
      loginHint: "登录后可同步训练记录，微信小程序互联",
      wechatBound: "已绑定微信",
      wechatNotBound: "未绑定微信",
      bindWechat: "绑定微信",
      bindWechatTitle: "绑定微信小程序",
      bindWechatDesc: "打开微信小程序，在「我的」页面点击「绑定网页账号」，输入下方绑定码",
      copyBindCode: "复制绑定码",
      bindWaiting: "等待绑定...",
      bindSuccess: "绑定成功",
      bindExpired: "绑定码已过期，请重新获取",
      bindFailed: "绑定失败，请重试",
      wechatLogin: "微信登录",
      wechatRegister: "微信注册",
      orLoginWith: "或使用以下方式登录",
      orRegisterWith: "或使用以下方式注册",
      wechatHint: "微信登录功能需要在小程序内使用",
      loginSuccess: "登录成功",
      registerSuccess: "注册成功",
      logoutSuccess: "已退出登录",
      profileUpdateSuccess: "资料更新成功",
      loginFailed: "登录失败",
      registerFailed: "注册失败",
      videoSizeExceeded: "视频大小超过 500MB 限制，请压缩或剪辑后重新上传",
      tourWelcomeTitle: "欢迎使用羽动智练",
      tourWelcomeDesc: "跟着引导快速了解如何使用系统。",
      tourStep1Title: "第一步：上传视频",
      tourStep1Desc: "点击这里上传羽毛球训练或比赛视频，支持拖拽上传。",
      tourStep2Title: "第二步：开始检测",
      tourStep2Desc: "上传完成后，点击开始检测，AI 将分析动作和步伐。",
      tourStep3Title: "第三步：查看击球时间轴",
      tourStep3Desc: "分析完成后，这里会显示每一次击球的详细信息。",
      tourStep4Title: "第四步：查看训练报告",
      tourStep4Desc: "切换到训练报告页，查看整体数据、雷达图和 AI 教练建议。",
      tourStep5Title: "第五步：查看历史记录",
      tourStep5Desc: "所有分析记录都会保存在训练历史中，方便随时回看。",
      tourNext: "下一步",
      tourSkip: "跳过",
      tourFinish: "完成",
    },
    en: {
      pageTitle: "BadmintonAI — Smart Training System",
      brandName: "BadmintonAI",
      creditText: "Powered by BadmintonAI",
      navTraining: "Detection",
      navAnalysis: "Analysis",
      navReport: "Report",
      navCoach: "AI Coach",
      navHistory: "History",
      navSettings: "Settings",
      tabRealtime: "Real-time",
      statusDisconnected: "Disconnected",
      statusConnected: "Connected",
      statusConnecting: "Connecting...",
      trainingTitle: "Real-time Training Detection",
      trainingDesc: "Upload or record badminton training videos. AI detects actions, tracks shuttle trajectory and evaluates posture in real-time.",
      trainingNotice: "The page connects to the backend analysis pipeline: upload triggers video quality pre-check, then /api/analyze generates annotated video, action results and training report.",
      shootingGuideTitle: "Filming Guide",
      guideLandscapeTitle: "Landscape Mode",
      guideLandscapeDesc: "Use landscape orientation for more stable footage and full player visibility",
      guideDistanceTitle: "Distance",
      guideDistanceDesc: "Stand 3-5m from the court sideline to ensure the full body is in frame",
      guideAngleTitle: "Angle",
      guideAngleDesc: "Film from the side, parallel to the net. Avoid frontal or steep angles",
      guideLightTitle: "Lighting",
      guideLightDesc: "Ensure bright court lighting, avoid backlit filming",
      guideStableTitle: "Stable Footage",
      guideStableDesc: "Use a tripod or phone stand to avoid handshake blur",
      guideDurationTitle: "Duration",
      guideDurationDesc: "10 seconds to 3 minutes clips with complete stroke actions recommended",
      precheckTitle: "Video Quality Check",
      precheckChecking: "Checking...",
      precheckPassed: "Passed",
      precheckWarning: "Warnings found",
      precheckFailed: "Check failed",
      btnProceed: "Continue Analysis",
      btnReupload: "Re-upload",
      processingTitle: "Processing Video",
      processingStage1: "Preparing pose analysis...",
      detectControls: "Detection Controls",
      detectControlsDesc: "Recommended configs are pre-loaded. GPU/CPU is auto-selected based on your hardware.",
      btnStart: "Start",
      btnStop: "Stop",
      btnReset: "Reset",
      btnSend: "Send",
      btnRefresh: "Refresh",
      btnExport: "Export Report",
      btnSaveSettings: "Save Settings",
      btnResetSettings: "Reset to Defaults",
      videoReady: "Annotated video is ready for playback.",
      downloadVideo: "Download Video",
      dropUpload: "Click or drag a video here to upload",
      shotTimelineTitle: "Shot Timeline",
      waitingAnalysis: "Waiting for analysis results",
      timelineEmpty: "Each shot will appear here after analysis. Click to jump to the video segment.",
      liveMetrics: "Live Metrics",
      metricProgress: "Progress",
      metricProgressUnit: "Current / Total",
      metricShots: "Shots Played",
      metricShotsUnit: "Current / Total",
      metricConf: "Confidence",
      metricConfUnit: "Current segment",
      metricAction: "Current Action",
      metricActionUnit: "Updates with playback",
      analysisTitle: "Action Analysis",
      analysisDesc: "Classify and evaluate detected badminton actions including stroke type, power analysis and quality scores.",
      actionTypeLabel: "Action Type",
      actionScoreLabel: "Quality Score",
      powerLevelLabel: "Power Level",
      qualityBreakdown: "Action Quality Breakdown",
      qSmooth: "Swing Smoothness",
      qAccuracy: "Contact Point Accuracy",
      qCoord: "Body Coordination",
      qFoot: "Footwork",
      qWrist: "Wrist Power",
      qBalance: "Balance & Stability",
      detectionHistory: "Detection History",
      thTime: "Time",
      thAction: "Action",
      thConf: "Confidence",
      thScore: "Score",
      thPower: "Power",
      noDetectionRecords: "No detection records yet",
      reportTitle: "Training Report",
      reportDesc: "View overall training statistics, radar chart analysis and detailed report. Export supported.",
      scoreSummary: "Score Overview",
      totalSessions: "Total Sessions",
      avgScore: "Avg Score",
      bestAction: "Best Action",
      totalFrames: "Frames Analyzed",
      reportDate: "Date",
      reportDuration: "Duration",
      reportActions: "Total Actions",
      reportHighlights: "Highlights",
      reportIssues: "Key Issues",
      reportSuggestions: "Suggestions",
      reportPlan: "Training Plan",
      reportReview: "Review Notes",
      coachTitle: "AI Coach",
      coachDesc: "Ask about technique, footwork, training plans, match review and injury prevention. After video analysis, the coach uses your report for context.",
      coachChatTitle: "Training Coach",
      coachModelLabel: "Model",
      coachZhipu: "Zhipu AI",
      coachPlaceholder: "e.g., How can I improve my backcourt smash power?",
      coachConfigTitle: "Coach Settings",
      coachUseReport: "Use training report context",
      coachContextLabel: "Current Context",
      coachNoReport: "No report loaded",
      coachContextDesc: "After video analysis, the AI coach reads actions, shots, confidence and footwork scores to answer questions.",
      historyTitle: "Training History",
      historyDesc: "View past training records, track quality trends and compare progress.",
      histSessions: "Sessions",
      histAvgScore: "Avg Score",
      histTotalShots: "Total Shots",
      histLastDate: "Last Session",
      trendChart: "Score Trend",
      sessionList: "Session Records",
      noHistory: "No training records yet. Complete a video analysis to see history here.",
      settingsTitle: "System Settings",
      settingsDesc: "Configure interface language, model parameters, video processing and preferences.",
      langSettings: "Language",
      langSettingsDesc: "Choose display language. Settings are saved automatically and applied site-wide.",
      modelConfig: "Model Config",
      inferenceBackend: "Inference Backend",
      computeDevice: "Device",
      inputResolution: "Input Resolution",
      modelPrecision: "Precision",
      fp32: "FP32 (High Precision)",
      fp16: "FP16 (Balanced)",
      int8: "INT8 (Fast)",
      videoConfig: "Video Processing",
      frameRate: "Frame Rate",
      frameSkip: "Frame Skip",
      roiArea: "ROI",
      saveDetection: "Save Results",
      dontSave: "Don't Save",
      saveJson: "Save as JSON",
      actions: "Actions",
      precheckPassMsg: "Video quality looks good, ready for analysis",
      precheckPassMatchMsg: "Wide-angle match video detected, ready for analysis",
      precheckWarnMsg: "Minor issues detected, analysis may proceed with reduced accuracy",
      precheckWarnMatchMsg: "Wide-angle match video, will auto-adapt parameters",
      precheckFailMsg: "Video quality is poor, please check and re-upload",
      btnLogin: "Login / Register",
      login: "Login",
      register: "Register",
      logout: "Logout",
      switchAccount: "Switch Account",
      username: "Username",
      usernameOrEmail: "Username or Email",
      nickname: "Nickname",
      email: "Email",
      password: "Password",
      avatarUrl: "Avatar URL",
      editProfile: "Edit Profile",
      save: "Save",
      cancel: "Cancel",
      accountSettings: "Account Settings",
      notLoggedIn: "You are not logged in",
      loginHint: "Login to sync training records and connect with WeChat Mini Program",
      wechatBound: "WeChat bound",
      wechatNotBound: "WeChat not bound",
      bindWechat: "Bind WeChat",
      bindWechatTitle: "Bind WeChat Mini Program",
      bindWechatDesc: "Open the WeChat Mini Program, tap 'Bind Web Account' in 'My' page, and enter the code below",
      copyBindCode: "Copy Code",
      bindWaiting: "Waiting for binding...",
      bindSuccess: "Binding successful",
      bindExpired: "Code expired, please get a new one",
      bindFailed: "Binding failed, please try again",
      wechatLogin: "WeChat Login",
      wechatRegister: "Register with WeChat",
      orLoginWith: "Or login with",
      orRegisterWith: "Or register with",
      wechatHint: "WeChat login is only available within the Mini Program",
      loginSuccess: "Login successful",
      registerSuccess: "Registration successful",
      logoutSuccess: "Logged out",
      profileUpdateSuccess: "Profile updated",
      loginFailed: "Login failed",
      registerFailed: "Registration failed",
      videoSizeExceeded: "Video exceeds 500MB limit. Please compress or trim before uploading.",
      tourWelcomeTitle: "Welcome to Badminton Smart Coach",
      tourWelcomeDesc: "Follow this quick guide to get started.",
      tourStep1Title: "Step 1: Upload Video",
      tourStep1Desc: "Click here to upload your badminton training or match video. Drag and drop is also supported.",
      tourStep2Title: "Step 2: Start Analysis",
      tourStep2Desc: "After uploading, click Start Analysis and the AI will evaluate your strokes and footwork.",
      tourStep3Title: "Step 3: Shot Timeline",
      tourStep3Desc: "Once analysis is complete, every shot will be shown here with details.",
      tourStep4Title: "Step 4: Training Report",
      tourStep4Desc: "Switch to the Training Report tab to see overall stats, radar chart and AI coach advice.",
      tourStep5Title: "Step 5: History",
      tourStep5Desc: "All analyses are saved in Training History for future review.",
      tourNext: "Next",
      tourSkip: "Skip",
      tourFinish: "Finish",
    },
    ja: {
      pageTitle: "BadmintonAI — バドミントン智能トレーニング",
      brandName: "BadmintonAI",
      creditText: "Powered by BadmintonAI",
      navTraining: "検出",
      navAnalysis: "分析",
      navReport: "レポート",
      navCoach: "AIコーチ",
      navHistory: "履歴",
      navSettings: "設定",
      tabRealtime: "リアルタイム",
      statusDisconnected: "未接続",
      statusConnected: "接続済み",
      statusConnecting: "接続中...",
      trainingTitle: "リアルタイムトレーニング検出",
      trainingDesc: "バドミントン練習動画をアップロードまたは録画。AIが動作を検出し、シャトル軌道を追跡し、姿勢を評価します。",
      trainingNotice: "バックエンド分析パイプラインに接続：アップロード後に動画画質チェックを行い、/api/analyze で注釈付き動画・結果・レポートを生成します。",
      shootingGuideTitle: "撮影ガイド",
      guideLandscapeTitle: "横画面撮影",
      guideLandscapeDesc: "横画面で撮影すると、映像が安定し全身が映ります",
      guideDistanceTitle: "撮影距離",
      guideDistanceDesc: "コートのサイドラインから3-5m離れて、全身がフレームに入るように",
      guideAngleTitle: "撮影角度",
      guideAngleDesc: "ネットと平行に横から撮影。正面や斜めすぎる角度は避けて",
      guideLightTitle: "照明",
      guideLightDesc: "コートを明るく保ち、逆光での撮影を避けて",
      guideStableTitle: "安定撮影",
      guideStableDesc: "三脚やスタンドを使って手ブレを防止",
      guideDurationTitle: "動画の長さ",
      guideDurationDesc: "ストロークが含まれる10秒〜3分程度のクリップ推奨",
      precheckTitle: "動画画質チェック",
      precheckChecking: "チェック中...",
      precheckPassed: "合格",
      precheckWarning: "警告あり",
      precheckFailed: "チェック不合格",
      btnProceed: "分析を続ける",
      btnReupload: "再アップロード",
      processingTitle: "動画を処理中",
      processingStage1: "姿勢分析を準備中...",
      detectControls: "検出設定",
      detectControlsDesc: "推奨設定をプリセット済み。ハードウェアに応じてGPU/CPUを自動選択します。",
      btnStart: "開始",
      btnStop: "停止",
      btnReset: "リセット",
      btnSend: "送信",
      btnRefresh: "更新",
      btnExport: "レポート出力",
      btnSaveSettings: "設定を保存",
      btnResetSettings: "初期設定に戻す",
      videoReady: "注釈付き動画の再生準備ができました。",
      downloadVideo: "動画をダウンロード",
      dropUpload: "クリックまたはドラッグで動画をアップロード",
      shotTimelineTitle: "ショットタイムライン",
      waitingAnalysis: "分析結果を待っています",
      timelineEmpty: "分析後、各ショットがここに表示されます。クリックで該当動画にジャンプ。",
      liveMetrics: "ライブ指標",
      metricProgress: "再生位置",
      metricProgressUnit: "現在 / 合計",
      metricShots: "ショット数",
      metricShotsUnit: "現在 / 合計",
      metricConf: "信頼度",
      metricConfUnit: "現在のセグメント",
      metricAction: "現在の動作",
      metricActionUnit: "再生に合わせて更新",
      analysisTitle: "動作分析",
      analysisDesc: "検出されたバドミントン動作を分類・評価。ストローク種別、パワー分析、品質スコアを含みます。",
      actionTypeLabel: "動作タイプ",
      actionScoreLabel: "品質スコア",
      powerLevelLabel: "パワーレベル",
      qualityBreakdown: "動作品質の内訳",
      qSmooth: "スイングの滑らかさ",
      qAccuracy: "打点の精度",
      qCoord: "身体の協調性",
      qFoot: "フットワーク",
      qWrist: "手首のパワー",
      qBalance: "重心安定性",
      detectionHistory: "検出履歴",
      thTime: "時間",
      thAction: "動作",
      thConf: "信頼度",
      thScore: "スコア",
      thPower: "パワー",
      noDetectionRecords: "検出記録がありません",
      reportTitle: "トレーニングレポート",
      reportDesc: "トレーニング統計、レーダーチャート分析、詳細レポートを表示。エクスポート対応。",
      scoreSummary: "スコア概要",
      totalSessions: "総セッション数",
      avgScore: "平均スコア",
      bestAction: "ベスト動作",
      totalFrames: "解析フレーム数",
      reportDate: "日付",
      reportDuration: "時間",
      reportActions: "総動作数",
      reportHighlights: "ハイライト",
      reportIssues: "主な課題",
      reportSuggestions: "改善提案",
      reportPlan: "トレーニング計画",
      reportReview: "レビュー所見",
      coachTitle: "AIコーチ",
      coachDesc: "技術、フットワーク、練習計画、試合の复盘、怪我予防について質問できます。動画分析後はレポートを文脈として使用します。",
      coachChatTitle: "トレーニングコーチ",
      coachModelLabel: "モデル",
      coachZhipu: "智譜AI",
      coachPlaceholder: "例：バックコートのスマッシュ力を上げるには？",
      coachConfigTitle: "コーチ設定",
      coachUseReport: "トレーニングレポートを使用",
      coachContextLabel: "現在のコンテキスト",
      coachNoReport: "レポート未読み込み",
      coachContextDesc: "動画分析後、AIコーチは動作・ショット・信頼度・フットワークスコアを読み取って回答します。",
      historyTitle: "トレーニング履歴",
      historyDesc: "過去のトレーニング記録を表示し、品質の変化トレンドを追跡します。",
      histSessions: "セッション数",
      histAvgScore: "平均スコア",
      histTotalShots: "総ショット数",
      histLastDate: "最終セッション",
      trendChart: "スコア推移",
      sessionList: "セッション記録",
      noHistory: "トレーニング記録がありません。動画分析を完了すると表示されます。",
      settingsTitle: "システム設定",
      settingsDesc: "表示言語、モデルパラメータ、動画処理、環境設定を構成します。",
      langSettings: "言語設定",
      langSettingsDesc: "表示言語を選択。設定は自動保存され、全体に適用されます。",
      modelConfig: "モデル設定",
      inferenceBackend: "推論バックエンド",
      computeDevice: "デバイス",
      inputResolution: "入力解像度",
      modelPrecision: "精度",
      fp32: "FP32（高精度）",
      fp16: "FP16（バランス）",
      int8: "INT8（高速）",
      videoConfig: "動画処理",
      frameRate: "フレームレート",
      frameSkip: "フレームスキップ",
      roiArea: "ROI領域",
      saveDetection: "結果を保存",
      dontSave: "保存しない",
      saveJson: "JSONで保存",
      actions: "操作",
      precheckPassMsg: "動画画質良好、分析可能です",
      precheckPassMatchMsg: "試合の広角動画を検出、分析可能です",
      precheckWarnMsg: "小さな問題がありますが、分析は可能です（精度に影響する可能性あり）",
      precheckWarnMatchMsg: "広角試合動画、パラメータを自動調整します",
      precheckFailMsg: "動画画質が良くありません。確認して再アップロードしてください",
      btnLogin: "ログイン / 新規登録",
      login: "ログイン",
      register: "新規登録",
      logout: "ログアウト",
      switchAccount: "アカウント切替",
      username: "ユーザー名",
      usernameOrEmail: "ユーザー名/メール",
      nickname: "ニックネーム",
      email: "メールアドレス",
      password: "パスワード",
      avatarUrl: "アバターURL",
      editProfile: "プロフィール編集",
      save: "保存",
      cancel: "キャンセル",
      accountSettings: "アカウント設定",
      notLoggedIn: "ログインしていません",
      loginHint: "ログインするとトレーニング記録を同期し、WeChatミニプログラムと連携できます",
      wechatBound: "WeChat連携済み",
      wechatNotBound: "WeChat未連携",
      bindWechat: "WeChatを連携",
      bindWechatTitle: "WeChatミニプログラムを連携",
      bindWechatDesc: "WeChatミニプログラムを開き、「マイ」ページの「Webアカウントを連携」から以下のコードを入力してください",
      copyBindCode: "コードをコピー",
      bindWaiting: "連携待ち...",
      bindSuccess: "連携しました",
      bindExpired: "コードの有効期限が切れました。再度取得してください",
      bindFailed: "連携に失敗しました。もう一度お試しください",
      wechatLogin: "WeChatログイン",
      wechatRegister: "WeChatで新規登録",
      orLoginWith: "または次の方法でログイン",
      orRegisterWith: "または次の方法で登録",
      wechatHint: "WeChatログインはミニプログラム内でのみ利用可能です",
      loginSuccess: "ログインしました",
      registerSuccess: "登録が完了しました",
      logoutSuccess: "ログアウトしました",
      profileUpdateSuccess: "プロフィールを更新しました",
      loginFailed: "ログインに失敗しました",
      registerFailed: "登録に失敗しました",
      videoSizeExceeded: "動画が500MBを超えています。圧縮またはトリミングしてからアップロードしてください。",
      tourWelcomeTitle: "羽動智練へようこそ",
      tourWelcomeDesc: "このガイドに従って、基本的な使い方を確認しましょう。",
      tourStep1Title: "ステップ1：動画をアップロード",
      tourStep1Desc: "ここをタップして練習や試合の動画をアップロードします。ドラッグ＆ドロップも可能です。",
      tourStep2Title: "ステップ2：分析を開始",
      tourStep2Desc: "アップロード後、「分析開始」を押すと、AIが動作とフットワークを分析します。",
      tourStep3Title: "ステップ3：ショットタイムライン",
      tourStep3Desc: "分析完了後、各ショットの詳細がここに表示されます。",
      tourStep4Title: "ステップ4：トレーニングレポート",
      tourStep4Desc: "「トレーニングレポート」タブで総合データ、レーダーチャート、AIコーチのアドバイスを確認します。",
      tourStep5Title: "ステップ5：履歴",
      tourStep5Desc: "すべての分析結果は「トレーニング履歴」に保存され、後から確認できます。",
      tourNext: "次へ",
      tourSkip: "スキップ",
      tourFinish: "完了",
    },
    ko: {
      pageTitle: "BadmintonAI — 배드민턴 스마트 트레이닝",
      brandName: "BadmintonAI",
      creditText: "Powered by BadmintonAI",
      navTraining: "검출",
      navAnalysis: "분석",
      navReport: "리포트",
      navCoach: "AI 코치",
      navHistory: "기록",
      navSettings: "설정",
      tabRealtime: "실시간",
      statusDisconnected: "연결 안됨",
      statusConnected: "연결됨",
      statusConnecting: "연결 중...",
      trainingTitle: "실시간 훈련 감지",
      trainingDesc: "배드민턴 훈련 영상을 업로드하거나 녹화하세요. AI가 동작을 감지하고 셔틀 궤적을 추적하며 자세를 평가합니다.",
      trainingNotice: "백엔드 분석 파이프라인에 연결됨: 업로드 시 화질 검사 후 /api/analyze에서 주석 영상, 결과, 리포트를 생성합니다.",
      shootingGuideTitle: "촬영 가이드",
      guideLandscapeTitle: "가로 촬영",
      guideLandscapeDesc: "가로 모드로 촬영하면 안정적인 화면과 전신이 담깁니다",
      guideDistanceTitle: "촬영 거리",
      guideDistanceDesc: "코트 사이드라인에서 3-5m 떨어져 전신이 프레임에 들어오게 하세요",
      guideAngleTitle: "촬영 각도",
      guideAngleDesc: "네트와 평행하게 측면에서 촬영. 정면이나 너무 기울인 각도 피하기",
      guideLightTitle: "조명",
      guideLightDesc: "코트 조명을 밝게 하고 역광 촬영 피하기",
      guideStableTitle: "안정적인 촬영",
      guideStableDesc: "삼각대나 거치대를 사용해 흔들림 방지",
      guideDurationTitle: "영상 길이",
      guideDurationDesc: "완전한 타격 동작이 포함된 10초~3분 클립 권장",
      precheckTitle: "영상 화질 검사",
      precheckChecking: "검사 중...",
      precheckPassed: "통과",
      precheckWarning: "경고 있음",
      precheckFailed: "검사 실패",
      btnProceed: "분석 계속",
      btnReupload: "재업로드",
      processingTitle: "영상 처리 중",
      processingStage1: "자세 분석 준비 중...",
      detectControls: "감지 컨트롤",
      detectControlsDesc: "추천 설정이 미리 로드됨. 하드웨어에 따라 GPU/CPU 자동 선택.",
      btnStart: "시작",
      btnStop: "정지",
      btnReset: "리셋",
      btnSend: "전송",
      btnRefresh: "새로고침",
      btnExport: "리포트 내보내기",
      btnSaveSettings: "설정 저장",
      btnResetSettings: "기본값으로 복원",
      videoReady: "주석 영상이 재생 준비되었습니다.",
      downloadVideo: "영상 다운로드",
      dropUpload: "클릭하거나 영상을 여기로 드래그",
      shotTimelineTitle: "샷 타임라인",
      waitingAnalysis: "분석 결과 대기 중",
      timelineEmpty: "분석 후 각 샷이 여기에 표시됩니다. 클릭 시 해당 구간으로 이동.",
      liveMetrics: "실시간 지표",
      metricProgress: "재생 진행",
      metricProgressUnit: "현재 / 전체",
      metricShots: "샷 수",
      metricShotsUnit: "현재 / 전체",
      metricConf: "신뢰도",
      metricConfUnit: "현재 구간",
      metricAction: "현재 동작",
      metricActionUnit: "재생에 따라 갱신",
      analysisTitle: "동작 분석",
      analysisDesc: "감지된 배드민턴 동작을 분류하고 평가합니다. 스트로크 유형, 파워 분석, 품질 점수 포함.",
      actionTypeLabel: "동작 유형",
      actionScoreLabel: "품질 점수",
      powerLevelLabel: "파워 레벨",
      qualityBreakdown: "동작 품질 분석",
      qSmooth: "스윙 부드러움",
      qAccuracy: "타점 정확도",
      qCoord: "신체 협응",
      qFoot: "풋워크",
      qWrist: "손목 파워",
      qBalance: "균형 안정성",
      detectionHistory: "감지 기록",
      thTime: "시간",
      thAction: "동작",
      thConf: "신뢰도",
      thScore: "점수",
      thPower: "파워",
      noDetectionRecords: "감지 기록 없음",
      reportTitle: "훈련 리포트",
      reportDesc: "전체 훈련 통계, 레이더 차트 분석, 상세 리포트를 확인하세요. 내보내기 지원.",
      scoreSummary: "점수 개요",
      totalSessions: "총 세션",
      avgScore: "평균 점수",
      bestAction: "베스트 동작",
      totalFrames: "분석 프레임",
      reportDate: "날짜",
      reportDuration: "시간",
      reportActions: "총 동작 수",
      reportHighlights: "하이라이트",
      reportIssues: "주요 문제",
      reportSuggestions: "개선 제안",
      reportPlan: "훈련 계획",
      reportReview: "리뷰 노트",
      coachTitle: "AI 코치",
      coachDesc: "기술, 풋워크, 훈련 계획, 경기 복기, 부상 예방에 대해 질문하세요. 영상 분석 후 리포트를 맥락으로 사용합니다.",
      coachChatTitle: "트레이닝 코치",
      coachModelLabel: "모델",
      coachZhipu: "즈푸 AI",
      coachPlaceholder: "예: 백코트 스매시 파워를 높이려면 어떻게 해야 하나요?",
      coachConfigTitle: "코치 설정",
      coachUseReport: "훈련 리포트 사용",
      coachContextLabel: "현재 컨텍스트",
      coachNoReport: "리포트 없음",
      coachContextDesc: "영상 분석 후 AI 코치가 동작, 샷, 신뢰도, 풋워크 점수를 읽어 답변합니다.",
      historyTitle: "훈련 기록",
      historyDesc: "과거 훈련 기록을 보고 품질 변화 추이를 추적하세요.",
      histSessions: "세션 수",
      histAvgScore: "평균 점수",
      histTotalShots: "총 샷 수",
      histLastDate: "마지막 세션",
      trendChart: "점수 추이",
      sessionList: "세션 기록",
      noHistory: "훈련 기록 없음. 영상 분석 완료 후 표시됩니다.",
      settingsTitle: "시스템 설정",
      settingsDesc: "인터페이스 언어, 모델 파라미터, 영상 처리 및 환경설정을 구성합니다.",
      langSettings: "언어 설정",
      langSettingsDesc: "표시 언어를 선택하세요. 설정은 자동 저장되고 전체에 적용됩니다.",
      modelConfig: "모델 설정",
      inferenceBackend: "추론 백엔드",
      computeDevice: "디바이스",
      inputResolution: "입력 해상도",
      modelPrecision: "정밀도",
      fp32: "FP32 (고정밀)",
      fp16: "FP16 (균형)",
      int8: "INT8 (고속)",
      videoConfig: "영상 처리",
      frameRate: "프레임 레이트",
      frameSkip: "프레임 스킵",
      roiArea: "ROI 영역",
      saveDetection: "결과 저장",
      dontSave: "저장 안 함",
      saveJson: "JSON으로 저장",
      actions: "작업",
      precheckPassMsg: "영상 화질 양호, 분석 가능합니다",
      precheckPassMatchMsg: "광각 경기 영상 감지, 분석 가능합니다",
      precheckWarnMsg: "사소한 문제가 있지만 분석은 가능합니다 (정확도에 영향 있을 수 있음)",
      precheckWarnMatchMsg: "광각 경기 영상, 파라미터를 자동 조정합니다",
      precheckFailMsg: "영상 화질이 좋지 않습니다. 확인 후 재업로드해 주세요",
      btnLogin: "로그인 / 회원가입",
      login: "로그인",
      register: "회원가입",
      logout: "로그아웃",
      switchAccount: "계정 전환",
      username: "사용자명",
      usernameOrEmail: "사용자명/이메일",
      nickname: "닉네임",
      email: "이메일",
      password: "비밀번호",
      avatarUrl: "아바타 URL",
      editProfile: "프로필 편집",
      save: "저장",
      cancel: "취소",
      accountSettings: "계정 설정",
      notLoggedIn: "로그인하지 않았습니다",
      loginHint: "로그인하면 훈련 기록을 동기화하고 위챗 미니프로그램과 연동할 수 있습니다",
      wechatBound: "위챗 연동됨",
      wechatNotBound: "위챗 미연동",
      bindWechat: "위챗 연동",
      bindWechatTitle: "위챗 미니프로그램 연동",
      bindWechatDesc: "위챗 미니프로그램을 열고 '내' 페이지의 '웹 계정 연동'을 탭한 후 아래 코드를 입력하세요",
      copyBindCode: "코드 복사",
      bindWaiting: "연동 대기 중...",
      bindSuccess: "연동 성공",
      bindExpired: "코드가 만료되었습니다. 다시 받아주세요",
      bindFailed: "연동 실패. 다시 시도해주세요",
      wechatLogin: "위챗 로그인",
      wechatRegister: "위챗으로 회원가입",
      orLoginWith: "또는 다음으로 로그인",
      orRegisterWith: "또는 다음으로 가입",
      wechatHint: "위챗 로그인은 미니프로그램 내에서만 사용 가능합니다",
      loginSuccess: "로그인 성공",
      registerSuccess: "회원가입 성공",
      logoutSuccess: "로그아웃되었습니다",
      profileUpdateSuccess: "프로필이 업데이트되었습니다",
      loginFailed: "로그인 실패",
      registerFailed: "회원가입 실패",
      videoSizeExceeded: "영상 크기가 500MB를 초과합니다. 압축하거나 편집 후 업로드하세요.",
      tourWelcomeTitle: "羽動智練에 오신 것을 환영합니다",
      tourWelcomeDesc: "이 가이드를 따라 기본 사용법을 알아보세요.",
      tourStep1Title: "1단계: 영상 업로드",
      tourStep1Desc: "여기를 클릭하여 배드민턴 연습 또는 경기 영상을 업로드하세요. 드래그 앤 드롭도 지원됩니다.",
      tourStep2Title: "2단계: 분석 시작",
      tourStep2Desc: "업로드 후 분석 시작을 누른 AI가 동작과 풋워크를 분석합니다.",
      tourStep3Title: "3단계: 샷 타임라인",
      tourStep3Desc: "분석 완료 후 각 샷의 상세 정보가 여기에 표시됩니다.",
      tourStep4Title: "4단계: 훈련 리포트",
      tourStep4Desc: "훈련 리포트 탭에서 종합 데이터, 레이더 차트, AI 코치 조언을 확인하세요.",
      tourStep5Title: "5단계: 히스토리",
      tourStep5Desc: "모든 분석 기록은 훈련 히스토리에 저장되어 언제든 다시 볼 수 있습니다.",
      tourNext: "다음",
      tourSkip: "건너뛰기",
      tourFinish: "완료",
    },
    id: {
      pageTitle: "BadmintonAI — Sistem Latihan Cerdas Bulu Tangkis",
      brandName: "BadmintonAI",
      creditText: "Powered by BadmintonAI",
      navTraining: "Deteksi",
      navAnalysis: "Analisis",
      navReport: "Laporan",
      navCoach: "Pelatih AI",
      navHistory: "Riwayat",
      navSettings: "Pengaturan",
      tabRealtime: "Real-time",
      statusDisconnected: "Terputus",
      statusConnected: "Terhubung",
      statusConnecting: "Menghubungkan...",
      trainingTitle: "Deteksi Latihan Real-time",
      trainingDesc: "Unggah atau rekam video latihan bulu tangkis. AI mendeteksi gerakan, melacak lintasan kok, dan mengevaluasi postur secara real-time.",
      trainingNotice: "Terhubung ke pipeline analisis backend: unggah memicu pemeriksaan kualitas video, lalu /api/analyze menghasilkan video beranotasi, hasil, dan laporan.",
      shootingGuideTitle: "Panduan Pengambilan Video",
      guideLandscapeTitle: "Mode Lanskap",
      guideLandscapeDesc: "Gunakan orientasi lanskap untuk footage lebih stabil dan pemain terlihat penuh",
      guideDistanceTitle: "Jarak",
      guideDistanceDesc: "Berdiri 3-5m dari garis samping lapangan agar seluruh tubuh terlihat",
      guideAngleTitle: "Sudut",
      guideAngleDesc: "Rekam dari samping, sejajar dengan net. Hindari sudut depan atau terlalu miring",
      guideLightTitle: "Pencahayaan",
      guideLightDesc: "Pastikan pencahayaan lapangan terang, hindari rekaman backlight",
      guideStableTitle: "Rekaman Stabil",
      guideStableDesc: "Gunakan tripod atau penyangga untuk menghindari goyangan",
      guideDurationTitle: "Durasi",
      guideDurationDesc: "Klip 10 detik - 3 menit dengan pukulan lengkap direkomendasikan",
      precheckTitle: "Pemeriksaan Kualitas Video",
      precheckChecking: "Memeriksa...",
      precheckPassed: "Lulus",
      precheckWarning: "Ada peringatan",
      precheckFailed: "Gagal",
      btnProceed: "Lanjut Analisis",
      btnReupload: "Unggah Ulang",
      processingTitle: "Memproses Video",
      processingStage1: "Menyiapkan analisis pose...",
      detectControls: "Kontrol Deteksi",
      detectControlsDesc: "Konfigurasi rekomendasi sudah dimuat. GPU/CPU dipilih otomatis berdasarkan perangkat keras.",
      btnStart: "Mulai",
      btnStop: "Berhenti",
      btnReset: "Reset",
      btnSend: "Kirim",
      btnRefresh: "Refresh",
      btnExport: "Ekspor Laporan",
      btnSaveSettings: "Simpan Pengaturan",
      btnResetSettings: "Reset ke Default",
      videoReady: "Video beranotasi siap diputar.",
      downloadVideo: "Unduh Video",
      dropUpload: "Klik atau seret video ke sini untuk mengunggah",
      shotTimelineTitle: "Timeline Pukulan",
      waitingAnalysis: "Menunggu hasil analisis",
      timelineEmpty: "Setiap pukulan akan muncul di sini setelah analisis. Klik untuk lompat ke segmen video.",
      liveMetrics: "Metrik Live",
      metricProgress: "Progress",
      metricProgressUnit: "Sekarang / Total",
      metricShots: "Pukulan",
      metricShotsUnit: "Sekarang / Total",
      metricConf: "Kepercayaan",
      metricConfUnit: "Segmen sekarang",
      metricAction: "Gerakan Sekarang",
      metricActionUnit: "Update saat putar",
      analysisTitle: "Analisis Gerakan",
      analysisDesc: "Mengklasifikasikan dan mengevaluasi gerakan bulu tangkis yang terdeteksi, termasuk jenis pukulan, analisis tenaga, dan skor kualitas.",
      actionTypeLabel: "Jenis Gerakan",
      actionScoreLabel: "Skor Kualitas",
      powerLevelLabel: "Tingkat Tenaga",
      qualityBreakdown: "Rincian Kualitas Gerakan",
      qSmooth: "Kelancaran Ayunan",
      qAccuracy: "Akurasi Titik Pukul",
      qCoord: "Koordinasi Tubuh",
      qFoot: "Footwork",
      qWrist: "Tenaga Pergelangan",
      qBalance: "Keseimbangan",
      detectionHistory: "Riwayat Deteksi",
      thTime: "Waktu",
      thAction: "Gerakan",
      thConf: "Kepercayaan",
      thScore: "Skor",
      thPower: "Tenaga",
      noDetectionRecords: "Belum ada riwayat deteksi",
      reportTitle: "Laporan Latihan",
      reportDesc: "Lihat statistik latihan keseluruhan, analisis radar chart, dan laporan detail. Ekspor didukung.",
      scoreSummary: "Ringkasan Skor",
      totalSessions: "Total Sesi",
      avgScore: "Skor Rata-rata",
      bestAction: "Gerakan Terbaik",
      totalFrames: "Frame Dianalisis",
      reportDate: "Tanggal",
      reportDuration: "Durasi",
      reportActions: "Total Gerakan",
      reportHighlights: "Highlight",
      reportIssues: "Masalah Utama",
      reportSuggestions: "Saran",
      reportPlan: "Rencana Latihan",
      reportReview: "Catatan Review",
      coachTitle: "Pelatih AI",
      coachDesc: "Tanya tentang teknik, footwork, rencana latihan, review pertandingan, dan pencegahan cedera. Setelah analisis video, pelatih menggunakan laporan Anda sebagai konteks.",
      coachChatTitle: "Pelatih Latihan",
      coachModelLabel: "Model",
      coachZhipu: "Zhipu AI",
      coachPlaceholder: "cth: Bagaimana cara meningkatkan power smash backcourt saya?",
      coachConfigTitle: "Pengaturan Pelatih",
      coachUseReport: "Gunakan konteks laporan latihan",
      coachContextLabel: "Konteks Saat Ini",
      coachNoReport: "Belum ada laporan",
      coachContextDesc: "Setelah analisis video, pelatih AI membaca gerakan, pukulan, kepercayaan, dan skor footwork untuk menjawab pertanyaan.",
      historyTitle: "Riwayat Latihan",
      historyDesc: "Lihat catatan latihan sebelumnya, lacak tren kualitas, dan bandingkan kemajuan.",
      histSessions: "Sesi",
      histAvgScore: "Skor Rata-rata",
      histTotalShots: "Total Pukulan",
      histLastDate: "Sesi Terakhir",
      trendChart: "Tren Skor",
      sessionList: "Catatan Sesi",
      noHistory: "Belum ada catatan latihan. Selesaikan analisis video untuk melihat riwayat.",
      settingsTitle: "Pengaturan Sistem",
      settingsDesc: "Konfigurasi bahasa antarmuka, parameter model, pemrosesan video, dan preferensi.",
      langSettings: "Bahasa",
      langSettingsDesc: "Pilih bahasa tampilan. Pengaturan disimpan otomatis dan diterapkan ke seluruh situs.",
      modelConfig: "Konfigurasi Model",
      inferenceBackend: "Backend Inferensi",
      computeDevice: "Perangkat",
      inputResolution: "Resolusi Input",
      modelPrecision: "Presisi",
      fp32: "FP32 (Presisi Tinggi)",
      fp16: "FP16 (Seimbang)",
      int8: "INT8 (Cepat)",
      videoConfig: "Pemrosesan Video",
      frameRate: "Frame Rate",
      frameSkip: "Lompat Frame",
      roiArea: "Area ROI",
      saveDetection: "Simpan Hasil",
      dontSave: "Jangan Simpan",
      saveJson: "Simpan sebagai JSON",
      actions: "Aksi",
      precheckPassMsg: "Kualitas video baik, siap dianalisis",
      precheckPassMatchMsg: "Video pertandingan sudut lebar terdeteksi, siap dianalisis",
      precheckWarnMsg: "Ada masalah kecil, analisis dapat dilanjutkan dengan akurasi terbatas",
      precheckWarnMatchMsg: "Video sudut lebar, parameter akan disesuaikan otomatis",
      precheckFailMsg: "Kualitas video buruk, silakan periksa dan unggah ulang",
      btnLogin: "Masuk / Daftar",
      login: "Masuk",
      register: "Daftar",
      logout: "Keluar",
      switchAccount: "Ganti Akun",
      username: "Nama Pengguna",
      usernameOrEmail: "Nama Pengguna/Email",
      nickname: "Nama Panggilan",
      email: "Email",
      password: "Kata Sandi",
      avatarUrl: "URL Avatar",
      editProfile: "Edit Profil",
      save: "Simpan",
      cancel: "Batal",
      accountSettings: "Pengaturan Akun",
      notLoggedIn: "Anda belum masuk",
      loginHint: "Masuk untuk menyinkronkan catatan latihan dan terhubung dengan Mini Program WeChat",
      wechatBound: "WeChat terhubung",
      wechatNotBound: "WeChat belum terhubung",
      bindWechat: "Hubungkan WeChat",
      bindWechatTitle: "Hubungkan Mini Program WeChat",
      bindWechatDesc: "Buka Mini Program WeChat, ketuk 'Hubungkan Akun Web' di halaman 'Saya', dan masukkan kode di bawah",
      copyBindCode: "Salin Kode",
      bindWaiting: "Menunggu penghubungan...",
      bindSuccess: "Penghubungan berhasil",
      bindExpired: "Kode sudah kedaluwarsa, silakan dapatkan yang baru",
      bindFailed: "Penghubungan gagal, silakan coba lagi",
      wechatLogin: "Masuk dengan WeChat",
      wechatRegister: "Daftar dengan WeChat",
      orLoginWith: "Atau masuk dengan",
      orRegisterWith: "Atau daftar dengan",
      wechatHint: "Login WeChat hanya tersedia di dalam Mini Program",
      loginSuccess: "Berhasil masuk",
      registerSuccess: "Pendaftaran berhasil",
      logoutSuccess: "Berhasil keluar",
      profileUpdateSuccess: "Profil diperbarui",
      loginFailed: "Gagal masuk",
      registerFailed: "Pendaftaran gagal",
      videoSizeExceeded: "Video melebihi batas 500MB. Silakan kompres atau potong sebelum mengunggah.",
      tourWelcomeTitle: "Selamat datang di Badminton Smart Coach",
      tourWelcomeDesc: "Ikuti panduan singkat ini untuk memulai.",
      tourStep1Title: "Langkah 1: Unggah Video",
      tourStep1Desc: "Klik di sini untuk mengunggah video latihan atau pertandingan bulu tangkis. Drag and drop juga didukung.",
      tourStep2Title: "Langkah 2: Mulai Analisis",
      tourStep2Desc: "Setelah diunggah, klik Mulai Analisis dan AI akan mengevaluasi pukulan dan footwork Anda.",
      tourStep3Title: "Langkah 3: Timeline Pukulan",
      tourStep3Desc: "Setelah analisis selesai, setiap pukulan akan ditampilkan di sini dengan detailnya.",
      tourStep4Title: "Langkah 4: Laporan Latihan",
      tourStep4Desc: "Beralih ke tab Laporan Latihan untuk melihat statistik, radar chart, dan saran pelatih AI.",
      tourStep5Title: "Langkah 5: Riwayat",
      tourStep5Desc: "Semua analisis disimpan dalam Riwayat Latihan untuk ditinjau kapan saja.",
      tourNext: "Lanjut",
      tourSkip: "Lewati",
      tourFinish: "Selesai",
    },
  };

  const SUPPORTED_LANGS = ["zh", "en", "ja", "ko", "id"];
  const LANG_DISPLAY = {
    zh: { name: "中文", flag: "🇨🇳", avatar: "教", userAvatar: "我" },
    en: { name: "English", flag: "🇬🇧", avatar: "AI", userAvatar: "Me" },
    ja: { name: "日本語", flag: "🇯🇵", avatar: "AI", userAvatar: "私" },
    ko: { name: "한국어", flag: "🇰🇷", avatar: "AI", userAvatar: "나" },
    id: { name: "Bahasa", flag: "🇮🇩", avatar: "AI", userAvatar: "Me" },
  };

  function t(key, lang) {
    const l = lang || state.uiLanguage || "zh";
    const dict = GLOBAL_I18N[l] || GLOBAL_I18N.zh;
    return dict[key] !== undefined ? dict[key] : (GLOBAL_I18N.zh[key] || key);
  }

  function applyGlobalLanguage(lang) {
    if (!SUPPORTED_LANGS.includes(lang)) lang = "zh";
    state.uiLanguage = lang;
    try { localStorage.setItem("badminton_lang", lang); } catch (e) {}

    document.documentElement.lang = lang === "zh" ? "zh-CN" : lang;
    document.title = t("pageTitle", lang);

    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      const text = t(key, lang);
      if (text) el.textContent = text;
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      const text = t(key, lang);
      if (text) el.placeholder = text;
    });
    document.querySelectorAll("[data-i18n-title]").forEach((el) => {
      const key = el.getAttribute("data-i18n-title");
      const text = t(key, lang);
      if (text) el.title = text;
    });

    document.querySelectorAll(".lang-option").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.lang === lang);
    });

    const ld = LANG_DISPLAY[lang];
    if (elements.coachWelcome) elements.coachWelcome.textContent = getCoachWelcomeText(lang);
    if (elements.coachQuestion) elements.coachQuestion.placeholder = t("coachPlaceholder", lang);
    if (elements.btnCoachSend && !elements.btnCoachSend.disabled) elements.btnCoachSend.textContent = t("btnSend", lang);

    if (elements.coachUseReportLabel) elements.coachUseReportLabel.textContent = t("coachUseReport", lang);
    if (elements.coachContextLabel) elements.coachContextLabel.textContent = t("coachContextLabel", lang);
    if (elements.coachContextDesc) elements.coachContextDesc.textContent = t("coachContextDesc", lang);
    if (elements.coachSideTitle) elements.coachSideTitle.textContent = t("coachConfigTitle", lang);
    if (elements.coachChatTitle) elements.coachChatTitle.textContent = t("coachChatTitle", lang);

    updateCoachContextStatus();
    renderCoachPromptButtons(lang);
    updateCoachAvatars(lang);
    updateTopbarTitle();
  }

  function getCoachWelcomeText(lang) {
    const dict = {
      zh: "你好，我是羽动智练 AI 教练。你可以问我发力、步伐、训练计划、比赛复盘，也可以在完成视频分析后让我结合本次报告给建议。",
      en: "Hello! I'm your BadmintonAI Coach. Ask me about technique, footwork, training plans, match review, or share your analysis report for personalized advice.",
      ja: "こんにちは、BadmintonAIコーチです。技術、フットワーク、練習計画、試合の复盘について質問できます。動画分析後はレポートを基にアドバイスします。",
      ko: "안녕하세요, BadmintonAI 코치입니다. 기술, 풋워크, 훈련 계획, 경기 복기에 대해 질문하실 수 있습니다. 영상 분석 후 리포트를 바탕으로 조언해 드립니다.",
      id: "Halo! Saya Pelatih AI BadmintonAI. Tanya saya tentang teknik, footwork, rencana latihan, review tanding, atau bagikan laporan analisis untuk saran personal.",
    };
    return dict[lang] || dict.zh;
  }

  function renderCoachPromptButtons(lang) {
    if (!elements.coachPrompts) return;
    const prompts = {
      zh: [
        { label: "总结本次问题", prompt: "帮我根据本次训练报告总结三个最优先改进的问题。" },
        { label: "20分钟步伐训练", prompt: "给我安排一套 20 分钟羽毛球步伐训练计划。" },
        { label: "回位慢怎么改", prompt: "我击球后回位慢，应该从哪些动作细节改？" },
        { label: "热身放松建议", prompt: "羽毛球训练前后应该怎么热身和放松？" },
      ],
      en: [
        { label: "Summarize Issues", prompt: "Based on this training report, summarize the top 3 priority issues to improve." },
        { label: "20min Footwork", prompt: "Create a 20-minute badminton footwork training plan for me." },
        { label: "Slow Recovery", prompt: "My recovery after hitting is slow - what technical details should I fix?" },
        { label: "Warm-up/Cool-down", prompt: "How should I warm up before and cool down after badminton training?" },
      ],
      ja: [
        { label: "問題をまとめる", prompt: "今回のトレーニングレポートから、最優先で改善すべき3つの問題をまとめてください。" },
        { label: "20分フットワーク", prompt: "20分間のバドミントンフットワーク練習メニューを作ってください。" },
        { label: "戻りが遅い", prompt: "ショット後の戻りが遅いのですが、どの技術的詳細を改善すべきですか？" },
        { label: "ウォームアップ", prompt: "バドミントンの練習前後のウォームアップとクールダウン方法を教えてください。" },
      ],
      ko: [
        { label: "문제점 요약", prompt: "이번 트레이닝 리포트에서 가장 우선적으로 개선해야 할 3가지 문제를 요약해 주세요." },
        { label: "20분 풋워크", prompt: "20분 배드민턴 풋워크 훈련 계획을 만들어 주세요." },
        { label: "복귀 느림", prompt: "샷 후 복귀가 느린데 어떤 기술적 세부사항을 고쳐야 하나요?" },
        { label: "워밍업", prompt: "배드민턴 훈련 전후 워밍업과 쿨다운 방법을 알려주세요." },
      ],
      id: [
        { label: "Ringkas Masalah", prompt: "Berdasarkan laporan latihan ini, rangkum 3 masalah prioritas utama untuk diperbaiki." },
        { label: "Footwork 20menit", prompt: "Buatkan rencana latihan footwork bulu tangkis 20 menit untuk saya." },
        { label: "Recovery Lambat", prompt: "Recovery setelah pukulan saya lambat - detail teknis apa yang harus diperbaiki?" },
        { label: "Pemanasan", prompt: "Bagaimana cara pemanasan sebelum dan pendinginan setelah latihan bulu tangkis?" },
      ],
    };
    const items = prompts[lang] || prompts.zh;
    elements.coachPrompts.innerHTML = items.map(item =>
      `<button type="button" class="coach-prompt" data-prompt="${item.prompt.replace(/"/g, '&quot;')}">${item.label}</button>`
    ).join("");
    elements.coachPrompts.querySelectorAll(".coach-prompt").forEach((button) => {
      button.addEventListener("click", () => {
        const promptText = button.dataset.prompt || button.textContent || "";
        if (elements.coachQuestion) {
          elements.coachQuestion.value = promptText;
          elements.coachQuestion.focus();
        }
      });
    });
  }

  function updateCoachAvatars(lang) {
    const ld = LANG_DISPLAY[lang] || LANG_DISPLAY.zh;
    document.querySelectorAll(".coach-message").forEach((msg) => {
      const avatar = msg.querySelector(".coach-avatar");
      if (!avatar) return;
      if (msg.classList.contains("user")) {
        avatar.textContent = ld.userAvatar;
      } else {
        avatar.textContent = ld.avatar;
      }
    });
  }

  // ---- Animated Background (floating shuttlecocks) ----
  function createShuttlecockSVG(size) {
    const s = size || 24;
    return `<svg width="${s}" height="${s}" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <ellipse cx="16" cy="24" rx="5" ry="3.5" fill="#f0f5f2" stroke="#5eff9f" stroke-width="0.8"/>
      <ellipse cx="16" cy="24" rx="3.5" ry="2.2" fill="#c8ddd3" opacity="0.6"/>
      <path d="M11 23 L8 6 M13 23 L11 5 M16 23 L16 4 M19 23 L21 5 M21 23 L24 6" stroke="#e8f5ee" stroke-width="1.2" stroke-linecap="round"/>
      <path d="M9 8 Q16 3 23 8" stroke="#5eff9f" stroke-width="0.6" fill="none" opacity="0.5"/>
      <path d="M10 13 Q16 9 22 13" stroke="#5eff9f" stroke-width="0.5" fill="none" opacity="0.4"/>
      <path d="M11 18 Q16 15 21 18" stroke="#5eff9f" stroke-width="0.5" fill="none" opacity="0.3"/>
    </svg>`;
  }

  function spawnShuttlecock() {
    const container = document.getElementById("bgAnimation");
    if (!container) return;
    const el = document.createElement("div");
    el.className = "shuttlecock";
    const size = 16 + Math.random() * 20;
    el.innerHTML = createShuttlecockSVG(size);
    const startX = Math.random() * 100;
    const duration = 12 + Math.random() * 18;
    const delay = Math.random() * 2;
    el.style.left = startX + "%";
    el.style.bottom = "-40px";
    el.style.animationDuration = duration + "s";
    el.style.animationDelay = delay + "s";
    const driftX = (Math.random() - 0.5) * 80;
    el.style.setProperty("--drift-x", driftX + "px");
    container.appendChild(el);
    setTimeout(() => { if (el.parentNode) el.parentNode.removeChild(el); }, (duration + delay) * 1000 + 500);
  }

  function initAnimatedBackground() {
    for (let i = 0; i < 6; i++) {
      setTimeout(() => spawnShuttlecock(), i * 800);
    }
    setInterval(spawnShuttlecock, 2500 + Math.random() * 2000);
  }

  // ---- State ----
  const state = {
    connected: false,
    detecting: false,
    realVideoLoaded: false,
    videoFile: null,
    precheckPassed: false,
    precheckResult: null,
    analysisReport: null,
    frameImage: null,
    bbox: null,
    courtCorners: [],
    detections: 0,
    fps: 0,
    latency: 0,
    avgConf: 0,
    history: [],
    radarData: [0, 0, 0, 0, 0, 0],
    footworkTrace: [],
    shotEvents: [],
    playbackDuration: 0,
    coachHistory: [],
    analysisTimerId: null,
    analysisStartedAt: 0,
    courtAnimationFrame: null,
    analysisVideoObjectUrl: null,
    uiLanguage: "zh",
    user: null,
    authToken: null,
  };

  // ---- DOM Elements ----
  const elements = {
    statusIndicator: document.getElementById("statusIndicator"),
    statusText: document.querySelector(".status-text"),
    topbarTitle: document.getElementById("topbarTitle"),

    // Tabs
    mainTabs: document.getElementById("mainTabs"),
    panels: {
      training: document.getElementById("panel-training"),
      analysis: document.getElementById("panel-analysis"),
      report: document.getElementById("panel-report"),
      coach: document.getElementById("panel-coach"),
      history: document.getElementById("panel-history"),
      settings: document.getElementById("panel-settings"),
    },

    // Canvas
    frameCanvas: document.getElementById("frameCanvas"),
    frameCanvasWrap: document.getElementById("frameCanvasWrap"),
    analysisVideo: document.getElementById("analysisVideo"),
    videoActions: document.getElementById("videoActions"),
    videoStatusText: document.getElementById("videoStatusText"),
    downloadVideoLink: document.getElementById("downloadVideoLink"),
    emptyMedia: document.getElementById("emptyMedia"),
    videoUploadInput: document.getElementById("videoUploadInput"),
    analysisTimer: document.getElementById("analysisTimer"),
    analysisStage: document.getElementById("analysisStage"),
    analysisElapsed: document.getElementById("analysisElapsed"),
    analysisProgressBar: document.getElementById("analysisProgressBar"),
    shotTimeline: document.getElementById("shotTimeline"),
    shotTimelineEmpty: document.getElementById("shotTimelineEmpty"),
    shotTimelineSummary: document.getElementById("shotTimelineSummary"),
    courtCanvas: document.getElementById("courtCanvas"),
    radarCanvas: document.getElementById("radarCanvas"),

    // Controls
    btnStart: document.getElementById("btnStart"),
    btnStop: document.getElementById("btnStop"),
    btnReset: document.getElementById("btnReset"),
    btnSettings: document.getElementById("btnSettings"),
    btnExport: document.getElementById("btnExport"),
    btnSaveSettings: document.getElementById("btnSaveSettings"),
    btnResetSettings: document.getElementById("btnResetSettings"),

    // Shooting guide & precheck
    guideToggle: document.getElementById("guideToggle"),
    shootingGuide: document.getElementById("shootingGuide"),
    precheckPanel: document.getElementById("precheckPanel"),
    precheckStatus: document.getElementById("precheckStatus"),
    precheckItems: document.getElementById("precheckItems"),
    precheckActions: document.getElementById("precheckActions"),
    btnProceedAnalyze: document.getElementById("btnProceedAnalyze"),
    btnReupload: document.getElementById("btnReupload"),

    // History page
    historyList: document.getElementById("historyList"),
    historyTotalSessions: document.getElementById("historyTotalSessions"),
    historyAvgScore: document.getElementById("historyAvgScore"),
    historyTotalShots: document.getElementById("historyTotalShots"),
    historyLastDate: document.getElementById("historyLastDate"),
    trendChart: document.getElementById("trendChart"),
    btnRefreshHistory: document.getElementById("btnRefreshHistory"),

    // Inputs
    modelSelect: document.getElementById("modelSelect"),
    confThreshold: document.getElementById("confThreshold"),
    videoSource: document.getElementById("videoSource"),
    inferenceBackend: document.getElementById("inferenceBackend"),
    computeDevice: document.getElementById("computeDevice"),
    inputResolution: document.getElementById("inputResolution"),
    modelPrecision: document.getElementById("modelPrecision"),
    frameRate: document.getElementById("frameRate"),
    frameSkip: document.getElementById("frameSkip"),
    roiX1: document.getElementById("roiX1"),
    roiY1: document.getElementById("roiY1"),
    roiX2: document.getElementById("roiX2"),
    roiY2: document.getElementById("roiY2"),
    saveDetection: document.getElementById("saveDetection"),
    configOutput: document.getElementById("configOutput"),

    // Metrics
    metricFps: document.getElementById("metricFps"),
    metricDetections: document.getElementById("metricDetections"),
    metricConf: document.getElementById("metricConf"),
    metricLatency: document.getElementById("metricLatency"),

    // Analysis
    actionType: document.getElementById("actionType"),
    actionScore: document.getElementById("actionScore"),
    powerLevel: document.getElementById("powerLevel"),
    qualitySmooth: document.getElementById("qualitySmooth"),
    qualityAccuracy: document.getElementById("qualityAccuracy"),
    qualityCoord: document.getElementById("qualityCoord"),
    qualityFoot: document.getElementById("qualityFoot"),
    qualityWrist: document.getElementById("qualityWrist"),
    qualityBalance: document.getElementById("qualityBalance"),
    barSmooth: document.getElementById("barSmooth"),
    barAccuracy: document.getElementById("barAccuracy"),
    barCoord: document.getElementById("barCoord"),
    barFoot: document.getElementById("barFoot"),
    barWrist: document.getElementById("barWrist"),
    barBalance: document.getElementById("barBalance"),
    historyTable: document.getElementById("historyTable"),

    // Report
    totalSessions: document.getElementById("totalSessions"),
    avgScore: document.getElementById("avgScore"),
    bestAction: document.getElementById("bestAction"),
    totalFrames: document.getElementById("totalFrames"),
    reportDate: document.getElementById("reportDate"),
    reportDuration: document.getElementById("reportDuration"),
    reportActions: document.getElementById("reportActions"),
    reportHighlights: document.getElementById("reportHighlights"),
    reportIssues: document.getElementById("reportIssues"),
    reportSuggestions: document.getElementById("reportSuggestions"),
    reportPlan: document.getElementById("reportPlan"),
    reportReview: document.getElementById("reportReview"),

    // AI Coach
    coachProvider: document.getElementById("coachProvider"),
    coachWelcome: document.getElementById("coachWelcome"),
    coachMessages: document.getElementById("coachMessages"),
    coachQuestion: document.getElementById("coachQuestion"),
    btnCoachSend: document.getElementById("btnCoachSend"),
    coachUseReport: document.getElementById("coachUseReport"),
    coachContextStatus: document.getElementById("coachContextStatus"),
    coachSideTitle: document.getElementById("coachSideTitle"),
    coachUseReportLabel: document.getElementById("coachUseReportLabel"),
    coachContextLabel: document.getElementById("coachContextLabel"),
    coachContextDesc: document.getElementById("coachContextDesc"),
    coachChatTitle: document.getElementById("coachChatTitle"),
    coachPrompts: document.getElementById("coachPrompts"),

    // Auth
    btnLogin: document.getElementById("btnLogin"),
    userMenu: document.getElementById("userMenu"),
    btnUserAvatar: document.getElementById("btnUserAvatar"),
    userAvatarCircle: document.getElementById("userAvatarCircle"),
    userDropdown: document.getElementById("userDropdown"),
    userNickname: document.getElementById("userNickname"),
    userUsername: document.getElementById("userUsername"),
    wechatBadge: document.getElementById("wechatBadge"),
    btnSwitchAccount: document.getElementById("btnSwitchAccount"),
    btnLogout: document.getElementById("btnLogout"),
    authModal: document.getElementById("authModal"),
    btnCloseAuthModal: document.getElementById("btnCloseAuthModal"),
    loginForm: document.getElementById("loginForm"),
    registerForm: document.getElementById("registerForm"),
    loginUsername: document.getElementById("loginUsername"),
    loginPassword: document.getElementById("loginPassword"),
    loginError: document.getElementById("loginError"),
    regUsername: document.getElementById("regUsername"),
    regNickname: document.getElementById("regNickname"),
    regEmail: document.getElementById("regEmail"),
    regPassword: document.getElementById("regPassword"),
    registerError: document.getElementById("registerError"),
    btnWechatLogin: document.getElementById("btnWechatLogin"),
    btnWechatRegister: document.getElementById("btnWechatRegister"),
    wechatHint: document.getElementById("wechatHint"),
    btnSettingsLogin: document.getElementById("btnSettingsLogin"),
    accountGuest: document.getElementById("accountGuest"),
    accountLogged: document.getElementById("accountLogged"),
    settingsAvatar: document.getElementById("settingsAvatar"),
    settingsNickname: document.getElementById("settingsNickname"),
    settingsUsername: document.getElementById("settingsUsername"),
    settingsWechatStatus: document.getElementById("settingsWechatStatus"),
    btnEditProfile: document.getElementById("btnEditProfile"),
    btnBindWechat: document.getElementById("btnBindWechat"),
    btnSettingsLogout: document.getElementById("btnSettingsLogout"),
    profileModal: document.getElementById("profileModal"),
    btnCloseProfileModal: document.getElementById("btnCloseProfileModal"),
    profileForm: document.getElementById("profileForm"),
    editNickname: document.getElementById("editNickname"),
    editAvatar: document.getElementById("editAvatar"),
    profileError: document.getElementById("profileError"),
    btnCancelProfile: document.getElementById("btnCancelProfile"),
    btnSaveProfile: document.getElementById("btnSaveProfile"),

    // Bind WeChat
    bindWechatModal: document.getElementById("bindWechatModal"),
    btnCloseBindWechatModal: document.getElementById("btnCloseBindWechatModal"),
    bindCodeDisplay: document.getElementById("bindCodeDisplay"),
    btnCopyBindCode: document.getElementById("btnCopyBindCode"),
    bindStatus: document.getElementById("bindStatus"),
    bindTimer: document.getElementById("bindTimer"),

    // Tour
    tourOverlay: document.getElementById("tourOverlay"),
    tourHighlight: document.getElementById("tourHighlight"),
    tourCard: document.getElementById("tourCard"),
    tourTitle: document.getElementById("tourTitle"),
    tourDesc: document.getElementById("tourDesc"),
    tourDots: document.getElementById("tourDots"),
    btnSkipTour: document.getElementById("btnSkipTour"),
    btnNextTour: document.getElementById("btnNextTour"),
  };

  const ctx = elements.frameCanvas.getContext("2d");
  const courtCtx = elements.courtCanvas.getContext("2d");
  const radarCtx = elements.radarCanvas.getContext("2d");
  const API_BASE = window.location.protocol.startsWith("http")
    ? window.location.origin
    : "http://127.0.0.1:8000";
  const COURT_CORNER_KEYS = ["top_left", "top_right", "bottom_left", "bottom_right"];
  const COURT_CORNER_LABELS = ["TL", "TR", "BL", "BR"];
  const DELIVERY_ANALYSIS_CONFIG = Object.freeze({
    target_player: "largest",
    target_bbox: null,
    target_roi: "full",
    analysis_preset: "adaptive",
    conf_threshold: 0.3,
    footwork_map_mode: "image",
    llm_provider: "qwen",
    llm_timeout: 120,
    llm_shots_per_group: 8,
    reuse_annotated_video: true,
    write_shot_clips: false,
    skip_backend_precheck: true,
    use_cpu: false,
  });

  const COACH_I18N = {
    zh: {
      welcome: "你好，我是羽动智练 AI 教练。你可以问我发力、步伐、训练计划、比赛复盘，也可以在完成视频分析后让我结合本次报告给建议。",
      placeholder: "例如：我后场杀球总是发不上力，应该怎么练？",
      send: "发送",
      thinking: "思考中...",
      noQuestion: "请输入想问 AI 教练的问题",
      thinkingStatus: "思考进度：",
      firstStatus: "正在理解你的问题",
      generating: "正在生成回答...",
      genFailed: "AI 教练生成失败",
      noAnswer: "我暂时没有生成有效回答。",
      unavailable: "AI教练暂时不可用：",
      providerLabel: "模型",
      langLabel: "语言",
      coachTitle: "训练教练",
      contextTitle: "教练配置",
      contextLabel: "当前上下文",
      useReport: "结合本次训练分析",
      noReport: "暂无训练报告",
      contextDesc: "完成一次视频分析后，AI 教练会自动读取动作、击球片段、置信度和步伐评分，用于回答追问。",
      reportLoaded: "已加载训练报告",
      prompts: [
        { label: "总结本次问题", prompt: "帮我根据本次训练报告总结三个最优先改进的问题。" },
        { label: "20分钟步伐训练", prompt: "给我安排一套 20 分钟羽毛球步伐训练计划。" },
        { label: "回位慢怎么改", prompt: "我击球后回位慢，应该从哪些动作细节改？" },
        { label: "热身放松建议", prompt: "羽毛球训练前后应该怎么热身和放松？" },
      ],
    },
    en: {
      welcome: "Hello! I'm your BadmintonAI Coach. Ask me about technique, footwork, training plans, match review, or share your analysis report for personalized advice.",
      placeholder: "e.g., How can I improve my backcourt smash power?",
      send: "Send",
      thinking: "Thinking...",
      noQuestion: "Please enter a question for the AI coach",
      thinkingStatus: "Progress:",
      firstStatus: "Understanding your question",
      generating: "Generating response...",
      genFailed: "AI coach generation failed",
      noAnswer: "I couldn't generate a valid response at this time.",
      unavailable: "AI coach unavailable: ",
      providerLabel: "Model",
      langLabel: "Language",
      coachTitle: "Training Coach",
      contextTitle: "Coach Settings",
      contextLabel: "Current Context",
      useReport: "Use training analysis context",
      noReport: "No training report yet",
      contextDesc: "After completing a video analysis, the AI coach will automatically read actions, shots, confidence, and footwork scores to answer follow-up questions.",
      reportLoaded: "Report loaded",
      prompts: [
        { label: "Summarize Issues", prompt: "Based on this training report, summarize the top 3 priority issues to improve." },
        { label: "20min Footwork", prompt: "Create a 20-minute badminton footwork training plan for me." },
        { label: "Slow Recovery", prompt: "My recovery after hitting is slow - what technical details should I fix?" },
        { label: "Warm-up/Cool-down", prompt: "How should I warm up before and cool down after badminton training?" },
      ],
    },
    ja: {
      welcome: "こんにちは、BadmintonAIコーチです。技術、フットワーク、練習計画、試合の复盘について質問できます。動画分析後はレポートを基にアドバイスします。",
      placeholder: "例：後衛のスマッシュ力を上げるにはどうすればいいですか？",
      send: "送信",
      thinking: "考え中...",
      noQuestion: "AIコーチへの質問を入力してください",
      thinkingStatus: "思考進捗：",
      firstStatus: "質問を理解しています",
      generating: "回答を生成中...",
      genFailed: "AIコーチの生成に失敗しました",
      noAnswer: "有効な回答を生成できませんでした。",
      unavailable: "AIコーチは一時的に利用できません：",
      providerLabel: "モデル",
      langLabel: "言語",
      coachTitle: "トレーニングコーチ",
      contextTitle: "コーチ設定",
      contextLabel: "現在のコンテキスト",
      useReport: "トレーニング分析結果を使用",
      noReport: "トレーニングレポートがありません",
      contextDesc: "動画分析完了後、AIコーチはアクション、ショット、信頼度、フットワークスコアを自動的に読み取り、質問に回答します。",
      reportLoaded: "レポート読み込み済み",
      prompts: [
        { label: "問題をまとめる", prompt: "今回のトレーニングレポートから、最優先で改善すべき3つの問題をまとめてください。" },
        { label: "20分フットワーク", prompt: "20分間のバドミントンフットワーク練習メニューを作ってください。" },
        { label: "戻りが遅い", prompt: "ショット後の戻りが遅いのですが、どの技術的詳細を改善すべきですか？" },
        { label: "ウォームアップ", prompt: "バドミントンの練習前後のウォームアップとクールダウン方法を教えてください。" },
      ],
    },
    ko: {
      welcome: "안녕하세요, BadmintonAI 코치입니다. 기술, 풋워크, 훈련 계획, 경기 복기에 대해 질문하실 수 있습니다. 영상 분석 후 리포트를 바탕으로 조언해 드립니다.",
      placeholder: "예: 백핸드 스매시 파워를 높이려면 어떻게 해야 하나요?",
      send: "전송",
      thinking: "생각 중...",
      noQuestion: "AI 코치에게 질문을 입력해 주세요",
      thinkingStatus: "진행 상황:",
      firstStatus: "질문을 이해하는 중",
      generating: "답변 생성 중...",
      genFailed: "AI 코치 생성 실패",
      noAnswer: "유효한 답변을 생성하지 못했습니다.",
      unavailable: "AI 코치를 일시적으로 사용할 수 없습니다: ",
      providerLabel: "모델",
      langLabel: "언어",
      coachTitle: "트레이닝 코치",
      contextTitle: "코치 설정",
      contextLabel: "현재 컨텍스트",
      useReport: "트레이닝 분석 결과 사용",
      noReport: "트레이닝 리포트 없음",
      contextDesc: "영상 분석 완료 후 AI 코치가 액션, 샷, 신뢰도, 풋워크 점수를 자동으로 읽어 후속 질문에 답변합니다.",
      reportLoaded: "리포트 로드됨",
      prompts: [
        { label: "문제점 요약", prompt: "이번 트레이닝 리포트에서 가장 우선적으로 개선해야 할 3가지 문제를 요약해 주세요." },
        { label: "20분 풋워크", prompt: "20분 배드민턴 풋워크 훈련 계획을 만들어 주세요." },
        { label: "복귀 느림", prompt: "샷 후 복귀가 느린데 어떤 기술적 세부사항을 고쳐야 하나요?" },
        { label: "워밍업", prompt: "배드민턴 훈련 전후 워밍업과 쿨다운 방법을 알려주세요." },
      ],
    },
    id: {
      welcome: "Halo! Saya Pelatih AI BadmintonAI. Tanya saya tentang teknik, footwork, rencana latihan, review tanding, atau bagikan laporan analisis untuk saran personal.",
      placeholder: "cth: Bagaimana cara meningkatkan power smash backcourt saya?",
      send: "Kirim",
      thinking: "Berpikir...",
      noQuestion: "Silakan masukkan pertanyaan untuk pelatih AI",
      thinkingStatus: "Proses:",
      firstStatus: "Memahami pertanyaan Anda",
      generating: "Menghasilkan jawaban...",
      genFailed: "Pelatih AI gagal menghasilkan jawaban",
      noAnswer: "Saya tidak dapat menghasilkan jawaban yang valid saat ini.",
      unavailable: "Pelatih AI tidak tersedia: ",
      providerLabel: "Model",
      langLabel: "Bahasa",
      coachTitle: "Pelatih Latihan",
      contextTitle: "Pengaturan Pelatih",
      contextLabel: "Konteks Saat Ini",
      useReport: "Gunakan konteks analisis latihan",
      noReport: "Belum ada laporan latihan",
      contextDesc: "Setelah analisis video selesai, pelatih AI akan membaca aksi, pukulan, keyakinan, dan skor footwork untuk menjawab pertanyaan lanjutan.",
      reportLoaded: "Laporan dimuat",
      prompts: [
        { label: "Ringkas Masalah", prompt: "Berdasarkan laporan latihan ini, rangkum 3 masalah prioritas utama untuk diperbaiki." },
        { label: "Footwork 20menit", prompt: "Buatkan rencana latihan footwork bulu tangkis 20 menit untuk saya." },
        { label: "Recovery Lambat", prompt: "Recovery setelah pukulan saya lambat - detail teknis apa yang harus diperbaiki?" },
        { label: "Pemanasan", prompt: "Bagaimana cara pemanasan sebelum dan pendinginan setelah latihan bulu tangkis?" },
      ],
    },
  };

  function getCoachLang() {
    return SUPPORTED_LANGS.includes(state.uiLanguage) ? state.uiLanguage : "zh";
  }

  function coachT(key) {
    const dict = COACH_I18N[getCoachLang()] || COACH_I18N.zh;
    return dict[key] !== undefined ? dict[key] : (COACH_I18N.zh[key] || "");
  }

  function updateCoachUILanguage() {
    const lang = getCoachLang();
    renderCoachPromptButtons(lang);
    updateCoachContextStatus();
    if (elements.btnCoachSend && !elements.btnCoachSend.disabled) {
      elements.btnCoachSend.textContent = t("btnSend", state.uiLanguage);
    }
  }

  function updateTopbarTitle() {
    const active = document.querySelector(".nav-item.active");
    const tabMap = {
      "navTraining": { zh: "训练检测", en: "Detection", ja: "検出", ko: "검출", id: "Deteksi" },
      "navAnalysis": { zh: "动作分析", en: "Analysis", ja: "分析", ko: "분석", id: "Analisis" },
      "navReport":   { zh: "训练报告", en: "Report", ja: "レポート", ko: "리포트", id: "Laporan" },
      "navCoach":    { zh: "AI教练问答", en: "AI Coach", ja: "AIコーチ", ko: "AI 코치", id: "Pelatih AI" },
      "navHistory":  { zh: "训练历史", en: "History", ja: "履歴", ko: "기록", id: "Riwayat" },
      "navSettings": { zh: "系统设置", en: "Settings", ja: "設定", ko: "설정", id: "Pengaturan" },
    };
    const panel = elements?.topbarTitle?.closest(".topbar-panel");
    if (active && tabMap[active.id] && elements.topbarTitle) {
      elements.topbarTitle.textContent = tabMap[active.id][state.uiLanguage] || tabMap[active.id].zh;
    }
  }

  function apiUrl(path) {
    return `${API_BASE}${path}`;
  }

  // ---- Tab Switching ----
  function switchTab(tabName) {
    // Tabs
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.classList.toggle("active", tab.dataset.tab === tabName);
    });
    // Sidebar nav
    document.querySelectorAll(".nav-item").forEach((item) => {
      item.classList.toggle("active", item.dataset.tab === tabName);
    });
    // Panels
    Object.entries(elements.panels).forEach(([key, panel]) => {
      panel.classList.toggle("active", key === tabName);
    });
    // Update topbar title (i18n-aware)
    updateTopbarTitle();
  }

  // Tab click handlers
  elements.mainTabs.addEventListener("click", (e) => {
    const tab = e.target.closest(".tab");
    if (tab && tab.dataset.tab) {
      switchTab(tab.dataset.tab);
      if (tab.dataset.tab === "history") loadHistoryList();
    }
  });

  document.querySelector(".sidebar-nav").addEventListener("click", (e) => {
    const item = e.target.closest(".nav-item");
    if (item && item.dataset.tab) {
      switchTab(item.dataset.tab);
      if (item.dataset.tab === "history") loadHistoryList();
    }
  });

  if (elements.btnSettings) {
    elements.btnSettings.addEventListener("click", () => switchTab("settings"));
  }

  // ---- Connection Status ----
  function setConnected(connected) {
    state.connected = connected;
    const indicator = elements.statusIndicator;
    if (!indicator) return;
    const statusText = indicator.querySelector(".status-text");
    indicator.classList.remove("connected", "error");
    const connLabels = { zh: { on: "已连接", off: "未连接" }, en: { on: "Connected", off: "Disconnected" }, ja: { on: "接続済み", off: "未接続" }, ko: { on: "연결됨", off: "연결 안됨" }, id: { on: "Terhubung", off: "Terputus" } };
    const lbl = connLabels[state.uiLanguage] || connLabels.zh;
    if (connected) {
      indicator.classList.add("connected");
      if (statusText) statusText.textContent = lbl.on;
    } else {
      if (statusText) statusText.textContent = lbl.off;
    }
  }

  // ---- Drawing Functions ----
  function courtCornersPayload() {
    if (!Array.isArray(state.courtCorners) || state.courtCorners.length !== 4) return null;
    return COURT_CORNER_KEYS.reduce((payload, key, idx) => {
      const point = state.courtCorners[idx];
      payload[key] = [Number(point.x.toFixed(4)), Number(point.y.toFixed(4))];
      return payload;
    }, {});
  }

  function drawCourtCalibration() {
    if (!state.courtCorners || !state.courtCorners.length) return;
    const canvas = elements.frameCanvas;
    const points = state.courtCorners.map((point) => ({
      x: point.x * canvas.width,
      y: point.y * canvas.height,
    }));
    ctx.save();
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#ffd166";
    ctx.fillStyle = "rgba(255, 209, 102, 0.22)";
    if (points.length >= 2) {
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i += 1) ctx.lineTo(points[i].x, points[i].y);
      if (points.length === 4) ctx.closePath();
      ctx.stroke();
      if (points.length === 4) ctx.fill();
    }
    points.forEach((point, idx) => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, 7, 0, Math.PI * 2);
      ctx.fillStyle = "#ffd166";
      ctx.fill();
      ctx.strokeStyle = "#1f2937";
      ctx.stroke();
      ctx.fillStyle = "#1f2937";
      ctx.font = "bold 11px JetBrains Mono, monospace";
      ctx.fillText(COURT_CORNER_LABELS[idx], point.x + 10, point.y - 10);
    });
    ctx.restore();
  }

  function addCourtCornerFromEvent(event) {
    if (!state.frameImage || !elements.frameCanvas) return;
    const rect = elements.frameCanvas.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    if (state.courtCorners.length >= 4) state.courtCorners = [];
    const x = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
    const y = Math.max(0, Math.min(1, (event.clientY - rect.top) / rect.height));
    state.courtCorners.push({ x, y });
    drawFrame();
    const nextLabel = COURT_CORNER_LABELS[state.courtCorners.length] || "OK";
    const message = state.courtCorners.length === 4
      ? "Court calibration complete. Footwork map will use calibrated mapping."
      : `Court corner ${state.courtCorners.length}/4 saved. Next: ${nextLabel}`;
    showToast(message, state.courtCorners.length === 4 ? "success" : "info");
  }

  function drawFrame(previewBox = null) {
    if (!state.frameImage) return;
    ctx.clearRect(0, 0, elements.frameCanvas.width, elements.frameCanvas.height);
    ctx.drawImage(state.frameImage, 0, 0, elements.frameCanvas.width, elements.frameCanvas.height);

    const box = previewBox || state.bbox;
    if (box) {

    const x1 = box.x1 * elements.frameCanvas.width;
    const y1 = box.y1 * elements.frameCanvas.height;
    const x2 = box.x2 * elements.frameCanvas.width;
    const y2 = box.y2 * elements.frameCanvas.height;
    ctx.save();
    ctx.fillStyle = "rgba(94, 255, 159, 0.15)";
    ctx.strokeStyle = "#5eff9f";
    ctx.lineWidth = 3;
    ctx.fillRect(x1, y1, x2 - x1, y2 - y1);
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    ctx.fillStyle = "#5eff9f";
    ctx.font = "bold 14px JetBrains Mono, monospace";
    ctx.fillText("TARGET", x1 + 8, Math.max(20, y1 - 8));
    ctx.restore();
    }
    drawCourtCalibration();
  }

  function showUploadHint(text) {
    if (!elements.emptyMedia) return;
    elements.frameCanvasWrap.style.display = "none";
    if (elements.analysisVideo) {
      elements.analysisVideo.hidden = true;
      elements.analysisVideo.removeAttribute("src");
    }
    if (elements.videoActions) {
      elements.videoActions.hidden = true;
    }
    elements.emptyMedia.style.display = "flex";
    elements.emptyMedia.innerHTML = `<span>${text}</span>`;
  }

  function drawUploadedVideoFrame(video) {
    const canvas = elements.frameCanvas;
    const sourceW = video.videoWidth || 640;
    const sourceH = video.videoHeight || 480;
    const targetW = 640;
    const targetH = Math.max(360, Math.round((targetW * sourceH) / sourceW));
    canvas.width = targetW;
    canvas.height = targetH;
    ctx.clearRect(0, 0, targetW, targetH);
    ctx.drawImage(video, 0, 0, targetW, targetH);

    const img = new Image();
    img.onload = () => {
      state.frameImage = img;
      state.bbox = null;
      state.courtCorners = [];
      elements.emptyMedia.style.display = "none";
      elements.frameCanvasWrap.style.display = "block";
      if (elements.analysisVideo) {
        elements.analysisVideo.hidden = true;
        elements.analysisVideo.removeAttribute("src");
      }
      if (elements.videoActions) {
        elements.videoActions.hidden = true;
      }
      elements.frameCanvas.hidden = false;
      drawFrame();
      setConnected(true);
    };
    img.src = canvas.toDataURL("image/jpeg", 0.9);
  }

  function drawFrameBlob(blob) {
    const imageUrl = URL.createObjectURL(blob);
    const img = new Image();
    img.onload = () => {
      const sourceW = img.naturalWidth || 640;
      const sourceH = img.naturalHeight || 480;
      const targetW = 640;
      const targetH = Math.max(360, Math.round((targetW * sourceH) / sourceW));
      elements.frameCanvas.width = targetW;
      elements.frameCanvas.height = targetH;
      state.frameImage = img;
      state.bbox = null;
      state.courtCorners = [];
      elements.emptyMedia.style.display = "none";
      elements.frameCanvasWrap.style.display = "block";
      if (elements.analysisVideo) {
        elements.analysisVideo.hidden = true;
        elements.analysisVideo.removeAttribute("src");
      }
      if (elements.videoActions) {
        elements.videoActions.hidden = true;
      }
      elements.frameCanvas.hidden = false;
      drawFrame();
      setConnected(true);
      URL.revokeObjectURL(imageUrl);
    };
    img.onerror = () => {
      URL.revokeObjectURL(imageUrl);
      showUploadHint("抽帧图片加载失败，请换一个视频重试");
    };
    img.src = imageUrl;
  }

  async function loadFrameFromBackend(file) {
    const form = new FormData();
    form.append("video", file);
    form.append("time_sec", "3");
    const response = await fetch(apiUrl("/api/frame"), {
      method: "POST",
      body: form,
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    drawFrameBlob(await response.blob());
  }

  async function loadUploadedVideo(file) {
    if (!file) return;
    if (!state.user) {
      showAuthModal("login");
      return;
    }
    const MAX_VIDEO_SIZE = 500 * 1024 * 1024;
    if (file.size > MAX_VIDEO_SIZE) {
      showUploadHint(t("videoSizeExceeded"));
      if (elements.videoUploadInput) elements.videoUploadInput.value = "";
      return;
    }
    stopCourtPlaybackLoop();
    if (state.analysisTimerId) {
      window.clearInterval(state.analysisTimerId);
      state.analysisTimerId = null;
    }
    if (elements.analysisTimer) elements.analysisTimer.hidden = true;
    state.videoFile = file;
    state.analysisReport = null;
    state.realVideoLoaded = true;
    state.bbox = null;
    state.precheckPassed = false;
    state.precheckResult = null;
    hidePrecheckPanel();
    showUploadHint("正在读取视频画面...");
    if (window.location.protocol.startsWith("http")) {
      try {
        await loadFrameFromBackend(file);
        await runPrecheck(file);
        return;
      } catch (error) {
        showUploadHint(`后端抽帧失败：${formatFetchError(error)}，正在尝试浏览器预览...`);
      }
    }
    const url = URL.createObjectURL(file);
    const video = document.createElement("video");
    video.preload = "metadata";
    video.muted = true;
    video.playsInline = true;
    video.src = url;

    const cleanup = () => URL.revokeObjectURL(url);
    video.addEventListener("loadedmetadata", () => {
      const duration = Number.isFinite(video.duration) ? video.duration : 0;
      video.currentTime = duration > 2 ? Math.min(Math.max(duration * 0.12, 1), 5) : 0;
    });
    video.addEventListener("seeked", () => {
      drawUploadedVideoFrame(video);
      cleanup();
    }, { once: true });
    video.addEventListener("loadeddata", () => {
      if (!Number.isFinite(video.duration) || video.duration <= 2) {
        drawUploadedVideoFrame(video);
        cleanup();
      }
    }, { once: true });
    video.addEventListener("error", () => {
      cleanup();
      showUploadHint("视频读取失败，请换一个 MP4 文件重试");
    }, { once: true });
  }

  function showPrecheckPanel() {
    if (elements.precheckPanel) elements.precheckPanel.hidden = false;
  }

  function hidePrecheckPanel() {
    if (elements.precheckPanel) {
      elements.precheckPanel.hidden = true;
      elements.precheckItems.innerHTML = "";
      elements.precheckActions.hidden = true;
    }
  }

  function renderPrecheckResult(result) {
    state.precheckResult = result;
    showPrecheckPanel();
    const statusEl = elements.precheckStatus;
    statusEl.className = "precheck-status " + (result.overall || (result.ok ? "pass" : "fail"));
    const scene = result.scene_type;
    if (result.overall === "pass" || result.ok) {
      statusEl.textContent = scene === "match_wide" ? t("precheckPassMatchMsg") : t("precheckPassMsg");
    } else if (result.overall === "warn") {
      statusEl.textContent = scene === "match_wide" ? t("precheckWarnMatchMsg") : t("precheckWarnMsg");
    } else {
      statusEl.textContent = t("precheckFailMsg");
    }

    elements.precheckItems.innerHTML = "";
    (result.items || []).forEach((item) => {
      const div = document.createElement("div");
      div.className = "precheck-item";
      const iconMap = { pass: "✅", warn: "⚠️", fail: "❌" };
      div.innerHTML = `
        <span class="check-icon ${item.status}">${iconMap[item.status] || "•"}</span>
        <span class="check-label">${item.name}</span>
        <span class="check-value">${item.value || ""}</span>
        ${item.detail ? `<div class="check-detail">${item.detail}</div>` : ""}
      `;
      elements.precheckItems.appendChild(div);
    });

    elements.precheckActions.hidden = false;
    state.precheckPassed = result.ok || result.overall !== "fail";
    if (elements.btnProceedAnalyze) {
      const startLabels = { zh: "开始分析", en: "Start Analysis", ja: "分析を開始", ko: "분석 시작", id: "Mulai Analisis" };
      const startWideLabels = { zh: "开始分析（比赛远景模式）", en: "Start Analysis (Wide-angle Mode)", ja: "分析を開始（広角モード）", ko: "분석 시작 (광각 모드)", id: "Mulai Analisis (Mode Sudut Lebar)" };
      const proceedLabels = { zh: "继续分析", en: "Continue Analysis", ja: "分析を続ける", ko: "분석 계속", id: "Lanjut Analisis" };
      if (result.overall === "pass") {
        elements.btnProceedAnalyze.textContent = startLabels[state.uiLanguage] || startLabels.zh;
      } else if (result.scene_type === "match_wide") {
        elements.btnProceedAnalyze.textContent = startWideLabels[state.uiLanguage] || startWideLabels.zh;
      } else {
        elements.btnProceedAnalyze.textContent = proceedLabels[state.uiLanguage] || proceedLabels.zh;
      }
      elements.btnProceedAnalyze.disabled = !state.precheckPassed;
    }
  }

  async function runPrecheck(file) {
    if (!window.location.protocol.startsWith("http")) return;
    showPrecheckPanel();
    elements.precheckStatus.textContent = t("precheckChecking");
    elements.precheckStatus.className = "precheck-status";
    const checkingLabels = { zh: "正在检测视频质量...", en: "Checking video quality...", ja: "動画画質をチェック中...", ko: "영상 화질 확인 중...", id: "Memeriksa kualitas video..." };
    elements.precheckItems.innerHTML = `<div class="precheck-item"><span class="check-icon">⏳</span><span class="check-label">${checkingLabels[state.uiLanguage] || checkingLabels.zh}</span></div>`;
    elements.precheckActions.hidden = true;

    try {
      const fd = new FormData();
      fd.append("video", file);
      const resp = await fetch("/api/precheck", { method: "POST", body: fd });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(err.detail || "Precheck failed");
      }
      const result = await resp.json();
      renderPrecheckResult(result);
    } catch (err) {
      const failLabels = { zh: "检测失败，可直接尝试分析", en: "Precheck failed, you may try analysis directly", ja: "チェック失敗、直接分析を試せます", ko: "검사 실패, 직접 분석을 시도할 수 있습니다", id: "Pemeriksaan gagal, Anda bisa mencoba analisis langsung" };
      elements.precheckStatus.textContent = failLabels[state.uiLanguage] || failLabels.zh;
      elements.precheckStatus.className = "precheck-status warn";
      const precheckFailLabels = { zh: "预检失败", en: "Precheck failed", ja: "プレチェック失敗", ko: "사전 검사 실패", id: "Pemeriksaan awal gagal" };
      elements.precheckItems.innerHTML = `<div class="precheck-item"><span class="check-icon warn">⚠️</span><span class="check-label">${precheckFailLabels[state.uiLanguage] || precheckFailLabels.zh}</span><span class="check-value">${err.message}</span></div>`;
      elements.precheckActions.hidden = false;
      state.precheckPassed = true;
      if (elements.btnProceedAnalyze) elements.btnProceedAnalyze.disabled = false;
    }
  }

  function buildAnalyzeConfig() {
    const lang = state.uiLanguage || "zh";
    const analysisPreset = state.precheckResult?.scene_type === "match_wide"
      ? "match_far"
      : DELIVERY_ANALYSIS_CONFIG.analysis_preset;
    const annotatedOutputFps = analysisPreset === "match_far" ? 15 : null;
    return {
      ...DELIVERY_ANALYSIS_CONFIG,
      analysis_preset: analysisPreset,
      annotated_output_fps: annotatedOutputFps,
      court_corners: courtCornersPayload(),
      generate_llm_report: false,
      language: SUPPORTED_LANGS.includes(lang) ? lang : "zh",
      llm_language: SUPPORTED_LANGS.includes(lang) ? lang : "zh",
    };
  }

  function formatElapsed(ms) {
    const seconds = Math.max(0, Number(ms || 0) / 1000);
    if (seconds < 60) return `${seconds.toFixed(1)} 秒`;
    const minutes = Math.floor(seconds / 60);
    const remain = Math.floor(seconds % 60);
    return `${minutes} 分 ${String(remain).padStart(2, "0")} 秒`;
  }

  function startAnalysisTimer(startedAt = performance.now()) {
    state.analysisStartedAt = startedAt;
    if (state.analysisTimerId) {
      window.clearInterval(state.analysisTimerId);
      state.analysisTimerId = null;
    }
    if (elements.analysisTimer) elements.analysisTimer.hidden = false;
    if (elements.analysisStage) {
      elements.analysisStage.textContent = t("processingStage1");
      delete elements.analysisStage.dataset.sseUpdated;
    }
    if (elements.analysisElapsed) elements.analysisElapsed.textContent = "0.0 秒";
    if (elements.analysisProgressBar) elements.analysisProgressBar.style.width = "3%";
    state.analysisTimerId = window.setInterval(() => {
      const elapsed = performance.now() - state.analysisStartedAt;
      if (elements.analysisElapsed) elements.analysisElapsed.textContent = formatElapsed(elapsed);
      if (elements.analysisStage && !elements.analysisStage.dataset.sseUpdated) {
        const stageLabels = {
          zh: ["上传视频并准备姿态分析", "抽帧并加载动作识别模型", "识别人体姿态和步伐轨迹", "生成标注视频与训练报告"],
          en: ["Uploading video and preparing pose analysis", "Extracting frames and loading models", "Detecting poses and footwork traces", "Generating annotated video and report"],
          ja: ["動画アップロードと姿勢分析準備", "フレーム抽出とモデル読み込み", "姿勢とフットワーク軌跡の検出", "注釈動画とレポートの生成"],
          ko: ["영상 업로드 및 자세 분석 준비", "프레임 추출 및 모델 로딩", "자세와 풋워크 궤적 감지", "주석 영상과 리포트 생성"],
          id: ["Mengunggah video dan menyiapkan analisis pose", "Mengekstrak frame dan memuat model", "Mendeteksi pose dan jejak footwork", "Menghasilkan video beranotasi dan laporan"],
        };
        const labels = stageLabels[state.uiLanguage] || stageLabels.zh;
        let idx = 0;
        if (elapsed > 45000) idx = 3;
        else if (elapsed > 15000) idx = 2;
        else if (elapsed > 5000) idx = 1;
        elements.analysisStage.textContent = labels[idx];
      }
    }, 100);
  }

  function updateAnalysisProgress(percent, message) {
    const pct = Math.max(0, Math.min(100, Number(percent) || 0));
    if (elements.analysisProgressBar) elements.analysisProgressBar.style.width = pct + "%";
    if (message && elements.analysisStage) {
      elements.analysisStage.textContent = message;
      elements.analysisStage.dataset.sseUpdated = "1";
    }
  }

  function stopAnalysisTimer(statusText, elapsedMs = null) {
    if (state.analysisTimerId) {
      window.clearInterval(state.analysisTimerId);
      state.analysisTimerId = null;
    }
    const elapsed = elapsedMs == null ? performance.now() - state.analysisStartedAt : elapsedMs;
    if (elements.analysisTimer) elements.analysisTimer.hidden = false;
    if (elements.analysisStage) elements.analysisStage.textContent = statusText;
    if (elements.analysisElapsed) elements.analysisElapsed.textContent = formatElapsed(elapsed);
    if (elements.analysisProgressBar) elements.analysisProgressBar.style.width = "100%";
  }

  async function runBackendAnalysis() {
    if (!state.videoFile) {
      showUploadHint("请先点击这里上传视频，再开始分析");
      return;
    }

    state.detecting = true;
    setConnected(true);
    elements.btnStart.classList.add("btn-secondary");
    elements.btnStart.classList.remove("btn-primary");
    elements.btnStart.textContent = "分析中...";
    showUploadHint("正在调用后端分析，生成标注视频...");

    const startedAt = performance.now();
    startAnalysisTimer(startedAt);
    const form = new FormData();
    form.append("video", state.videoFile);
    form.append("config", JSON.stringify(buildAnalyzeConfig()));

    try {
      await ensureBackendReady();
      const response = await fetch(apiUrl("/api/analyze"), {
        method: "POST",
        body: form,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let finalReport = null;
      let sseError = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop();
        for (const chunk of events) {
          const lines = chunk.split("\n");
          let eventName = "message";
          let dataStr = "";
          for (const line of lines) {
            if (line.startsWith("event:")) eventName = line.slice(6).trim();
            else if (line.startsWith("data:")) dataStr += line.slice(5).trim();
          }
          if (!dataStr || dataStr === "[DONE]") continue;
          try {
            const data = JSON.parse(dataStr);
            if (eventName === "progress") {
              updateAnalysisProgress(data.percent, data.message);
            } else if (eventName === "result") {
              finalReport = data;
            } else if (eventName === "error") {
              sseError = data.message || "分析失败";
            } else if (eventName === "start") {
              updateAnalysisProgress(3, data.message || "开始分析...");
            }
          } catch (e) {
            // ignore parse errors for heartbeat etc.
          }
        }
      }

      if (sseError) throw new Error(sseError);
      if (!finalReport) throw new Error("未收到分析结果");

      const elapsedMs = performance.now() - startedAt;
      state.analysisReport = finalReport;
      stopAnalysisTimer("分析完成，已生成训练结果", elapsedMs);
      renderBackendReport(finalReport, elapsedMs);
      loadHistoryList();
      updateCoachContextStatus();
    } catch (error) {
      setConnected(false);
      stopAnalysisTimer("分析失败，请检查后端服务或视频格式");
      showUploadHint(`分析失败：${formatFetchError(error)}`);
    } finally {
      state.detecting = false;
      elements.btnStart.classList.remove("btn-secondary");
      elements.btnStart.classList.add("btn-primary");
      elements.btnStart.textContent = "开始检测";
    }
  }

  async function ensureBackendReady() {
    try {
      const response = await fetch(apiUrl("/api/health"), { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`后端健康检查失败：HTTP ${response.status}`);
      }
    } catch (error) {
      throw new Error(`无法连接后端 ${API_BASE}，请确认 uvicorn 正在运行，并通过 http://127.0.0.1:8000/frontend/ 打开页面`);
    }
  }

  function formatFetchError(error) {
    if (!error || !error.message) return "未知网络错误";
    if (error.message === "Failed to fetch") {
      return `无法连接后端 ${API_BASE}。请确认页面地址是 http://127.0.0.1:8000/frontend/，并查看 PowerShell 是否有 /api/analyze 请求日志。`;
    }
    return error.message;
  }

  function renderBackendReport(report, elapsedMs) {
    const annotatedUrl = report.annotated_video_url || report.raw_annotated_video_url;
    const previewUrl = report.annotated_preview_url
      ? `${report.annotated_preview_url}${report.annotated_preview_url.includes("?") ? "&" : "?"}t=${Date.now()}`
      : null;
    const videoUrl = annotatedUrl
      ? `${annotatedUrl}${annotatedUrl.includes("?") ? "&" : "?"}t=${Date.now()}`
      : null;

    const videoWarning = report.video_warning || null;
    if (videoUrl && elements.analysisVideo) {
      setupVideoActions(videoUrl, videoWarning);
      showAnalysisVideo(videoUrl, previewUrl, videoWarning);
    } else if (previewUrl) {
      showGeneratedPoster(previewUrl, videoWarning || "标注预览图已生成，视频文件暂未返回。");
    }

    state.fps = 0;
    state.detections = Number(report.hit_count || 0);
    state.latency = Math.max(1, Math.round(elapsedMs));
    state.avgConf = Number((Number(report.confidence || 0) * 100).toFixed(1));
    state.footworkTrace = Array.isArray(report.footwork_trace) ? report.footwork_trace : [];
    state.shotEvents = normalizeShotEvents(report.shot_events || report.report?.shot_events || []);
    state.playbackDuration = Number(report.video_metadata?.duration_sec || 0);
    renderShotTimeline();
    updatePlaybackMetrics(0, false);

    elements.actionType.textContent = report.predicted_action || "--";
    const confidencePercent = report.confidence == null ? null : Math.round(Number(report.confidence) * 100);

    const scores = report.footwork_scores || {};
    const scoreOf = (...keys) => {
      for (const key of keys) {
        const value = Number(scores[key]);
        if (Number.isFinite(value)) return Math.max(0, Math.min(100, value));
      }
      return 0;
    };
    const movement = scoreOf("移动量", "movement");
    const explosiveness = scoreOf("启动爆发", "explosiveness");
    const stability = scoreOf("重心稳定", "stability");
    const recovery = scoreOf("回位能力", "recovery");
    const coverage = scoreOf("覆盖范围", "coverage");
    const balance = scoreOf("步幅平衡", "balance");
    const coordination = scoreOf("身体协调", "coordination") || Math.max(0, Math.min(100, stability * 0.4 + balance * 0.35 + recovery * 0.25));
    const confidenceScore = report.confidence == null ? 0 : Math.max(0, Math.min(100, Number(report.confidence) * 100));
    const smoothness = Math.max(0, Math.min(100, recovery * 0.35 + balance * 0.35 + coverage * 0.3));
    const values = [
      smoothness,
      confidenceScore,
      coordination,
      movement,
      explosiveness,
      stability,
    ];
    const qualitySummary = report.quality_summary || {};
    const fallbackOverall = Math.max(0, Math.min(100, values.reduce((sum, value) => sum + value, 0) / Math.max(values.length, 1)));
    const overallScore = Number.isFinite(Number(qualitySummary.overall_score))
      ? Number(qualitySummary.overall_score)
      : fallbackOverall;
    const avgQualityScore = Number.isFinite(Number(qualitySummary.avg_quality_score))
      ? Number(qualitySummary.avg_quality_score)
      : overallScore;
    const scoreSource = Number.isFinite(Number(qualitySummary.overall_score))
      ? `质量分 ${Number(overallScore).toFixed(1)}`
      : `综合估算 ${Number(overallScore).toFixed(1)}`;

    elements.actionScore.textContent = Math.round(overallScore);
    elements.powerLevel.textContent = confidencePercent == null ? scoreSource : `${scoreSource} · 识别置信度 ${confidencePercent}%`;

    [
      [elements.qualitySmooth, elements.barSmooth, values[0]],
      [elements.qualityAccuracy, elements.barAccuracy, values[1]],
      [elements.qualityCoord, elements.barCoord, values[2]],
      [elements.qualityFoot, elements.barFoot, values[3]],
      [elements.qualityWrist, elements.barWrist, values[4]],
      [elements.qualityBalance, elements.barBalance, values[5]],
    ].forEach(([label, bar, value]) => {
      label.textContent = value.toFixed(1);
      bar.style.width = `${value}%`;
    });
    state.radarData = values;
    drawRadar(state.radarData);

    const historyRows = (report.shot_events || [])
      .slice(0, 20)
      .map((event, index) => {
        const time = Number(event.time_sec ?? event.time ?? 0);
        const action = event.shot_action || event.action || event.predicted_action || "击球片段";
        const confidence = Number(event.shot_confidence ?? event.confidence ?? 0);
        const quality = Number(event.quality_score);
        const qualityText = Number.isFinite(quality) ? quality.toFixed(1) : "--";
        return `<tr><td>${time > 0 ? `${time.toFixed(1)}s` : index + 1}</td><td>${action}</td><td>${(confidence * 100).toFixed(1)}%</td><td>${qualityText}</td><td>${event.quality_level || "--"}</td></tr>`;
      });
    elements.historyTable.innerHTML = historyRows.join("") || '<tr><td colspan="5" style="text-align:center; color:var(--muted); padding:32px;">暂无逐拍检测记录</td></tr>';

    const coach = report.coach_report || {};
    elements.totalSessions.textContent = "1";
    elements.avgScore.textContent = Math.round(avgQualityScore);
    elements.bestAction.textContent = report.predicted_action || "--";
    elements.totalFrames.textContent = report.report?.motion_summary?.valid_frames || "--";
    elements.reportDate.textContent = new Date().toLocaleString();
    elements.reportDuration.textContent = formatDuration(report.video_metadata?.duration_sec);
    elements.reportActions.textContent = `${report.hit_count || 0} 次`;
    elements.reportHighlights.textContent = buildHighlightText(report, coach);
    elements.reportIssues.textContent = buildIssueText(report, coach);
    elements.reportSuggestions.textContent = buildSuggestionText(report, coach);
    elements.reportPlan.textContent = buildPlanText(report, coach);
    elements.reportReview.textContent = buildReviewText(report);
    drawCourt(values, state.footworkTrace, 1);
    updateCoachContextStatus();
  }

  function setupVideoActions(videoUrl) {
    if (!elements.videoActions) return;
    elements.videoActions.hidden = false;
    elements.videoStatusText.textContent = "标注视频已生成，可在页面中播放。";
    elements.downloadVideoLink.href = videoUrl;
  }

  function showAnalysisVideo(videoUrl, previewUrl = null) {
    let settled = false;
    const markPlayable = () => {
      settled = true;
      elements.videoStatusText.textContent = "标注视频已生成，可播放或下载。";
    };
    const markProblem = () => {
      elements.videoStatusText.textContent = "浏览器未能播放当前视频，请下载视频查看，或重新分析生成新视频。";
      if (previewUrl) {
        showGeneratedPoster(previewUrl, "浏览器未能播放标注视频，已切换为预览图。可下载视频查看。");
      }
    };

    elements.analysisVideo.onloadeddata = markPlayable;
    elements.analysisVideo.oncanplay = markPlayable;
    elements.analysisVideo.onerror = markProblem;
    elements.analysisVideo.onstalled = markProblem;
    elements.analysisVideo.ontimeupdate = () => {
      updatePlaybackMetrics(elements.analysisVideo.currentTime || 0, true);
    };
    elements.analysisVideo.onloadedmetadata = () => {
      if (!state.playbackDuration && Number.isFinite(elements.analysisVideo.duration)) {
        state.playbackDuration = elements.analysisVideo.duration;
      }
      updatePlaybackMetrics(elements.analysisVideo.currentTime || 0, true);
    };
    elements.frameCanvas.hidden = true;
    elements.analysisVideo.pause();
    elements.analysisVideo.removeAttribute("src");
    elements.analysisVideo.load();
    elements.analysisVideo.src = videoUrl;
    if (previewUrl) {
      elements.analysisVideo.poster = previewUrl;
    } else {
      elements.analysisVideo.removeAttribute("poster");
    }
    elements.analysisVideo.hidden = false;
    elements.frameCanvasWrap.style.display = "block";
    elements.emptyMedia.style.display = "none";
    elements.analysisVideo.load();
    window.setTimeout(() => {
      if (!settled && elements.analysisVideo && !elements.analysisVideo.hidden) {
        markProblem();
      }
    }, 4500);
  }

  function formatDuration(durationSec) {
    const seconds = Number(durationSec || 0);
    if (!Number.isFinite(seconds) || seconds <= 0) return "--";
    const minutes = Math.floor(seconds / 60);
    const remain = Math.round(seconds % 60);
    return minutes > 0 ? `${minutes} 分 ${remain} 秒` : `${remain} 秒`;
  }

  function showGeneratedPoster(previewUrl, message) {
    if (!previewUrl) return;
    const img = new Image();
    img.onload = () => {
      const sourceW = img.naturalWidth || 640;
      const sourceH = img.naturalHeight || 480;
      const targetW = 640;
      const targetH = Math.max(360, Math.round((targetW * sourceH) / sourceW));
      elements.frameCanvas.width = targetW;
      elements.frameCanvas.height = targetH;
      ctx.clearRect(0, 0, targetW, targetH);
      ctx.drawImage(img, 0, 0, targetW, targetH);
      state.frameImage = img;
      elements.frameCanvas.hidden = false;
      if (elements.analysisVideo) {
        stopCourtPlaybackLoop();
        elements.analysisVideo.pause();
        elements.analysisVideo.hidden = true;
      }
      elements.frameCanvasWrap.style.display = "block";
      elements.emptyMedia.style.display = "none";
      if (elements.videoStatusText && message) {
        elements.videoStatusText.textContent = message;
      }
    };
    img.src = previewUrl;
  }

  function setupVideoActions(videoUrl, warning = null) {
    if (!elements.videoActions) return;
    elements.videoActions.hidden = false;
    if (elements.videoStatusText) {
      elements.videoStatusText.textContent = warning || "标注视频已生成，正在准备页面播放。";
    }
    elements.downloadVideoLink.href = videoUrl;
  }

  function showAnalysisVideo(videoUrl, previewUrl = null, warning = null) {
    const video = elements.analysisVideo;
    const status = elements.videoStatusText;
    if (!video) return;

    let settled = false;
    let fallbackShown = false;
    let triedBlobFallback = false;

    const mediaDebug = () => {
      const errorCode = video.error ? video.error.code : "none";
      return `readyState=${video.readyState}, networkState=${video.networkState}, error=${errorCode}`;
    };

    const setStatus = (text) => {
      if (status) status.textContent = text;
    };

    const markPlayable = () => {
      settled = true;
      fallbackShown = false;
      setStatus("标注视频已生成，可在页面播放，也可以下载。");
    };

    const markWaiting = () => {
      if (settled || fallbackShown) return;
      setStatus("视频仍在加载，若长时间没有画面，可以先下载视频查看。");
    };

    const markProblem = (reason = "浏览器解码失败") => {
      if (fallbackShown) return;
      fallbackShown = true;
      const hint = warning || `${reason}，已保留下载入口。`;
      setStatus(`${hint} ${mediaDebug()}`);
      video.hidden = false;
      elements.frameCanvas.hidden = true;
    };

    const loadVideoBlobFallback = async () => {
      if (triedBlobFallback) return false;
      triedBlobFallback = true;
      try {
        setStatus("正在准备稳定播放源，请稍候...");
        const response = await fetch(videoUrl, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const blob = await response.blob();
        if (state.analysisVideoObjectUrl) {
          URL.revokeObjectURL(state.analysisVideoObjectUrl);
        }
        state.analysisVideoObjectUrl = URL.createObjectURL(new Blob([blob], { type: "video/mp4" }));
        video.pause();
        video.removeAttribute("src");
        video.load();
        video.src = state.analysisVideoObjectUrl;
        video.hidden = false;
        elements.frameCanvas.hidden = true;
        video.load();
        setStatus("稳定播放源已准备好，可直接播放，也可以下载视频。");
        return true;
      } catch (error) {
        setStatus(`稳定播放源准备失败，正在尝试后端直连播放。${error.message || error}`);
        return false;
      }
    };

    let sourceReadyForEvents = false;

    video.onloadedmetadata = () => {
      settled = true;
      if (!state.playbackDuration && Number.isFinite(video.duration)) {
        state.playbackDuration = video.duration;
      }
      updatePlaybackMetrics(video.currentTime || 0, true);
      setStatus("标注视频元数据已加载，点击播放即可查看。");
    };
    video.onloadeddata = markPlayable;
    video.oncanplay = markPlayable;
    video.onplay = startCourtPlaybackLoop;
    video.onplaying = () => {
      markPlayable();
      startCourtPlaybackLoop();
    };
    video.onpause = stopCourtPlaybackLoop;
    video.onended = stopCourtPlaybackLoop;
    video.onerror = async () => {
      if (!sourceReadyForEvents) return;
      const recovered = await loadVideoBlobFallback();
      if (!recovered) markProblem("浏览器无法解码当前标注视频");
    };
    video.onstalled = markWaiting;
    video.onwaiting = markWaiting;
    video.ontimeupdate = () => updatePlaybackMetrics(video.currentTime || 0, true);

    elements.frameCanvas.hidden = true;
    video.pause();
    video.preload = "auto";
    video.controls = true;
    video.removeAttribute("src");
    video.load();
    if (previewUrl) {
      video.poster = previewUrl;
    } else {
      video.removeAttribute("poster");
    }
    video.hidden = false;
    elements.frameCanvasWrap.style.display = "block";
    elements.emptyMedia.style.display = "none";
    setStatus("正在准备本地缓存播放源...");
    loadVideoBlobFallback().then((loaded) => {
      if (loaded) {
        sourceReadyForEvents = true;
        return;
      }
      video.pause();
      video.removeAttribute("src");
      video.load();
      video.src = videoUrl;
      sourceReadyForEvents = true;
      video.load();
    });

    window.setTimeout(() => {
      if (!settled && video && !video.hidden) {
        if (video.networkState === HTMLMediaElement.NETWORK_NO_SOURCE || video.error) {
          markProblem("浏览器没有拿到可播放的视频源");
        } else {
          markWaiting();
        }
      }
    }, 12000);
  }

  function showGeneratedPoster(previewUrl, message) {
    if (!previewUrl) return;
    const img = new Image();
    img.onload = () => {
      const sourceW = img.naturalWidth || 640;
      const sourceH = img.naturalHeight || 480;
      const targetW = 640;
      const targetH = Math.max(360, Math.round((targetW * sourceH) / sourceW));
      elements.frameCanvas.width = targetW;
      elements.frameCanvas.height = targetH;
      ctx.clearRect(0, 0, targetW, targetH);
      ctx.drawImage(img, 0, 0, targetW, targetH);
      state.frameImage = img;
      elements.frameCanvas.hidden = false;
      if (elements.analysisVideo) {
        elements.analysisVideo.pause();
        elements.analysisVideo.hidden = true;
      }
      elements.frameCanvasWrap.style.display = "block";
      elements.emptyMedia.style.display = "none";
      if (elements.videoStatusText && message) {
        elements.videoStatusText.textContent = message;
      }
    };
    img.onerror = () => {
      if (elements.videoStatusText) {
        elements.videoStatusText.textContent = "标注视频已生成，但页面预览图加载失败；请点击下载视频查看。";
      }
      if (elements.videoActions) {
        elements.videoActions.hidden = false;
      }
    };
    img.src = previewUrl;
  }

  function cleanCoachText(text) {
    return String(text || "")
      .replace(/#{1,6}\s*/g, "")
      .replace(/\*\*/g, "")
      .replace(/`+/g, "")
      .replace(/你好[，,！!。]?\s*我是[^。！!\n]*[。！!]?\s*/g, "")
      .replace(/作为[^，,。]*AI[^，,。]*[，,。]\s*/g, "")
      .replace(/根据本次训练的视觉模型数据和分段复盘[，,。]\s*/g, "")
      .replace(/\n{2,}/g, "\n")
      .trim();
  }

  function firstUsefulSentence(text, fallback = "--") {
    const cleaned = cleanCoachText(text);
    if (!cleaned) return fallback;
    const sentences = cleaned
      .split(/[。！？\n]/)
      .map((item) => item.trim())
      .filter(Boolean)
      .filter((item) => !/^(本次训练|训练报告|总体概览|概览|建议|重点问题)[:：]?$/.test(item));
    return sentences[0] ? `${sentences[0]}。` : fallback;
  }

  function buildHighlightText(report, coach) {
    const action = report.predicted_action || "主要动作";
    const confidence = report.confidence == null ? null : Math.round(Number(report.confidence) * 100);
    const hitCount = Number(report.hit_count || 0);
    const localHighlight = [
      `${action}${confidence == null ? "" : ` 置信度约 ${confidence}%`}，本次共识别 ${hitCount} 个疑似击球片段`,
      `姿态检测率约 ${Math.round(Number(report.detection_rate || 0) * 100)}%，可作为本次复盘的数据可靠性参考`,
    ];
    if (report.llm_coach_report) {
      const llmLine = firstUsefulSentence(report.llm_coach_report, "");
      return normalizeList([llmLine, ...(coach.highlights || [])], localHighlight, 4);
    }
    return normalizeList(coach.highlights || [], localHighlight, 4);
  }

  function buildSuggestionText(report, coach) {
    const fallback = [
      "优先复看低置信片段，确认动作类别是否被相近动作混淆",
      "结合标注视频检查击球后回位、重心稳定和手腕发力节奏",
      "若视频中多人交叉或远近切换明显，下一次建议先截取更清晰的单人训练片段",
    ];
    return normalizeList([...(coach.focus || []), ...(coach.training_plan || [])], fallback, 4);
  }

  function normalizeList(items, fallbackItems, limit = 4) {
    const source = Array.isArray(items) && items.length ? items : fallbackItems;
    return source
      .map((item) => cleanCoachText(item))
      .filter(Boolean)
      .slice(0, limit)
      .map((item, index) => `${index + 1}. ${item.replace(/[。；;]$/, "")}`)
      .join("\n");
  }

  function buildIssueText(report, coach) {
    const lowConfidence = Number(report.low_confidence_shots || 0);
    const fallback = [
      lowConfidence > 0
        ? `有 ${lowConfidence} 个低置信击球片段，建议优先人工复核`
        : "当前主要风险在于姿态跟踪稳定性，需要结合标注视频确认",
      "重点观察击球后回位速度、重心稳定和连续移动后的步幅一致性",
    ];
    return normalizeList(coach.focus || [], fallback, 4);
  }

  function buildPlanText(report, coach) {
    const fallback = [
      "进行 3 组启动步 + 回位训练，每组 30 秒，关注击球后第一步是否及时",
      "选择 3-5 个低置信片段慢放复盘，检查击球点高度、挥拍路线和身体重心",
      "下一次拍摄保持固定机位，并尽量让目标球员完整进入画面",
    ];
    return normalizeList(coach.training_plan || [], fallback, 4);
  }

  function buildReviewText(report) {
    const top = (report.top_predictions || [])
      .slice(0, 3)
      .map(([action, confidence]) => `${action} ${Math.round(Number(confidence || 0) * 100)}%`)
      .join(" / ");
    const fallback = [
      top ? `Top 动作分布：${top}` : "复核 Top 动作分布，确认是否与实际训练内容一致",
      "若标注视频中出现跟踪跳人，下一次请优先使用清晰单人片段或缩短视频时长",
      "报告建议用于训练参考，关键动作仍建议结合慢放视频人工确认",
    ];
    return normalizeList([], fallback, 4);
  }

  function cleanTrace(trace) {
    const cleaned = [];
    let previous = null;
    (trace || []).forEach((point) => {
      const t = point && Number.isFinite(Number(point.time_sec)) ? Number(point.time_sec) : null;
      const current = {
        x: Number.isFinite(Number(point.x)) ? Number(point.x) : 0.5,
        y: Number.isFinite(Number(point.y)) ? Number(point.y) : 0.5,
        time_sec: t,
      };
      if (previous) {
        const jump = Math.hypot(current.x - previous.x, current.y - previous.y);
        if (jump > 0.16) return;
      }
      cleaned.push(current);
      previous = current;
    });
    if (cleaned.length < 5) return cleaned;
    return cleaned.map((pt, index) => {
      if (index < 2 || index > cleaned.length - 3) return pt;
      const window = cleaned.slice(index - 2, index + 3);
      return {
        x: window.reduce((sum, item) => sum + item.x, 0) / window.length,
        y: window.reduce((sum, item) => sum + item.y, 0) / window.length,
        time_sec: pt.time_sec,
      };
    });
  }

  function smoothCourtPoints(points, passes = 2) {
    if (!points || points.length < 3) return points || [];
    let smoothed = points.map((point) => ({ ...point }));
    for (let pass = 0; pass < passes; pass += 1) {
      smoothed = smoothed.map((point, index, list) => {
        if (index === 0 || index === list.length - 1) return point;
        const prev = list[index - 1];
        const next = list[index + 1];
        return {
          x: point.x * 0.5 + (prev.x + next.x) * 0.25,
          y: point.y * 0.5 + (prev.y + next.y) * 0.25,
        };
      });
    }
    return smoothed;
  }

  function densifyCourtPoints(points, maxDistance = 8) {
    if (!points || points.length < 2) return points || [];
    const dense = [points[0]];
    for (let index = 1; index < points.length; index += 1) {
      const prev = points[index - 1];
      const next = points[index];
      const distance = Math.hypot(next.x - prev.x, next.y - prev.y);
      const steps = Math.max(1, Math.ceil(distance / maxDistance));
      for (let step = 1; step <= steps; step += 1) {
        const t = step / steps;
        dense.push({
          x: prev.x + (next.x - prev.x) * t,
          y: prev.y + (next.y - prev.y) * t,
        });
      }
    }
    return dense;
  }

  function traceSmoothPath(ctx, points) {
    if (!points || points.length < 2) return;
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let index = 1; index < points.length - 1; index += 1) {
      const midpoint = {
        x: (points[index].x + points[index + 1].x) / 2,
        y: (points[index].y + points[index + 1].y) / 2,
      };
      ctx.quadraticCurveTo(points[index].x, points[index].y, midpoint.x, midpoint.y);
    }
    const last = points[points.length - 1];
    ctx.lineTo(last.x, last.y);
  }

  function drawFootworkTrail(ctx, points) {
    if (!points || points.length < 2) return;
    ctx.save();
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    ctx.shadowColor = "rgba(94, 255, 159, 0.24)";
    ctx.shadowBlur = 10;
    ctx.strokeStyle = "rgba(94, 255, 159, 0.16)";
    ctx.lineWidth = 7;
    traceSmoothPath(ctx, points);
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.strokeStyle = "rgba(232, 255, 244, 0.72)";
    ctx.lineWidth = 2.2;
    traceSmoothPath(ctx, points);
    ctx.stroke();

    const tail = Math.min(points.length - 1, 28);
    for (let index = 1; index <= tail; index += 1) {
      const point = points[points.length - index];
      const alpha = 0.08 + (1 - index / tail) * 0.18;
      ctx.fillStyle = `rgba(232, 255, 244, ${alpha})`;
      ctx.beginPath();
      ctx.arc(point.x, point.y, 2.2, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  function findTraceIndexByTime(trace, targetTime) {
    if (!trace || trace.length === 0) return 0;
    if (trace.length === 1) return 0;
    const t0 = trace[0].time_sec;
    const tN = trace[trace.length - 1].time_sec;
    const hasTime = t0 != null && Number.isFinite(t0) && tN != null && Number.isFinite(tN) && tN > t0;
    if (!hasTime) return -1;
    if (targetTime <= t0) return 0;
    if (targetTime >= tN) return trace.length - 1;
    let lo = 0, hi = trace.length - 1;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      const mt = trace[mid].time_sec;
      if (mt == null || !Number.isFinite(mt) || mt < targetTime) lo = mid + 1;
      else hi = mid;
    }
    return lo;
  }

  function drawCourt(values = null, trace = state.footworkTrace, progressRatio = 1, currentTime = null) {
    const canvas = elements.courtCanvas;
    const w = canvas.width;
    const h = canvas.height;
    courtCtx.clearRect(0, 0, w, h);

    // Background
    courtCtx.fillStyle = "#0a1f16";
    courtCtx.fillRect(0, 0, w, h);

    // Standard badminton half-court (doubles): 6.10m wide x 6.70m deep (net to baseline)
    // We draw with equal margins on sides, smaller margin top/bottom for labels
    const padX = 28;
    const padTop = 36;
    const padBottom = 28;
    const availW = w - padX * 2;
    const availH = h - padTop - padBottom;
    const courtAspect = 6.10 / 6.70;
    let courtW, courtH;
    if (availW / availH > courtAspect) {
      courtH = availH;
      courtW = courtH * courtAspect;
    } else {
      courtW = availW;
      courtH = courtW / courtAspect;
    }
    const left = padX + (availW - courtW) / 2;
    const top = padTop + (availH - courtH) / 2;
    const right = left + courtW;
    const bottom = top + courtH;

    // Standard court line ratios (relative to half-court, 0=net, 1=baseline)
    const R_SHORT_SERVICE = 1.98 / 6.70;
    const R_SINGLES_SIDE = 0.46 / 6.10;
    const yShort = top + courtH * R_SHORT_SERVICE;
    const xSinglesL = left + courtW * R_SINGLES_SIDE;
    const xSinglesR = right - courtW * R_SINGLES_SIDE;
    const xCenter = left + courtW * 0.5;

    // Doubles outer boundary
    courtCtx.strokeStyle = "#2a6e52";
    courtCtx.lineWidth = 2;
    courtCtx.strokeRect(left, top, courtW, courtH);

    // Singles sidelines
    courtCtx.strokeStyle = "#254b3e";
    courtCtx.lineWidth = 1.2;
    courtCtx.beginPath();
    courtCtx.moveTo(xSinglesL, top);
    courtCtx.lineTo(xSinglesL, bottom);
    courtCtx.stroke();
    courtCtx.beginPath();
    courtCtx.moveTo(xSinglesR, top);
    courtCtx.lineTo(xSinglesR, bottom);
    courtCtx.stroke();

    // Short service line
    courtCtx.beginPath();
    courtCtx.moveTo(left, yShort);
    courtCtx.lineTo(right, yShort);
    courtCtx.stroke();

    // Center line (from short service line to baseline)
    courtCtx.beginPath();
    courtCtx.moveTo(xCenter, yShort);
    courtCtx.lineTo(xCenter, bottom);
    courtCtx.stroke();

    // Net (top boundary, dashed green)
    courtCtx.strokeStyle = "#5eff9f";
    courtCtx.setLineDash([6, 4]);
    courtCtx.lineWidth = 2;
    courtCtx.beginPath();
    courtCtx.moveTo(left, top);
    courtCtx.lineTo(right, top);
    courtCtx.stroke();
    courtCtx.setLineDash([]);

    // Baseline label area
    courtCtx.strokeStyle = "rgba(94,255,159,0.2)";
    courtCtx.lineWidth = 1;
    courtCtx.setLineDash([3, 3]);
    courtCtx.beginPath();
    courtCtx.moveTo(left, bottom);
    courtCtx.lineTo(right, bottom);
    courtCtx.stroke();
    courtCtx.setLineDash([]);

    // Zone labels
    courtCtx.fillStyle = "rgba(168,201,187,0.45)";
    courtCtx.font = "10px JetBrains Mono, monospace";
    courtCtx.textAlign = "center";
    courtCtx.fillText("NET", xCenter, top - 8);
    courtCtx.textAlign = "center";
    courtCtx.fillText("BASELINE", xCenter, bottom + 14);
    courtCtx.save();
    courtCtx.fillStyle = "rgba(168,201,187,0.3)";
    courtCtx.font = "9px JetBrains Mono, monospace";
    courtCtx.fillText("FRONT", xCenter, top + courtH * 0.15);
    courtCtx.fillText("MID", xCenter, top + courtH * (R_SHORT_SERVICE + (1 - R_SHORT_SERVICE) * 0.35));
    courtCtx.fillText("BACK", xCenter, top + courtH * (R_SHORT_SERVICE + (1 - R_SHORT_SERVICE) * 0.8));
    courtCtx.restore();

    // Title / footer
    courtCtx.fillStyle = "#a8c9bb";
    courtCtx.font = "12px JetBrains Mono, monospace";
    courtCtx.textAlign = "center";
    courtCtx.fillText("目标球员半场步伐热区", w / 2, h - 8);

    if (!trace || trace.length < 2) {
      courtCtx.fillStyle = "rgba(168, 201, 187, 0.78)";
      courtCtx.font = "13px Microsoft YaHei, sans-serif";
      courtCtx.fillText("分析完成后显示目标球员步伐热力分布", w / 2, h / 2);
      return;
    }

    const cleanedTrace = cleanTrace(trace);
    if (cleanedTrace.length < 2) return;

    let baseIndex;
    let fraction = 0;
    const t = Number.isFinite(Number(currentTime)) ? Number(currentTime) : null;
    if (t != null) {
      const idx = findTraceIndexByTime(cleanedTrace, t);
      if (idx >= 0) {
        if (idx === 0) {
          baseIndex = 0;
          fraction = 0;
        } else if (idx >= cleanedTrace.length - 1) {
          baseIndex = cleanedTrace.length - 2;
          const prev = cleanedTrace[baseIndex];
          const curr = cleanedTrace[baseIndex + 1];
          const dt = (curr.time_sec - prev.time_sec) || 1;
          fraction = Math.max(0, Math.min(1, (t - prev.time_sec) / dt));
        } else {
          const prev = cleanedTrace[idx - 1];
          const curr = cleanedTrace[idx];
          if (curr.time_sec > t && prev.time_sec <= t) {
            baseIndex = idx - 1;
            const dt = (curr.time_sec - prev.time_sec) || 1;
            fraction = Math.max(0, Math.min(1, (t - prev.time_sec) / dt));
          } else {
            baseIndex = idx;
            fraction = 0;
          }
        }
      } else {
        const safeProgress = Math.max(0.02, Math.min(1, Number(progressRatio || 1)));
        const exactIndex = Math.max(1, (cleanedTrace.length - 1) * safeProgress);
        baseIndex = Math.max(1, Math.min(cleanedTrace.length - 1, Math.floor(exactIndex)));
        fraction = Math.max(0, Math.min(1, exactIndex - baseIndex));
      }
    } else {
      const safeProgress = Math.max(0.02, Math.min(1, Number(progressRatio || 1)));
      const exactIndex = Math.max(1, (cleanedTrace.length - 1) * safeProgress);
      baseIndex = Math.max(1, Math.min(cleanedTrace.length - 1, Math.floor(exactIndex)));
      fraction = Math.max(0, Math.min(1, exactIndex - baseIndex));
    }

    const visible = cleanedTrace.slice(0, baseIndex + 1);
    if (fraction > 0 && cleanedTrace[baseIndex + 1]) {
      const from = cleanedTrace[baseIndex];
      const to = cleanedTrace[baseIndex + 1];
      visible.push({
        x: from.x + (to.x - from.x) * fraction,
        y: from.y + (to.y - from.y) * fraction,
      });
    }
    const points = visible.map((point) => {
      const nx = Number.isFinite(Number(point.x)) ? Number(point.x) : 0.5;
      const ny = Number.isFinite(Number(point.y)) ? Number(point.y) : 0.5;
      return {
        x: left + (0.08 + nx * 0.84) * courtW,
        y: top + (0.06 + ny * 0.88) * courtH,
      };
    });

    // Heat layer
    const heatCols = 14;
    const heatRows = 16;
    const heat = new Array(heatCols * heatRows).fill(0);
    points.forEach((point) => {
      const gx = Math.max(0, Math.min(heatCols - 1, Math.round(((point.x - left) / courtW) * (heatCols - 1))));
      const gy = Math.max(0, Math.min(heatRows - 1, Math.round(((point.y - top) / courtH) * (heatRows - 1))));
      for (let yy = -1; yy <= 1; yy += 1) {
        for (let xx = -1; xx <= 1; xx += 1) {
          const nx = gx + xx;
          const ny = gy + yy;
          if (nx < 0 || nx >= heatCols || ny < 0 || ny >= heatRows) continue;
          heat[ny * heatCols + nx] += xx === 0 && yy === 0 ? 3 : 1;
        }
      }
    });
    const maxHeat = Math.max(1, ...heat);
    for (let gy = 0; gy < heatRows; gy += 1) {
      for (let gx = 0; gx < heatCols; gx += 1) {
        const value = heat[gy * heatCols + gx] / maxHeat;
        if (value <= 0.04) continue;
        const cellW = courtW / heatCols;
        const cellH = courtH / heatRows;
        const cellX = left + gx * cellW;
        const cellY = top + gy * cellH;
        const alpha = 0.08 + value * 0.46;
        const hue = 155 - value * 105;
        courtCtx.fillStyle = `hsla(${hue}, 95%, ${48 + value * 12}%, ${alpha})`;
        const rx = cellX - cellW * 0.12;
        const ry = cellY - cellH * 0.12;
        const rw = cellW * 1.24;
        const rh = cellH * 1.24;
        courtCtx.beginPath();
        if (typeof courtCtx.roundRect === "function") {
          courtCtx.roundRect(rx, ry, rw, rh, 10);
        } else {
          courtCtx.rect(rx, ry, rw, rh);
        }
        courtCtx.fill();
      }
    }

    // Recent trajectory only, smoothed and interpolated for a stable playback trail.
    const recent = densifyCourtPoints(smoothCourtPoints(points.slice(-90), 3), 7);
    drawFootworkTrail(courtCtx, recent);

    const current = recent[recent.length - 1] || points[points.length - 1];
    if (current) {
      const pulse = 10 + Math.sin(Date.now() / 180) * 2;
      courtCtx.fillStyle = "rgba(255, 223, 112, 0.20)";
      courtCtx.beginPath();
      courtCtx.arc(current.x, current.y, pulse, 0, Math.PI * 2);
      courtCtx.fill();
      courtCtx.fillStyle = "#ffdf70";
      courtCtx.beginPath();
      courtCtx.arc(current.x, current.y, 6, 0, Math.PI * 2);
      courtCtx.fill();
    }

    const movement = values?.[0] || 0;
    const recovery = values?.[3] || 0;
    const coverage = values?.[4] || 0;
    const summary = `热区 ${points.length} 点 · 覆盖 ${coverage.toFixed(0)} · 移动 ${movement.toFixed(0)} · 回位 ${recovery.toFixed(0)}`;
    courtCtx.fillStyle = "#d9f7e8";
    courtCtx.font = "13px Microsoft YaHei, sans-serif";
    courtCtx.textAlign = "center";
    courtCtx.fillText(summary, w / 2, 20);
  }

  function drawRadar(data) {
    const canvas = elements.radarCanvas;
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const r = Math.min(cx, cy) - 30;

    radarCtx.clearRect(0, 0, w, h);

    // Background
    radarCtx.fillStyle = "#0a1f16";
    radarCtx.fillRect(0, 0, w, h);

    const labels = ["挥拍流畅", "击球精准", "身体协调", "步法移动", "手腕发力", "重心稳定"];
    const n = labels.length;

    // Grid rings
    for (let ring = 1; ring <= 5; ring++) {
      const ringR = (r / 5) * ring;
      radarCtx.beginPath();
      for (let i = 0; i <= n; i++) {
        const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
        const x = cx + Math.cos(angle) * ringR;
        const y = cy + Math.sin(angle) * ringR;
        if (i === 0) radarCtx.moveTo(x, y);
        else radarCtx.lineTo(x, y);
      }
      radarCtx.strokeStyle = "rgba(37, 75, 62, 0.6)";
      radarCtx.lineWidth = 1;
      radarCtx.stroke();
    }

    // Axis lines
    for (let i = 0; i < n; i++) {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      radarCtx.beginPath();
      radarCtx.moveTo(cx, cy);
      radarCtx.lineTo(cx + Math.cos(angle) * r, cy + Math.sin(angle) * r);
      radarCtx.strokeStyle = "rgba(37, 75, 62, 0.5)";
      radarCtx.lineWidth = 1;
      radarCtx.stroke();
    }

    // Data polygon
    radarCtx.beginPath();
    for (let i = 0; i <= n; i++) {
      const idx = i % n;
      const angle = (Math.PI * 2 * idx) / n - Math.PI / 2;
      const val = (data[idx] || 0) / 100;
      const x = cx + Math.cos(angle) * r * val;
      const y = cy + Math.sin(angle) * r * val;
      if (i === 0) radarCtx.moveTo(x, y);
      else radarCtx.lineTo(x, y);
    }
    radarCtx.fillStyle = "rgba(94, 255, 159, 0.18)";
    radarCtx.fill();
    radarCtx.strokeStyle = "#5eff9f";
    radarCtx.lineWidth = 2;
    radarCtx.stroke();

    // Data points
    for (let i = 0; i < n; i++) {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const val = (data[i] || 0) / 100;
      const x = cx + Math.cos(angle) * r * val;
      const y = cy + Math.sin(angle) * r * val;
      radarCtx.beginPath();
      radarCtx.arc(x, y, 4, 0, Math.PI * 2);
      radarCtx.fillStyle = "#5eff9f";
      radarCtx.fill();
    }

    // Labels
    radarCtx.fillStyle = "#a8c9bb";
    radarCtx.font = "11px JetBrains Mono, monospace";
    radarCtx.textAlign = "center";
    radarCtx.textBaseline = "middle";
    for (let i = 0; i < n; i++) {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const lx = cx + Math.cos(angle) * (r + 20);
      const ly = cy + Math.sin(angle) * (r + 20);
      radarCtx.fillText(labels[i], lx, ly);
    }
  }

  // ---- Update UI Helpers ----
  function normalizeShotEvents(events) {
    return (events || [])
      .map((event, index) => ({
        index: Number(event.index || index + 1),
        time: Number(event.time_sec ?? event.time ?? 0),
        frame: Number(event.frame ?? 0),
        action: event.shot_action || event.action || event.predicted_action || "击球片段",
        confidence: Number(event.shot_confidence ?? event.confidence ?? 0),
        quality: Number(event.quality_score),
        qualityLevel: event.quality_level || "",
      }))
      .filter((event) => Number.isFinite(event.time))
      .sort((a, b) => a.time - b.time);
  }

  function timelineEventClass(event) {
    const quality = Number(event.quality);
    const confidence = Number(event.confidence || 0) * 100;
    const score = Number.isFinite(quality) ? quality : confidence;
    if (score >= 75) return "is-good";
    if (score >= 50) return "is-mid";
    return "is-low";
  }

  function seekToShot(event) {
    const video = elements.analysisVideo;
    const seekTime = Math.max(0, Number(event.time || 0) - 0.35);
    updatePlaybackMetrics(seekTime, true);
    document.querySelectorAll(".timeline-shot.active").forEach((node) => node.classList.remove("active"));
    const button = elements.shotTimeline?.querySelector(`[data-shot-index="${event.index}"]`);
    if (button) button.classList.add("active");
    if (!video || video.hidden) return;
    try {
      video.currentTime = seekTime;
      video.focus({ preventScroll: true });
    } catch (error) {
      console.warn("Unable to seek video", error);
    }
  }

  function renderShotTimeline() {
    const timeline = elements.shotTimeline;
    if (!timeline) return;
    timeline.querySelectorAll(".timeline-shot").forEach((node) => node.remove());

    const duration = state.playbackDuration || Number(state.analysisReport?.video_metadata?.duration_sec || 0);
    const events = state.shotEvents || [];
    if (!events.length) {
      if (elements.shotTimelineEmpty) elements.shotTimelineEmpty.hidden = false;
      if (elements.shotTimelineSummary) elements.shotTimelineSummary.textContent = "暂无逐拍事件";
      return;
    }

    if (elements.shotTimelineEmpty) elements.shotTimelineEmpty.hidden = true;
    if (elements.shotTimelineSummary) {
      const first = events[0]?.time || 0;
      const last = events[events.length - 1]?.time || 0;
      elements.shotTimelineSummary.textContent = `${events.length} 次击球 · ${formatClock(first)} - ${formatClock(last)}`;
    }

    events.forEach((event) => {
      const position = duration > 0
        ? Math.max(0, Math.min(100, (Number(event.time || 0) / duration) * 100))
        : Math.max(0, Math.min(100, (event.index / Math.max(events.length, 1)) * 100));
      const confidence = Number(event.confidence || 0) * 100;
      const quality = Number(event.quality);
      const scoreText = Number.isFinite(quality)
        ? `质量 ${quality.toFixed(1)}`
        : `置信 ${confidence.toFixed(1)}%`;

      const button = document.createElement("button");
      button.type = "button";
      button.className = `timeline-shot ${timelineEventClass(event)}`;
      button.style.left = `${position}%`;
      button.style.top = `${event.index % 2 === 0 ? 82 : 44}px`;
      button.dataset.shotIndex = String(event.index);
      button.title = `${formatClock(event.time)} · ${event.action} · ${scoreText}`;
      button.innerHTML = `
        <span class="shot-pin">${event.index}</span>
        <span class="shot-label">
          <b>${event.action}</b>
          <small>${formatClock(event.time)} · ${scoreText}</small>
        </span>
      `;
      button.addEventListener("click", () => seekToShot(event));
      timeline.appendChild(button);
    });
  }

  function formatClock(seconds) {
    const safe = Math.max(0, Number(seconds || 0));
    const minutes = Math.floor(safe / 60);
    const remain = Math.floor(safe % 60);
    return `${minutes}:${String(remain).padStart(2, "0")}`;
  }

  function stopCourtPlaybackLoop() {
    if (state.courtAnimationFrame) {
      window.cancelAnimationFrame(state.courtAnimationFrame);
      state.courtAnimationFrame = null;
    }
  }

  function startCourtPlaybackLoop() {
    stopCourtPlaybackLoop();
    const video = elements.analysisVideo;
    const tick = () => {
      if (!video || video.hidden || video.paused || video.ended) {
        stopCourtPlaybackLoop();
        return;
      }
      updatePlaybackMetrics(video.currentTime || 0, true);
      state.courtAnimationFrame = window.requestAnimationFrame(tick);
    };
    state.courtAnimationFrame = window.requestAnimationFrame(tick);
  }

  function updatePlaybackMetrics(currentTime = 0, animateCourt = false) {
    const duration = state.playbackDuration || Number(state.analysisReport?.video_metadata?.duration_sec || 0);
    const totalEvents = state.shotEvents.length || Number(state.analysisReport?.hit_count || 0);
    const passedEvents = state.shotEvents.filter((event) => event.time <= currentTime + 0.15);
    const currentEvent = [...passedEvents].reverse()[0] || state.shotEvents[0] || null;
    const progressRatio = duration > 0 ? Math.max(0, Math.min(1, currentTime / duration)) : 1;

    elements.metricFps.textContent = duration > 0
      ? `${formatClock(currentTime)} / ${formatClock(duration)}`
      : "总览";
    elements.metricDetections.textContent = `${passedEvents.length}/${totalEvents || 0}`;
    elements.metricConf.textContent = currentEvent && currentEvent.confidence
      ? `${(currentEvent.confidence * 100).toFixed(1)}%`
      : `${state.avgConf.toFixed(1)}%`;
    elements.metricLatency.textContent = currentEvent ? currentEvent.action : (state.analysisReport?.predicted_action || "--");

    if (elements.shotTimeline) {
      elements.shotTimeline.querySelectorAll(".timeline-shot.active").forEach((node) => node.classList.remove("active"));
      if (currentEvent) {
        const currentButton = elements.shotTimeline.querySelector(`[data-shot-index="${currentEvent.index}"]`);
        if (currentButton) currentButton.classList.add("active");
      }
    }

    if (animateCourt && state.footworkTrace.length) {
      drawCourt(state.radarData, state.footworkTrace, progressRatio, currentTime);
    }
  }

  function updateMetrics() {
    elements.metricFps.textContent = state.fps;
    elements.metricDetections.textContent = state.detections;
    elements.metricConf.textContent = state.avgConf.toFixed(1) + "%";
    elements.metricLatency.textContent = `${state.latency}ms`;
  }

  function updateAnalysis() {
    // Generate random scores for demo
    const scores = {
      smooth: 70 + Math.floor(Math.random() * 25),
      accuracy: 65 + Math.floor(Math.random() * 30),
      coord: 60 + Math.floor(Math.random() * 35),
      foot: 55 + Math.floor(Math.random() * 40),
      wrist: 65 + Math.floor(Math.random() * 30),
      balance: 70 + Math.floor(Math.random() * 25),
    };

    elements.qualitySmooth.textContent = scores.smooth;
    elements.qualityAccuracy.textContent = scores.accuracy;
    elements.qualityCoord.textContent = scores.coord;
    elements.qualityFoot.textContent = scores.foot;
    elements.qualityWrist.textContent = scores.wrist;
    elements.qualityBalance.textContent = scores.balance;

    elements.barSmooth.style.width = scores.smooth + "%";
    elements.barAccuracy.style.width = scores.accuracy + "%";
    elements.barCoord.style.width = scores.coord + "%";
    elements.barFoot.style.width = scores.foot + "%";
    elements.barWrist.style.width = scores.wrist + "%";
    elements.barBalance.style.width = scores.balance + "%";

    state.radarData = [
      scores.smooth,
      scores.accuracy,
      scores.coord,
      scores.foot,
      scores.wrist,
      scores.balance,
    ];
    drawRadar(state.radarData);

    const totalScore = Math.round(
      (scores.smooth + scores.accuracy + scores.coord + scores.foot + scores.wrist + scores.balance) / 6
    );
    elements.actionScore.textContent = totalScore;
    elements.actionType.textContent = "高远球";

    const powerLevels = ["弱", "中等", "强", "极强"];
    elements.powerLevel.textContent = powerLevels[Math.floor(Math.random() * powerLevels.length)];
  }

  function addHistoryEntry() {
    const actions = ["高远球", "杀球", "吊球", "网前挑球", "平抽球", "搓球"];
    const now = new Date();
    const timeStr = now.toLocaleTimeString("zh-CN");
    const action = actions[Math.floor(Math.random() * actions.length)];
    const conf = (70 + Math.random() * 28).toFixed(1);
    const score = 60 + Math.floor(Math.random() * 38);
    const powers = ["弱", "中等", "强", "极强"];
    const power = powers[Math.floor(Math.random() * powers.length)];

    state.history.unshift({ timeStr, action, conf, score, power });
    if (state.history.length > 50) state.history.pop();

    const tbody = elements.historyTable;
    tbody.innerHTML = state.history
      .map(
        (h) => `<tr>
        <td>${h.timeStr}</td>
        <td>${h.action}</td>
        <td>${h.conf}%</td>
        <td>${h.score}</td>
        <td>${h.power}</td>
      </tr>`
      )
      .join("");
  }

  function updateReport() {
    elements.totalSessions.textContent = Math.floor(Math.random() * 20) + 1;
    elements.avgScore.textContent = (70 + Math.floor(Math.random() * 25));
    elements.bestAction.textContent = "杀球";
    elements.totalFrames.textContent = state.detections;

    const now = new Date();
    elements.reportDate.textContent = now.toLocaleDateString("zh-CN");
    elements.reportDuration.textContent = Math.floor(Math.random() * 60 + 15) + " 分钟";
    elements.reportActions.textContent = state.history.length + " 次";
    elements.reportHighlights.textContent = "杀球动作评分达到 95 分";
    elements.reportSuggestions.textContent = "建议加强网前小球的练习，提升搓球精度。";
  }

  function updateConfigOutput() {
    const v = (el, def) => el ? (el.type === "number" ? parseFloat(el.value) : el.value) : def;
    const config = {
      model: v(elements.modelSelect, "yolov8"),
      confidence: v(elements.confThreshold, 0.5),
      videoSource: v(elements.videoSource, "file"),
      inferenceBackend: v(elements.inferenceBackend, "onnx"),
      computeDevice: v(elements.computeDevice, "cpu"),
      inputResolution: parseInt(v(elements.inputResolution, "640")),
      modelPrecision: v(elements.modelPrecision, "fp32"),
      frameRate: parseInt(v(elements.frameRate, "30")),
      frameSkip: parseInt(v(elements.frameSkip, "1")),
      roi: {
        x1: parseInt(v(elements.roiX1, "0")),
        y1: parseInt(v(elements.roiY1, "0")),
        x2: parseInt(v(elements.roiX2, "640")),
        y2: parseInt(v(elements.roiY2, "480")),
      },
      saveDetection: v(elements.saveDetection, "false") === "true",
    };
    if (elements.configOutput) {
      elements.configOutput.textContent = JSON.stringify(config, null, 2);
    }
  }

  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    let container = document.querySelector(".toast-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "toast-container";
      document.body.appendChild(container);
    }
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  function downloadTextFile(filename, content, mimeType = "text/markdown;charset=utf-8") {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function safeReportText(element, fallback = "--") {
    return (element?.textContent || "").trim() || fallback;
  }

  function buildMarkdownReport() {
    const report = state.analysisReport || {};
    const topPredictions = (report.top_predictions || [])
      .map(([action, confidence], index) => `${index + 1}. ${action} - ${(Number(confidence || 0) * 100).toFixed(1)}%`)
      .join("\n");
    const shotEvents = (report.shot_events || [])
      .slice(0, 20)
      .map((event, index) => {
        const time = Number(event.time_sec || event.time || 0).toFixed(2);
        const action = event.shot_action || event.action || "击球片段";
        const confidence = event.shot_confidence ?? event.confidence;
        const score = event.quality_score != null ? `，质量 ${event.quality_score}` : "";
        const confText = confidence != null ? `，置信度 ${(Number(confidence) * 100).toFixed(1)}%` : "";
        return `${index + 1}. ${time}s：${action}${confText}${score}`;
      })
      .join("\n");
    const footwork = report.footwork_scores || {};
    const footworkText = Object.entries(footwork)
      .map(([name, value]) => `- ${name}: ${Number(value || 0).toFixed(1)}`)
      .join("\n");
    const generatedAt = new Date().toLocaleString("zh-CN");

    return `# 羽动智练训练报告

生成时间：${generatedAt}

## 本次概览

- 主要动作：${safeReportText(elements.bestAction)}
- 平均评分：${safeReportText(elements.avgScore)}
- 总动作数：${safeReportText(elements.reportActions)}
- 有效帧数：${safeReportText(elements.totalFrames)}
- 训练时长：${safeReportText(elements.reportDuration)}

## 本次亮点

${safeReportText(elements.reportHighlights)}

## 重点问题

${safeReportText(elements.reportIssues)}

## 改进建议

${safeReportText(elements.reportSuggestions)}

## 训练计划

${safeReportText(elements.reportPlan)}

## 复核建议

${safeReportText(elements.reportReview)}

## 动作 Top 分布

${topPredictions || "暂无动作分布数据"}

## 逐拍复盘

${shotEvents || "暂无逐拍数据"}

## 步伐评分

${footworkText || "暂无步伐评分数据"}
`;
  }

  function exportTrainingReport() {
    if (!state.analysisReport) {
      showToast("请先完成一次视频分析，再导出报告", "error");
      return;
    }
    const now = new Date();
    const stamp = [
      now.getFullYear(),
      String(now.getMonth() + 1).padStart(2, "0"),
      String(now.getDate()).padStart(2, "0"),
      String(now.getHours()).padStart(2, "0"),
      String(now.getMinutes()).padStart(2, "0"),
    ].join("");
    downloadTextFile(`badminton-training-report-${stamp}.md`, buildMarkdownReport());
    showToast("训练报告已生成并开始下载", "info");
  }

  function updateCoachContextStatus() {
    if (!elements.coachContextStatus) return;
    const lang = getCoachLang();
    if (!state.analysisReport) {
      elements.coachContextStatus.textContent = t("coachNoReport");
      return;
    }
    const completeLabels = { zh: "已完成分析", en: "Analysis complete", ja: "分析完了", ko: "분석 완료", id: "Analisis selesai" };
    const hitsLabels = { zh: "次击球", en: " shots", ja: "回のショット", ko: "회 타격", id: " pukulan" };
    const action = state.analysisReport.predicted_action || completeLabels[lang] || completeLabels.zh;
    const hits = state.analysisReport.hit_count || state.shotEvents.length || 0;
    elements.coachContextStatus.textContent = `${action} · ${hits}${hitsLabels[lang] || hitsLabels.zh}`;
  }

  function appendCoachMessage(role, content) {
    if (!elements.coachMessages) return null;
    const row = document.createElement("div");
    row.className = `coach-message ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "coach-avatar";
    const lang = getCoachLang();
    if (role === "user") {
      avatar.textContent = lang === "zh" ? "我" : (lang === "ja" ? "私" : lang === "ko" ? "나" : "Me");
    } else {
      avatar.textContent = lang === "zh" ? "教" : "AI";
    }

    const bubble = document.createElement("div");
    bubble.className = "coach-bubble";
    bubble.textContent = content;

    row.appendChild(avatar);
    row.appendChild(bubble);
    elements.coachMessages.appendChild(row);
    elements.coachMessages.scrollTop = elements.coachMessages.scrollHeight;
    return row;
  }

  function setCoachBusy(busy) {
    if (!elements.btnCoachSend) return;
    elements.btnCoachSend.disabled = busy;
    elements.btnCoachSend.textContent = busy ? coachT("thinking") : coachT("send");
  }

  function cleanCoachAnswer(text) {
    return String(text || "")
      .replace(/```[\s\S]*?```/g, "")
      .replace(/^#{1,6}\s*/gm, "")
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/\*(.*?)\*/g, "$1")
      .replace(/`([^`]*)`/g, "$1")
      .replace(/^\s*[-*]\s+/gm, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  function renderCoachStreamingBubble(bubble, steps, answer) {
    if (!bubble) return;
    const stepText = steps.length
      ? `${coachT("thinkingStatus")}\n${steps.map((item) => `· ${item}`).join("\n")}\n\n`
      : "";
    const answerText = cleanCoachAnswer(answer);
    bubble.textContent = `${stepText}${answerText || coachT("generating")}`;
    elements.coachMessages.scrollTop = elements.coachMessages.scrollHeight;
  }

  async function readCoachStream(response, pendingBubble) {
    const reader = response.body?.getReader();
    if (!reader) {
      const data = await response.json().catch(() => ({}));
      return data.answer || "";
    }

    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let answer = "";
    let visibleAnswer = "";
    let queuedAnswer = "";
    const steps = [];
    let typeTimer = null;

    const startTyping = () => {
      if (typeTimer) return;
      typeTimer = window.setInterval(() => {
        if (!queuedAnswer) {
          window.clearInterval(typeTimer);
          typeTimer = null;
          return;
        }
        const take = Math.min(3, queuedAnswer.length);
        visibleAnswer += queuedAnswer.slice(0, take);
        queuedAnswer = queuedAnswer.slice(take);
        renderCoachStreamingBubble(pendingBubble, steps, visibleAnswer);
      }, 28);
    };

    const flushTyping = async () => {
      while (queuedAnswer) {
        const take = Math.min(8, queuedAnswer.length);
        visibleAnswer += queuedAnswer.slice(0, take);
        queuedAnswer = queuedAnswer.slice(take);
        renderCoachStreamingBubble(pendingBubble, steps, visibleAnswer);
        await new Promise((resolve) => window.setTimeout(resolve, 10));
      }
      if (typeTimer) {
        window.clearInterval(typeTimer);
        typeTimer = null;
      }
    };

    const handleEvent = (event, data) => {
      if (event === "status" && data.text) {
        steps.push(data.text);
        renderCoachStreamingBubble(pendingBubble, steps, visibleAnswer);
      } else if (event === "delta" && data.text) {
        answer += data.text;
        queuedAnswer += data.text;
        startTyping();
      } else if (event === "error") {
        throw new Error(data.message || coachT("genFailed"));
      }
    };

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const packets = buffer.split("\n\n");
      buffer = packets.pop() || "";
      for (const packet of packets) {
        let event = "message";
        let dataText = "";
        packet.split("\n").forEach((line) => {
          if (line.startsWith("event:")) event = line.slice(6).trim();
          if (line.startsWith("data:")) dataText += line.slice(5).trim();
        });
        if (!dataText) continue;
        handleEvent(event, JSON.parse(dataText));
      }
    }
    await flushTyping();
    return cleanCoachAnswer(answer);
  }

  async function sendCoachQuestion(questionText = null) {
    const question = (questionText || elements.coachQuestion?.value || "").trim();
    if (!question) {
      showToast(coachT("noQuestion"), "error");
      return;
    }

    appendCoachMessage("user", question);
    state.coachHistory.push({ role: "user", content: question });
    if (elements.coachQuestion) elements.coachQuestion.value = "";

    const pending = appendCoachMessage("assistant", `${coachT("thinkingStatus")}\n· ${coachT("firstStatus")}`);
    const pendingBubble = pending?.querySelector(".coach-bubble");
    setCoachBusy(true);

    try {
      await ensureBackendReady();
      const response = await fetch(apiUrl("/api/coach/chat/stream"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: elements.coachProvider?.value || "qwen",
          language: getCoachLang(),
          question,
          history: state.coachHistory.slice(-8),
          report: state.analysisReport,
          use_report_context: Boolean(elements.coachUseReport?.checked),
          timeout: 90,
        }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
      const answer = await readCoachStream(response, pendingBubble) || coachT("noAnswer");
      if (pendingBubble) pendingBubble.textContent = answer;
      state.coachHistory.push({ role: "assistant", content: answer });
    } catch (error) {
      const message = `${coachT("unavailable")}${formatFetchError(error)}`;
      if (pendingBubble) pendingBubble.textContent = message;
      state.coachHistory.push({ role: "assistant", content: message });
    } finally {
      setCoachBusy(false);
    }
  }

  // ---- Simulation: Start Detection ----
  let simInterval = null;

  if (elements.btnStart) {
  elements.btnStart.addEventListener("click", async () => {
    if (state.detecting) return;
    if (!state.user) {
      showAuthModal("login");
      return;
    }
    if (!state.precheckPassed && state.precheckResult && state.precheckResult.overall === "fail") {
      showUploadHint("视频预检未通过，请重新拍摄后上传，或点击\"继续分析\"强制分析");
      return;
    }
    await runBackendAnalysis();
  });
  }

  if (elements.btnProceedAnalyze) {
    elements.btnProceedAnalyze.addEventListener("click", async () => {
      if (state.detecting) return;
      if (!state.user) {
        showAuthModal("login");
        return;
      }
      await runBackendAnalysis();
    });
  }

  if (elements.btnReupload) {
    elements.btnReupload.addEventListener("click", () => {
      if (!state.user) {
        showAuthModal("login");
        return;
      }
      elements.videoUploadInput.click();
    });
  }

  if (elements.guideToggle && elements.shootingGuide) {
    elements.guideToggle.addEventListener("click", () => {
      elements.shootingGuide.classList.toggle("collapsed");
    });
  }

  if (elements.btnRefreshHistory) {
    elements.btnRefreshHistory.addEventListener("click", loadHistoryList);
  }

  if (elements.emptyMedia) {
  elements.emptyMedia.addEventListener("click", () => {
    if (!state.user) {
      showAuthModal("login");
      return;
    }
    if (elements.videoSource && elements.videoSource.value === "camera") {
      showUploadHint("当前演示版暂未接入摄像头，请先选择文件上传");
      return;
    }
    if (elements.videoUploadInput) elements.videoUploadInput.click();
  });
  }

  if (elements.frameCanvasWrap) {
  elements.frameCanvasWrap.addEventListener("click", (event) => {
    if (state.frameImage && event.target === elements.frameCanvas) {
      addCourtCornerFromEvent(event);
      return;
    }
    if (!state.user) {
      showAuthModal("login");
      return;
    }
    if (!state.frameImage && (!elements.videoSource || elements.videoSource.value === "file")) {
      if (elements.videoUploadInput) elements.videoUploadInput.click();
    }
  });
  }

  if (elements.emptyMedia) {
  elements.emptyMedia.addEventListener("dragover", (event) => {
    event.preventDefault();
    elements.emptyMedia.classList.add("drag-over");
  });

  elements.emptyMedia.addEventListener("dragleave", () => {
    elements.emptyMedia.classList.remove("drag-over");
  });

  elements.emptyMedia.addEventListener("drop", (event) => {
    event.preventDefault();
    elements.emptyMedia.classList.remove("drag-over");
    if (!state.user) {
      showAuthModal("login");
      return;
    }
    const [file] = event.dataTransfer.files || [];
    loadUploadedVideo(file);
  });
  }

  if (elements.videoUploadInput) {
  elements.videoUploadInput.addEventListener("change", (event) => {
    const [file] = event.target.files || [];
    loadUploadedVideo(file);
    event.target.value = "";
  });
  }

  if (elements.btnStop) {
  elements.btnStop.addEventListener("click", () => {
    if (!state.detecting) return;
    state.detecting = false;
    clearInterval(simInterval);
    simInterval = null;
    if (elements.btnStart) {
      elements.btnStart.classList.remove("btn-secondary");
      elements.btnStart.classList.add("btn-primary");
      elements.btnStart.textContent = t("btnStart");
    }
  });
  }

  if (elements.btnReset) {
  elements.btnReset.addEventListener("click", () => {
    stopCourtPlaybackLoop();
    if (state.analysisTimerId) {
      window.clearInterval(state.analysisTimerId);
      state.analysisTimerId = null;
    }
    if (elements.analysisTimer) elements.analysisTimer.hidden = true;
    if (state.detecting) {
      clearInterval(simInterval);
      simInterval = null;
      state.detecting = false;
    }
    state.detections = 0;
    state.fps = 0;
    state.latency = 0;
    state.avgConf = 0;
    state.bbox = null;
    state.realVideoLoaded = false;
    state.frameImage = null;
    state.history = [];
    state.analysisReport = null;
    state.coachHistory = [];
    state.shotEvents = [];
    state.footworkTrace = [];
    state.radarData = [0, 0, 0, 0, 0, 0];
    state.precheckPassed = false;
    state.precheckResult = null;
    state.videoFile = null;

    hidePrecheckPanel();
    updateMetrics();
    const noRecLabels = { zh: "暂无检测记录", en: "No detection records", ja: "検出記録なし", ko: "검출 기록 없음", id: "Tidak ada catatan" };
    if (elements.historyTable) {
      elements.historyTable.innerHTML =
        `<tr><td colspan="5" style="text-align:center; color:var(--muted); padding:32px;">${noRecLabels[state.uiLanguage] || noRecLabels.zh}</td></tr>`;
    }

    if (elements.frameCanvas && ctx) ctx.clearRect(0, 0, elements.frameCanvas.width, elements.frameCanvas.height);
    if (elements.emptyMedia) elements.emptyMedia.style.display = "flex";
    if (elements.frameCanvasWrap) elements.frameCanvasWrap.style.display = "none";
    drawRadar(state.radarData);
    renderShotTimeline();

    if (elements.btnStart) {
      elements.btnStart.classList.remove("btn-secondary");
      elements.btnStart.classList.add("btn-primary");
      elements.btnStart.textContent = t("btnStart");
    }
    setConnected(false);
    updateCoachContextStatus();
  });
  }

  // ---- Config Events ----
  [
    elements.modelSelect,
    elements.confThreshold,
    elements.videoSource,
    elements.inferenceBackend,
    elements.computeDevice,
    elements.inputResolution,
    elements.modelPrecision,
    elements.frameRate,
    elements.frameSkip,
    elements.roiX1, elements.roiY1, elements.roiX2, elements.roiY2,
    elements.saveDetection,
  ].filter(Boolean).forEach((el) => {
    el.addEventListener("change", updateConfigOutput);
  });

  if (elements.btnSaveSettings) {
  elements.btnSaveSettings.addEventListener("click", () => {
    updateConfigOutput();
    const savedLabels = { zh: "设置已保存", en: "Settings saved", ja: "設定を保存しました", ko: "설정 저장됨", id: "Pengaturan disimpan" };
    const toast = document.createElement("div");
    toast.className = "toast toast-success";
    toast.textContent = savedLabels[state.uiLanguage] || savedLabels.zh;
    let container = document.querySelector(".toast-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "toast-container";
      document.body.appendChild(container);
    }
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  });
  }

  if (elements.btnResetSettings) {
  elements.btnResetSettings.addEventListener("click", () => {
    if (elements.modelSelect) elements.modelSelect.value = "yolov8";
    if (elements.confThreshold) elements.confThreshold.value = 0.5;
    if (elements.videoSource) elements.videoSource.value = "file";
    if (elements.inferenceBackend) elements.inferenceBackend.value = "onnx";
    if (elements.computeDevice) elements.computeDevice.value = "cpu";
    if (elements.inputResolution) elements.inputResolution.value = "640";
    if (elements.modelPrecision) elements.modelPrecision.value = "fp32";
    if (elements.frameRate) elements.frameRate.value = "30";
    if (elements.frameSkip) elements.frameSkip.value = "1";
    if (elements.roiX1) elements.roiX1.value = "0";
    if (elements.roiY1) elements.roiY1.value = "0";
    if (elements.roiX2) elements.roiX2.value = "640";
    if (elements.roiY2) elements.roiY2.value = "480";
    if (elements.saveDetection) elements.saveDetection.value = "false";
    updateConfigOutput();
  });
  }

  if (elements.btnExport) {
  elements.btnExport.addEventListener("click", () => {
    exportTrainingReport();
  });
  }

  if (elements.btnCoachSend) {
    elements.btnCoachSend.addEventListener("click", () => {
      sendCoachQuestion();
    });
  }

  if (elements.coachQuestion) {
    elements.coachQuestion.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        sendCoachQuestion();
      }
    });
  }

  document.querySelectorAll(".coach-prompt").forEach((button) => {
    button.addEventListener("click", () => {
      const prompt = button.dataset.prompt || button.textContent || "";
      if (elements.coachQuestion) {
        elements.coachQuestion.value = prompt;
        elements.coachQuestion.focus();
      }
    });
  });

  // ---- Auth Logic ----
  function authApi(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    if (state.authToken) {
      headers["Authorization"] = `Bearer ${state.authToken}`;
    }
    return fetch(apiUrl(path), { ...options, headers }).then(async (resp) => {
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        throw new Error(data.detail || `HTTP ${resp.status}`);
      }
      return data;
    });
  }

  function saveAuth(token, user) {
    state.authToken = token;
    state.user = user;
    try {
      localStorage.setItem("badminton_token", token);
      localStorage.setItem("badminton_user", JSON.stringify(user));
    } catch (e) {}
  }

  function clearAuth() {
    state.authToken = null;
    state.user = null;
    try {
      localStorage.removeItem("badminton_token");
      localStorage.removeItem("badminton_user");
    } catch (e) {}
  }

  function getUserInitial(nickname) {
    if (!nickname) return "用";
    return nickname.charAt(0).toUpperCase();
  }

  function updateAuthUI() {
    const isLoggedIn = !!state.user;
    if (elements.btnLogin) elements.btnLogin.hidden = isLoggedIn;
    if (elements.userMenu) elements.userMenu.hidden = !isLoggedIn;

    if (isLoggedIn && state.user) {
      const u = state.user;
      const initial = getUserInitial(u.nickname);

      if (elements.userNickname) elements.userNickname.textContent = u.nickname;
      if (elements.userUsername) elements.userUsername.textContent = "@" + u.username;
      if (elements.userAvatarCircle) {
        if (u.avatar) {
          elements.userAvatarCircle.innerHTML = `<img src="${u.avatar}" alt="${u.nickname}" />`;
        } else {
          elements.userAvatarCircle.textContent = initial;
        }
      }
      if (elements.wechatBadge) elements.wechatBadge.hidden = !u.has_wechat;

      if (elements.settingsNickname) elements.settingsNickname.textContent = u.nickname;
      if (elements.settingsUsername) elements.settingsUsername.textContent = "@" + u.username;
      if (elements.settingsAvatar) {
        if (u.avatar) {
          elements.settingsAvatar.innerHTML = `<img src="${u.avatar}" alt="${u.nickname}" />`;
        } else {
          elements.settingsAvatar.textContent = initial;
        }
      }
      if (elements.settingsWechatStatus) {
        const statusEl = elements.settingsWechatStatus;
        const textSpan = statusEl.querySelector("span:last-child");
        if (u.has_wechat) {
          statusEl.classList.add("bound");
          if (textSpan) textSpan.textContent = t("wechatBound");
        } else {
          statusEl.classList.remove("bound");
          if (textSpan) textSpan.textContent = t("wechatNotBound");
        }
      }
    } else {
      if (elements.settingsNickname) elements.settingsNickname.textContent = "--";
      if (elements.settingsUsername) elements.settingsUsername.textContent = "--";
      if (elements.settingsAvatar) elements.settingsAvatar.textContent = "用";
      if (elements.settingsWechatStatus) {
        elements.settingsWechatStatus.classList.remove("bound");
        const textSpan = elements.settingsWechatStatus.querySelector("span:last-child");
        if (textSpan) textSpan.textContent = t("wechatNotBound");
      }
    }

    if (elements.accountGuest) elements.accountGuest.hidden = isLoggedIn;
    if (elements.accountLogged) elements.accountLogged.hidden = !isLoggedIn;
  }

  function showAuthModal(tab = "login") {
    switchAuthTab(tab);
    if (elements.authModal) elements.authModal.hidden = false;
    if (elements.loginError) {
      elements.loginError.hidden = true;
      elements.loginError.textContent = "";
    }
    if (elements.registerError) {
      elements.registerError.hidden = true;
      elements.registerError.textContent = "";
    }
  }

  function hideAuthModal() {
    if (elements.authModal) elements.authModal.hidden = true;
    if (elements.loginError) elements.loginError.hidden = true;
    if (elements.registerError) elements.registerError.hidden = true;
  }

  function showProfileModal() {
    if (!state.user) return;
    if (elements.editNickname) elements.editNickname.value = state.user.nickname || "";
    if (elements.editAvatar) elements.editAvatar.value = state.user.avatar || "";
    if (elements.profileError) {
      elements.profileError.hidden = true;
      elements.profileError.textContent = "";
    }
    if (elements.profileModal) elements.profileModal.hidden = false;
  }

  function hideProfileModal() {
    if (elements.profileModal) elements.profileModal.hidden = true;
    if (elements.profileError) elements.profileError.hidden = true;
  }

  // ---- Bind WeChat Modal ----
  let bindPollTimer = null;
  let bindCountdownTimer = null;
  let currentBindToken = null;

  function showBindWechatModal() {
    if (!state.user) {
      showAuthModal(true);
      return;
    }
    if (state.user && state.user.has_wechat) {
      showToast(coachT("wechatBound"), "info");
      return;
    }
    if (elements.bindWechatModal) elements.bindWechatModal.hidden = false;
    createBindToken();
  }

  function hideBindWechatModal() {
    if (elements.bindWechatModal) elements.bindWechatModal.hidden = true;
    stopBindPolling();
  }

  async function createBindToken() {
    try {
      const data = await authApi("/api/auth/wechat/bind-token", { method: "POST", body: JSON.stringify({}) });
      currentBindToken = data.token;
      if (elements.bindCodeDisplay) elements.bindCodeDisplay.textContent = data.token;
      if (elements.bindStatus) elements.bindStatus.textContent = coachT("bindWaiting");
      startBindPolling(data.token, data.expires_at);
    } catch (err) {
      if (elements.bindStatus) elements.bindStatus.textContent = coachT("bindFailed");
      showToast(err.message || coachT("bindFailed"), "error");
    }
  }

  function startBindPolling(token, expiresAt) {
    stopBindPolling();
    const deadline = expiresAt ? expiresAt * 1000 : Date.now() + 600000;
    updateBindTimer(deadline);
    bindCountdownTimer = setInterval(() => updateBindTimer(deadline), 1000);

    const poll = async () => {
      try {
        const status = await authApi(`/api/auth/wechat/bind-token/${token}/status`);
        if (status.status === "confirmed") {
          stopBindPolling();
          if (elements.bindStatus) elements.bindStatus.textContent = coachT("bindSuccess");
          state.user = status.user;
          localStorage.setItem("badminton_user", JSON.stringify(state.user));
          updateAuthUI();
          showToast(coachT("bindSuccess"), "success");
          setTimeout(hideBindWechatModal, 1500);
          return;
        }
        if (status.status === "expired") {
          stopBindPolling();
          if (elements.bindStatus) elements.bindStatus.textContent = coachT("bindExpired");
          return;
        }
      } catch (e) {
        // ignore poll errors
      }
      bindPollTimer = setTimeout(poll, 2000);
    };
    poll();
  }

  function stopBindPolling() {
    if (bindPollTimer) {
      clearTimeout(bindPollTimer);
      bindPollTimer = null;
    }
    if (bindCountdownTimer) {
      clearInterval(bindCountdownTimer);
      bindCountdownTimer = null;
    }
  }

  function updateBindTimer(deadline) {
    const remaining = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
    const min = String(Math.floor(remaining / 60)).padStart(2, "0");
    const sec = String(remaining % 60).padStart(2, "0");
    if (elements.bindTimer) elements.bindTimer.textContent = `${min}:${sec}`;
    if (remaining <= 0) {
      stopBindPolling();
      if (elements.bindStatus) elements.bindStatus.textContent = coachT("bindExpired");
    }
  }

  async function copyBindCode() {
    if (!currentBindToken) return;
    try {
      await navigator.clipboard.writeText(currentBindToken);
      showToast("绑定码已复制", "success");
    } catch (e) {
      showToast("复制失败，请手动长按复制", "info");
    }
  }

  // ---- Onboarding Tour ----
  const TOUR_STEPS = [
    { target: "emptyMedia", titleKey: "tourStep1Title", descKey: "tourStep1Desc", position: "bottom" },
    { target: "btnStart", titleKey: "tourStep2Title", descKey: "tourStep2Desc", position: "bottom" },
    { target: "shotTimeline", titleKey: "tourStep3Title", descKey: "tourStep3Desc", position: "top" },
    { target: "report", titleKey: "tourStep4Title", descKey: "tourStep4Desc", position: "bottom", navTab: "report" },
    { target: "history", titleKey: "tourStep5Title", descKey: "tourStep5Desc", position: "bottom", navTab: "history" },
  ];

  let currentTourStep = 0;
  let tourResizeHandler = null;

  function startTour(force = false) {
    if (!elements.tourOverlay) {
      console.warn("[Tour] overlay element not found");
      return;
    }
    if (!force) {
      try {
        const seen = localStorage.getItem("badminton_tour_seen");
        if (seen) {
          console.log("[Tour] already seen, skip. Use startTour(true) to force.");
          return;
        }
      } catch (e) {}
    }
    currentTourStep = 0;
    switchTab("training");
    elements.tourOverlay.hidden = false;
    document.body.style.overflow = "hidden";
    renderTourStep();
    console.log("[Tour] started");
  }

  function endTour() {
    if (elements.tourOverlay) elements.tourOverlay.hidden = true;
    document.body.style.overflow = "";
    try {
      localStorage.setItem("badminton_tour_seen", "1");
    } catch (e) {}
    if (tourResizeHandler) {
      window.removeEventListener("resize", tourResizeHandler);
      tourResizeHandler = null;
    }
  }

  function renderTourStep() {
    const step = TOUR_STEPS[currentTourStep];
    if (!step) {
      endTour();
      return;
    }
    if (step.navTab) {
      switchTab(step.navTab);
    }
    const target = elements[step.target] || document.querySelector(`[data-tab="${step.target}"]`);
    if (!target) {
      console.warn(`[Tour] target not found: ${step.target}`);
      currentTourStep++;
      renderTourStep();
      return;
    }
    const rect = target.getBoundingClientRect();
    if (!rect.width || !rect.height || !target.offsetParent) {
      console.warn(`[Tour] target not visible: ${step.target}, skip`);
      currentTourStep++;
      renderTourStep();
      return;
    }
    // Scroll target into center of viewport before positioning
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    setTimeout(() => {
      positionTourHighlight(target, step.position);
    }, 350);
    if (elements.tourTitle) elements.tourTitle.textContent = t(step.titleKey);
    if (elements.tourDesc) elements.tourDesc.textContent = t(step.descKey);
    if (elements.btnNextTour) {
      const isLast = currentTourStep === TOUR_STEPS.length - 1;
      elements.btnNextTour.textContent = t(isLast ? "tourFinish" : "tourNext");
    }
    renderTourDots();
    if (tourResizeHandler) window.removeEventListener("resize", tourResizeHandler);
    tourResizeHandler = () => positionTourHighlight(target, step.position);
    window.addEventListener("resize", tourResizeHandler);
  }

  function positionTourHighlight(target, position) {
    const rect = target.getBoundingClientRect();
    const padding = 8;
    // Overlay is fixed, so use viewport coordinates directly
    if (elements.tourHighlight) {
      elements.tourHighlight.style.left = (rect.left - padding) + "px";
      elements.tourHighlight.style.top = (rect.top - padding) + "px";
      elements.tourHighlight.style.width = (rect.width + padding * 2) + "px";
      elements.tourHighlight.style.height = (rect.height + padding * 2) + "px";
    }
    if (elements.tourCard) {
      const cardRect = elements.tourCard.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      let top = rect.bottom + 16;
      if (position === "top") {
        top = rect.top - cardRect.height - 16;
      }
      let left = rect.left + rect.width / 2 - cardRect.width / 2;
      left = Math.max(16, Math.min(left, viewportWidth - cardRect.width - 16));
      // Keep card inside viewport vertically
      if (top + cardRect.height > viewportHeight - 16) {
        top = rect.top - cardRect.height - 16;
      }
      if (top < 16) {
        top = rect.bottom + 16;
      }
      elements.tourCard.style.left = left + "px";
      elements.tourCard.style.top = top + "px";
    }
  }

  function renderTourDots() {
    if (!elements.tourDots) return;
    elements.tourDots.innerHTML = "";
    TOUR_STEPS.forEach((_, idx) => {
      const dot = document.createElement("span");
      dot.className = "tour-dot" + (idx === currentTourStep ? " active" : "");
      elements.tourDots.appendChild(dot);
    });
  }

  function nextTourStep() {
    currentTourStep++;
    renderTourStep();
  }

  function switchAuthTab(tab) {
    document.querySelectorAll(".auth-tab").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.authTab === tab);
    });
    document.querySelectorAll(".auth-form").forEach((form) => {
      form.classList.toggle("active", form.id === (tab === "login" ? "loginForm" : "registerForm"));
    });
  }

  async function handleLogin(e) {
    e.preventDefault();
    if (elements.loginError) {
      elements.loginError.hidden = true;
      elements.loginError.textContent = "";
    }
    const username = (elements.loginUsername?.value || "").trim();
    const password = elements.loginPassword?.value || "";
    if (!username || !password) {
      if (elements.loginError) {
        elements.loginError.textContent = "请输入用户名和密码";
        elements.loginError.hidden = false;
      }
      return;
    }
    try {
      const data = await authApi("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      saveAuth(data.token, data.user);
      updateAuthUI();
      hideAuthModal();
      showToast(t("loginSuccess"), "success");
      if (elements.loginPassword) elements.loginPassword.value = "";
    } catch (err) {
      if (elements.loginError) {
        elements.loginError.textContent = err.message || t("loginFailed");
        elements.loginError.hidden = false;
      }
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    if (elements.registerError) {
      elements.registerError.hidden = true;
      elements.registerError.textContent = "";
    }
    const username = (elements.regUsername?.value || "").trim();
    const nickname = (elements.regNickname?.value || "").trim();
    const email = (elements.regEmail?.value || "").trim();
    const password = elements.regPassword?.value || "";
    if (!username || !password) {
      if (elements.registerError) {
        elements.registerError.textContent = "请填写用户名和密码";
        elements.registerError.hidden = false;
      }
      return;
    }
    try {
      const data = await authApi("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ username, password, nickname, email }),
      });
      saveAuth(data.token, data.user);
      updateAuthUI();
      hideAuthModal();
      showToast(t("registerSuccess"), "success");
      if (elements.regPassword) elements.regPassword.value = "";
      setTimeout(() => startTour(true), 350);
    } catch (err) {
      if (elements.registerError) {
        elements.registerError.textContent = err.message || t("registerFailed");
        elements.registerError.hidden = false;
      }
    }
  }

  async function handleLogout() {
    try {
      await authApi("/api/auth/logout", { method: "POST" });
    } catch (e) {}
    clearAuth();
    updateAuthUI();
    if (elements.userDropdown) elements.userDropdown.hidden = true;
    showToast(t("logoutSuccess"), "info");
  }

  async function fetchCurrentUser() {
    try {
      const user = await authApi("/api/auth/me");
      state.user = user;
      updateAuthUI();
    } catch (e) {
      clearAuth();
      updateAuthUI();
    }
  }

  async function handleSaveProfile(e) {
    e.preventDefault();
    if (elements.profileError) {
      elements.profileError.hidden = true;
      elements.profileError.textContent = "";
    }
    const nickname = (elements.editNickname?.value || "").trim();
    const avatar = (elements.editAvatar?.value || "").trim();
    if (!nickname) {
      if (elements.profileError) {
        elements.profileError.textContent = "昵称不能为空";
        elements.profileError.hidden = false;
      }
      return;
    }
    try {
      const updated = await authApi("/api/auth/profile", {
        method: "PUT",
        body: JSON.stringify({ nickname, avatar: avatar || null, language: state.uiLanguage }),
      });
      state.user = updated;
      try {
        localStorage.setItem("badminton_user", JSON.stringify(updated));
      } catch (e) {}
      updateAuthUI();
      hideProfileModal();
      showToast(t("profileUpdateSuccess"), "success");
    } catch (err) {
      if (elements.profileError) {
        elements.profileError.textContent = err.message || "更新失败";
        elements.profileError.hidden = false;
      }
    }
  }

  function handleWechatLogin() {
    if (elements.wechatHint) {
      elements.wechatHint.hidden = false;
    }
    showToast("微信登录需要在微信小程序中使用", "info");
  }

  // Auth event bindings
  if (elements.btnLogin) {
    elements.btnLogin.addEventListener("click", () => showAuthModal("login"));
  }
  if (elements.btnSettingsLogin) {
    elements.btnSettingsLogin.addEventListener("click", () => showAuthModal("login"));
  }
  if (elements.btnCloseAuthModal) {
    elements.btnCloseAuthModal.addEventListener("click", hideAuthModal);
  }
  if (elements.authModal) {
    elements.authModal.addEventListener("click", (e) => {
      if (e.target === elements.authModal) hideAuthModal();
    });
  }
  document.querySelectorAll(".auth-tab").forEach((tab) => {
    tab.addEventListener("click", () => switchAuthTab(tab.dataset.authTab));
  });
  if (elements.loginForm) {
    elements.loginForm.addEventListener("submit", handleLogin);
  }
  if (elements.registerForm) {
    elements.registerForm.addEventListener("submit", handleRegister);
  }
  if (elements.btnWechatLogin) {
    elements.btnWechatLogin.addEventListener("click", handleWechatLogin);
  }
  if (elements.btnWechatRegister) {
    elements.btnWechatRegister.addEventListener("click", handleWechatLogin);
  }
  if (elements.btnSkipTour) {
    elements.btnSkipTour.addEventListener("click", endTour);
  }
  if (elements.btnNextTour) {
    elements.btnNextTour.addEventListener("click", nextTourStep);
  }
  if (elements.tourOverlay) {
    elements.tourOverlay.addEventListener("click", (e) => {
      if (e.target === elements.tourOverlay) endTour();
    });
  }
  if (elements.btnLogout) {
    elements.btnLogout.addEventListener("click", handleLogout);
  }
  if (elements.btnSettingsLogout) {
    elements.btnSettingsLogout.addEventListener("click", handleLogout);
  }
  if (elements.btnSwitchAccount) {
    elements.btnSwitchAccount.addEventListener("click", () => {
      if (elements.userDropdown) elements.userDropdown.hidden = true;
      showAuthModal("login");
    });
  }
  if (elements.btnUserAvatar) {
    elements.btnUserAvatar.addEventListener("click", (e) => {
      e.stopPropagation();
      if (elements.userDropdown) {
        elements.userDropdown.hidden = !elements.userDropdown.hidden;
      }
    });
  }
  document.addEventListener("click", () => {
    if (elements.userDropdown && !elements.userDropdown.hidden) {
      elements.userDropdown.hidden = true;
    }
  });
  if (elements.btnEditProfile) {
    elements.btnEditProfile.addEventListener("click", showProfileModal);
  }
  if (elements.btnCloseProfileModal) {
    elements.btnCloseProfileModal.addEventListener("click", hideProfileModal);
  }
  if (elements.btnCancelProfile) {
    elements.btnCancelProfile.addEventListener("click", hideProfileModal);
  }
  if (elements.profileForm) {
    elements.profileForm.addEventListener("submit", handleSaveProfile);
  }
  if (elements.profileModal) {
    elements.profileModal.addEventListener("click", (e) => {
      if (e.target === elements.profileModal) hideProfileModal();
    });
  }
  if (elements.btnBindWechat) {
    elements.btnBindWechat.addEventListener("click", showBindWechatModal);
  }
  if (elements.btnCloseBindWechatModal) {
    elements.btnCloseBindWechatModal.addEventListener("click", hideBindWechatModal);
  }
  if (elements.bindWechatModal) {
    elements.bindWechatModal.addEventListener("click", (e) => {
      if (e.target === elements.bindWechatModal) hideBindWechatModal();
    });
  }
  if (elements.btnCopyBindCode) {
    elements.btnCopyBindCode.addEventListener("click", copyBindCode);
  }

  // Restore auth from localStorage
  try {
    const savedToken = localStorage.getItem("badminton_token");
    const savedUser = localStorage.getItem("badminton_user");
    if (savedToken && savedUser) {
      state.authToken = savedToken;
      try {
        state.user = JSON.parse(savedUser);
      } catch (e) {
        state.user = null;
        state.authToken = null;
        localStorage.removeItem("badminton_token");
        localStorage.removeItem("badminton_user");
      }
    }
  } catch (e) {}

  // Ensure all modals are hidden initially
  if (elements.authModal) elements.authModal.hidden = true;
  if (elements.profileModal) elements.profileModal.hidden = true;
  if (elements.userDropdown) elements.userDropdown.hidden = true;

  updateAuthUI();
  if (state.authToken) {
    fetchCurrentUser();
  }

  // ESC key to close modals
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (elements.authModal && !elements.authModal.hidden) {
        hideAuthModal();
      }
      if (elements.profileModal && !elements.profileModal.hidden) {
        hideProfileModal();
      }
      if (elements.userDropdown && !elements.userDropdown.hidden) {
        elements.userDropdown.hidden = true;
      }
    }
  });

  // Global language selector (settings panel buttons)
  document.querySelectorAll(".lang-option").forEach((btn) => {
    btn.addEventListener("click", () => {
      const lang = (btn.dataset.lang || "zh").toLowerCase();
      if (!SUPPORTED_LANGS.includes(lang)) return;
      document.querySelectorAll(".lang-option").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      applyGlobalLanguage(lang);
      state.coachHistory = [];
      if (elements.coachMessages) {
        elements.coachMessages.innerHTML = "";
        const welcomeRow = document.createElement("div");
        welcomeRow.className = "coach-message assistant";
        const ld = LANG_DISPLAY[lang];
        welcomeRow.innerHTML = `<div class="coach-avatar">${ld.avatar}</div><div class="coach-bubble" id="coachWelcome"></div>`;
        elements.coachMessages.appendChild(welcomeRow);
        elements.coachWelcome = welcomeRow.querySelector("#coachWelcome");
        if (elements.coachWelcome) {
          elements.coachWelcome.textContent = getCoachWelcomeText(lang);
        }
      }
      updateCoachUILanguage();
    });
  });

  // Initialize language from localStorage
  let savedLang = "zh";
  try { savedLang = localStorage.getItem("badminton_lang") || "zh"; } catch (e) {}
  if (!SUPPORTED_LANGS.includes(savedLang)) savedLang = "zh";
  state.uiLanguage = savedLang;
  applyGlobalLanguage(savedLang);

  updateCoachUILanguage();

  // Init animated background
  initAnimatedBackground();

  // ---- Sample Frame Generator ----
  function generateSampleFrame() {
    const canvas = elements.frameCanvas;
    const w = canvas.width;
    const h = canvas.height;

    // Dark background
    ctx.fillStyle = "#0d2219";
    ctx.fillRect(0, 0, w, h);

    // Court floor
    ctx.fillStyle = "#132e25";
    ctx.fillRect(60, 40, w - 120, h - 80);

    // Court lines
    ctx.strokeStyle = "#254b3e";
    ctx.lineWidth = 1.5;
    ctx.strokeRect(60, 40, w - 120, h - 80);
    ctx.beginPath();
    ctx.moveTo(w / 2, 40);
    ctx.lineTo(w / 2, h - 40);
    ctx.stroke();

    // Simulated person silhouette
    ctx.fillStyle = "#1a4035";
    ctx.beginPath();
    ctx.arc(w / 2, h * 0.35, 18, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillRect(w / 2 - 10, h * 0.38, 20, h * 0.28);

    // Racket
    ctx.strokeStyle = "#5eff9f";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(w / 2 + 12, h * 0.4);
    ctx.lineTo(w / 2 + 40, h * 0.25);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(w / 2 + 44, h * 0.23, 10, 0, Math.PI * 2);
    ctx.stroke();

    // Shuttlecock
    ctx.fillStyle = "#ffdf70";
    ctx.beginPath();
    ctx.arc(w / 2 + 80, h * 0.18, 5, 0, Math.PI * 2);
    ctx.fill();

    // Store as image for drawFrame
    const img = new Image();
    img.src = canvas.toDataURL();
    state.frameImage = img;
    state.bbox = { x1: 0.35, y1: 0.25, x2: 0.65, y2: 0.7 };
    drawFrame();
  }

  // ---- Init ----
  async function loadHistoryList() {
    if (!window.location.protocol.startsWith("http")) return;
    try {
      const resp = await fetch(`/api/history?limit=50&language=${getCoachLang()}`);
      if (!resp.ok) throw new Error("Failed to load history");
      const data = await resp.json();
      renderHistoryList(data.items || []);
      drawTrendChart(data.items || []);
    } catch (err) {
      console.error("Load history failed:", err);
    }
  }

  function renderHistoryList(items) {
    // Summary stats
    const totalSessions = items.length;
    const scores = items.filter((i) => i.avg_quality_score != null).map((i) => i.avg_quality_score);
    const avgScore = scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : "--";
    const totalShots = items.reduce((sum, i) => sum + (i.total_shots || 0), 0);
    const lastDate = items.length > 0 ? (items[0].created_at_display || items[0].created_at || "").slice(5, 16) : "--";

    elements.historyTotalSessions.textContent = totalSessions;
    elements.historyAvgScore.textContent = avgScore;
    elements.historyTotalShots.textContent = totalShots;
    elements.historyLastDate.textContent = lastDate;

    // List
    if (items.length === 0) {
      elements.historyList.innerHTML = '<div class="history-empty">暂无训练记录，完成一次视频分析后会显示在这里。</div>';
      return;
    }

    elements.historyList.innerHTML = "";
    items.forEach((item) => {
      const score = item.avg_quality_score;
      let scoreClass = "mid";
      if (score >= 75) scoreClass = "high";
      else if (score < 55) scoreClass = "low";
      const scoreDisplay = score != null ? Math.round(score) : "--";
      const duration = item.duration_seconds ? `${item.duration_seconds.toFixed(0)}秒` : "";
      const dateStr = (item.created_at_display || item.created_at || "").slice(5, 16);

      const div = document.createElement("div");
      div.className = "history-item";
      div.innerHTML = `
        <div class="history-item-date">${dateStr}</div>
        <div class="history-item-info">
          <div class="history-item-title">${item.video_name || "训练视频"}</div>
          <div class="history-item-meta">
            <span>击球 ${item.total_shots || 0} 次</span>
            ${duration ? `<span>时长 ${duration}</span>` : ""}
            ${item.dominant_action ? `<span>主要动作 ${item.dominant_action}</span>` : ""}
          </div>
        </div>
        <div class="history-item-score ${scoreClass}">${scoreDisplay}</div>
      `;
      if (item.annotated_video_url) {
        div.style.cursor = "pointer";
        div.addEventListener("click", () => {
          switchTab("report");
        });
      }
      elements.historyList.appendChild(div);
    });
  }

  function drawTrendChart(items) {
    const canvas = elements.trendChart;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = 200 * dpr;
    canvas.style.height = "200px";
    ctx.scale(dpr, dpr);
    const w = rect.width;
    const h = 200;
    const pad = { top: 20, right: 20, bottom: 30, left: 40 };
    const cw = w - pad.left - pad.right;
    const ch = h - pad.top - pad.bottom;

    ctx.clearRect(0, 0, w, h);

    // Background grid
    ctx.strokeStyle = "rgba(94,255,159,0.08)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = pad.top + (ch / 4) * i;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(pad.left + cw, y);
      ctx.stroke();
    }

    // Y-axis labels
    ctx.fillStyle = "#a8c9bb";
    ctx.font = '11px "JetBrains Mono", monospace';
    ctx.textAlign = "right";
    for (let i = 0; i <= 4; i++) {
      const val = 100 - i * 25;
      const y = pad.top + (ch / 4) * i;
      ctx.fillText(String(val), pad.left - 8, y + 4);
    }

    const scoredItems = items.filter((i) => i.avg_quality_score != null).reverse();
    if (scoredItems.length < 2) {
      ctx.fillStyle = "#a8c9bb";
      ctx.font = "13px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("完成至少2次训练后显示评分趋势", w / 2, h / 2);
      return;
    }

    const n = scoredItems.length;
    const points = scoredItems.map((item, idx) => {
      const x = pad.left + (cw / Math.max(n - 1, 1)) * idx;
      const score = Math.max(0, Math.min(100, item.avg_quality_score));
      const y = pad.top + ch - (ch * score / 100);
      return { x, y, score, item };
    });

    // Gradient fill
    const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + ch);
    grad.addColorStop(0, "rgba(94,255,159,0.3)");
    grad.addColorStop(1, "rgba(94,255,159,0.0)");
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.moveTo(points[0].x, pad.top + ch);
    points.forEach((p) => ctx.lineTo(p.x, p.y));
    ctx.lineTo(points[points.length - 1].x, pad.top + ch);
    ctx.closePath();
    ctx.fill();

    // Line
    ctx.strokeStyle = "#5eff9f";
    ctx.lineWidth = 2;
    ctx.beginPath();
    points.forEach((p, i) => {
      if (i === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    });
    ctx.stroke();

    // Points
    points.forEach((p) => {
      ctx.fillStyle = "#07130f";
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#5eff9f";
      ctx.lineWidth = 2;
      ctx.stroke();
    });

    // X-axis labels (dates)
    ctx.fillStyle = "#a8c9bb";
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.textAlign = "center";
    const labelStep = Math.max(1, Math.floor(n / 6));
    points.forEach((p, i) => {
      if (i % labelStep === 0 || i === n - 1) {
        const dateStr = (p.item.created_at_display || "").slice(5, 10);
        ctx.fillText(dateStr, p.x, h - 8);
      }
    });
  }

  function init() {
    drawCourt();
    drawRadar(state.radarData);
    updateConfigOutput();
    elements.emptyMedia.style.display = "flex";
    elements.frameCanvasWrap.style.display = "none";
    updateCoachContextStatus();
  }

  init();
})();
