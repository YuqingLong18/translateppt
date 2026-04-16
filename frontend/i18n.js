(function () {
  const translations = {
    zh: {
      'title.main': 'DocTranslate 文档翻译',
      'title.login': 'DocTranslate 登录',
      'subtitle.main': '无缝文档翻译服务。',
      'auth.checking': '正在检查登录状态...',
      'auth.backToNexus': '← 返回 THIS Nexus',
      'auth.logout': '← 退出登录',
      'upload.heading': '上传',
      'upload.cta': '拖拽文件到此或点击选择',
      'upload.supported': '支持 .pptx, .docx, .xlsx',
      'settings.heading': '设置',
      'form.source': '源语言',
      'form.target': '目标语言',
      'form.font': '字体（可选）',
      'form.fontPlaceholder': '默认',
      'form.sideBySide': 'PowerPoint 并排翻译（源文 | 译文，逐段对齐）',
      'form.xlsxModeLabel': 'Excel 翻译方式',
      'form.xlsxModeInPlace': '直接替换原单元格',
      'form.xlsxModeInPlaceCopy': '在原工作表中写回翻译结果。',
      'form.xlsxModeNewSheet': '保留原表并新增翻译表',
      'form.xlsxModeNewSheetCopy': '为每个工作表复制一个翻译版本，放在原表旁边。',
      'button.translate': '开始翻译',
      'status.ready': '准备好翻译。',
      'status.waitingUpload': '等待上传文件。',
      'status.filesAlreadyQueued': '所选文件已在队列中。',
      'status.filesQueued': '{count} 个文件已加入队列。配置设置后点击“开始翻译”。',
      'status.addFile': '请先添加至少一个文件。',
      'status.processingQueue': '已有队列正在处理，请稍候。',
      'status.chooseTarget': '请选择目标语言以继续。',
      'status.translationHint': '去奖励自己一杯咖啡，稍后回来看看结果。',
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
      'login.subheading': '教师请使用 Microsoft SSO 继续',
      'login.teacherOnlyNote': '本应用仅供教师使用。请使用 THIS Nexus 的 Microsoft 账号进入 translate.thisnexus.cn。',
      'login.button': '使用 Microsoft 继续',
      'login.buttonWorking': '正在跳转...',
      'login.footer': '文档翻译服务',
      'login.error.connection': '网络连接错误，请重试。',
      'login.error.teacherOnly': '该 Microsoft 账号无权使用文档翻译服务。',
      'login.error.ssoFailed': 'Microsoft 登录失败，请重试。',
      'login.error.ssoRequired': '请使用 Microsoft SSO 登录。'
    },
    en: {
      'title.main': 'DocTranslate - Document Translator',
      'title.login': 'Login - Document Translator',
      'subtitle.main': 'Seamless document translation.',
      'auth.checking': 'Checking authentication...',
      'auth.backToNexus': '← Back to THIS Nexus',
      'auth.logout': '← Logout',
      'upload.heading': 'Upload',
      'upload.cta': 'Drag files here or click to browse',
      'upload.supported': 'Supports .pptx, .docx, .xlsx',
      'settings.heading': 'Settings',
      'form.source': 'Source Language',
      'form.target': 'Target Language',
      'form.font': 'Font (Optional)',
      'form.fontPlaceholder': 'Default',
      'form.sideBySide': 'PowerPoint side-by-side translation (source | translation, aligned by paragraph)',
      'form.xlsxModeLabel': 'Excel Translation Mode',
      'form.xlsxModeInPlace': 'Replace cells in place',
      'form.xlsxModeInPlaceCopy': 'Write translations back into the original worksheets.',
      'form.xlsxModeNewSheet': 'Keep originals and add translated sheets',
      'form.xlsxModeNewSheetCopy': 'Duplicate each worksheet and place the translated copy next to the original.',
      'button.translate': 'Start Translation',
      'status.ready': 'Ready to translate.',
      'status.waitingUpload': 'Waiting for file upload.',
      'status.filesAlreadyQueued': 'Selected files are already queued.',
      'status.filesQueued': '{count} file{suffix} queued. Configure settings and click Translate.',
      'status.addFile': 'Add at least one file to the queue before translating.',
      'status.processingQueue': 'A queue is already processing. Please wait.',
      'status.chooseTarget': 'Choose a target language to continue.',
      'status.translationHint': 'Go treat yourself with a coffee, then come back to check the result.',
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
      'login.subheading': 'Teachers sign in with Microsoft SSO',
      'login.teacherOnlyNote': 'This app is for teachers only. Use your THIS Nexus Microsoft account to open translate.thisnexus.cn.',
      'login.button': 'Continue with Microsoft',
      'login.buttonWorking': 'Redirecting...',
      'login.footer': 'Document Translation Service',
      'login.error.connection': 'Connection error. Please try again.',
      'login.error.teacherOnly': 'This Microsoft account is not allowed to use DocTranslate.',
      'login.error.ssoFailed': 'Microsoft sign-in failed. Please try again.',
      'login.error.ssoRequired': 'Please sign in with Microsoft SSO.'
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
