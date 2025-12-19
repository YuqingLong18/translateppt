(function () {
  const translations = {
    zh: {
      'title.main': 'DocTranslate 文档翻译',
      'title.login': 'DocTranslate 登录',
      'subtitle.main': '无缝文档翻译服务。',
      'auth.checking': '正在检查登录状态...',
      'auth.logout': '← 退出登录',
      'upload.heading': '上传',
      'upload.cta': '拖拽文件到此或点击选择',
      'upload.supported': '支持 .pptx, .docx, .xlsx',
      'settings.heading': '设置',
      'form.source': '源语言',
      'form.target': '目标语言',
      'form.font': '字体（可选）',
      'form.fontPlaceholder': '默认',
      'form.sideBySide': '并排翻译（源文 | 译文，逐段对齐）',
      'button.translate': '开始翻译',
      'status.ready': '准备好翻译。',
      'status.waitingUpload': '等待上传文件。',
      'status.filesAlreadyQueued': '所选文件已在队列中。',
      'status.filesQueued': '{count} 个文件已加入队列。配置设置后点击“开始翻译”。',
      'status.addFile': '请先添加至少一个文件。',
      'status.processingQueue': '已有队列正在处理，请稍候。',
      'status.chooseTarget': '请选择目标语言以继续。',
      'status.finishedFile': '{name} 已完成。',
      'status.skipFile': '已跳过 {name}：{reason}。继续处理...',
      'status.queueWithErrors': '队列处理完成，但存在错误。查看下方详情。',
      'status.queueSuccess': '所有排队的文件均已成功翻译。',
      'status.queueEmpty': '没有文件被翻译。',
      'status.languagesError': '无法加载语言列表。刷新页面后再试。',
      'progress.uploading': '正在上传 {name} ({current}/{total})...',
      'progress.translating': '正在翻译 {name} ({current}/{total})...',
      'progress.default': '处理中...',
      'card.completed': '已完成',
      'downloads.link': '下载',
      'queue.remove': '移除',
      'failures.heading': '无法翻译的文件：',
      'common.translationFailed': '翻译失败',
      'login.subheading': '登录以继续',
      'login.usernameLabel': '用户名',
      'login.usernamePlaceholder': '请输入用户名',
      'login.passwordLabel': '密码',
      'login.passwordPlaceholder': '请输入密码',
      'login.button': '登录',
      'login.buttonWorking': '正在登录...',
      'login.footer': '文档翻译服务',
      'login.error.missingFields': '请输入用户名和密码',
      'login.error.connection': '网络连接错误，请重试。',
      'login.error.invalid': '用户名或密码错误'
    },
    en: {
      'title.main': 'DocTranslate - Document Translator',
      'title.login': 'Login - Document Translator',
      'subtitle.main': 'Seamless document translation.',
      'auth.checking': 'Checking authentication...',
      'auth.logout': '← Logout',
      'upload.heading': 'Upload',
      'upload.cta': 'Drag files here or click to browse',
      'upload.supported': 'Supports .pptx, .docx, .xlsx',
      'settings.heading': 'Settings',
      'form.source': 'Source Language',
      'form.target': 'Target Language',
      'form.font': 'Font (Optional)',
      'form.fontPlaceholder': 'Default',
      'form.sideBySide': 'Side-by-side translation (source | translation, aligned by paragraph)',
      'button.translate': 'Start Translation',
      'status.ready': 'Ready to translate.',
      'status.waitingUpload': 'Waiting for file upload.',
      'status.filesAlreadyQueued': 'Selected files are already queued.',
      'status.filesQueued': '{count} file{suffix} queued. Configure settings and click Translate.',
      'status.addFile': 'Add at least one file to the queue before translating.',
      'status.processingQueue': 'A queue is already processing. Please wait.',
      'status.chooseTarget': 'Choose a target language to continue.',
      'status.finishedFile': 'Finished {name}.',
      'status.skipFile': 'Skipped {name}: {reason}. Continuing...',
      'status.queueWithErrors': 'Queue finished with some errors. See details below.',
      'status.queueSuccess': 'All queued files translated successfully.',
      'status.queueEmpty': 'No files were translated.',
      'status.languagesError': 'Unable to load languages. Refresh the page and try again.',
      'progress.uploading': 'Uploading {name} ({current}/{total})...',
      'progress.translating': 'Translating {name} ({current}/{total})...',
      'progress.default': 'Processing...',
      'card.completed': 'Completed',
      'downloads.link': 'Download',
      'queue.remove': 'Remove',
      'failures.heading': 'Unable to translate:',
      'common.translationFailed': 'Translation failed',
      'login.subheading': 'Sign in to continue',
      'login.usernameLabel': 'Username',
      'login.usernamePlaceholder': 'Enter your username',
      'login.passwordLabel': 'Password',
      'login.passwordPlaceholder': 'Enter your password',
      'login.button': 'Sign In',
      'login.buttonWorking': 'Signing in...',
      'login.footer': 'Document Translation Service',
      'login.error.missingFields': 'Please enter both username and password',
      'login.error.connection': 'Connection error. Please try again.',
      'login.error.invalid': 'Invalid username or password'
    }
  };

  const storageKey = 'docTranslateLanguage';
  let currentLanguage = 'zh';
  try {
    const saved = localStorage.getItem(storageKey);
    if (saved && translations[saved]) {
      currentLanguage = saved;
    }
  } catch (error) {
    currentLanguage = 'zh';
  }

  document.documentElement.lang = currentLanguage;

  function format(template, replacements = {}) {
    return template.replace(/\{(\w+)\}/g, (_, token) => {
      return Object.prototype.hasOwnProperty.call(replacements, token)
        ? replacements[token]
        : '';
    });
  }

  function translate(key, replacements) {
    if (!key) return '';
    const table = translations[currentLanguage] || {};
    const template = table[key];
    if (!template) {
      return key;
    }
    return format(template, replacements);
  }

  function applyStaticTranslations(root = document) {
    const elements = root.querySelectorAll('[data-i18n]');
    elements.forEach((element) => {
      const key = element.getAttribute('data-i18n');
      if (!key) return;
      const attr = element.getAttribute('data-i18n-attr');
      const value = translate(key);
      if (attr) {
        element.setAttribute(attr, value);
      } else {
        element.textContent = value;
      }
    });
  }

  function updateToggleState(root = document) {
    const toggles = root.querySelectorAll('[data-language-toggle]');
    toggles.forEach((toggle) => {
      const buttons = toggle.querySelectorAll('[data-language-option]');
      buttons.forEach((button) => {
        const lang = button.getAttribute('data-language-option');
        const isActive = lang === currentLanguage;
        button.classList.toggle('active', isActive);
        button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
      });
    });
  }

  function initLanguageToggles(root = document) {
    const toggles = root.querySelectorAll('[data-language-toggle]');
    toggles.forEach((toggle) => {
      if (toggle.dataset.languageToggleBound) {
        return;
      }
      toggle.dataset.languageToggleBound = 'true';
      toggle.addEventListener('click', (event) => {
        const button = event.target.closest('[data-language-option]');
        if (!button) return;
        const lang = button.getAttribute('data-language-option');
        setLanguage(lang);
      });
    });
    updateToggleState(root);
  }

  function setLanguage(lang, options = {}) {
    if (!translations[lang]) return;
    const { force = false, skipStorage = false } = options;
    const changed = lang !== currentLanguage;
    currentLanguage = lang;
    document.documentElement.lang = lang;
    applyStaticTranslations();
    updateToggleState();
    if (!skipStorage) {
      try {
        localStorage.setItem(storageKey, lang);
      } catch (error) {
        // Ignore storage errors
      }
    }
    if (force || changed) {
      document.dispatchEvent(
        new CustomEvent('i18n:languagechange', { detail: { lang } })
      );
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    applyStaticTranslations();
    initLanguageToggles();
    setLanguage(currentLanguage, { force: true, skipStorage: true });
  });

  window.i18n = {
    translate,
    setLanguage,
    getLanguage() {
      return currentLanguage;
    },
    applyStaticTranslations,
    initLanguageToggles
  };
})();
