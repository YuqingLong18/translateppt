const sourceSelect = document.getElementById('source-lang');
const targetSelect = document.getElementById('target-lang');
const fileInput = document.getElementById('file-input');
const dropZone = document.getElementById('drop-zone');
const fileInfo = document.getElementById('file-info');
const statusMessage = document.getElementById('status-message');
const progressIndicator = document.getElementById('progress-indicator');
const progressText = document.getElementById('progress-text');
const translateForm = document.getElementById('translation-form');
const translateBtn = document.getElementById('translate-btn');
const downloadCard = document.getElementById('download-card');
const fileQueueList = document.getElementById('file-queue');
const downloadList = document.getElementById('download-list');
const failedSummary = document.getElementById('failed-summary');
const userStatus = document.getElementById('user-status');
const backToNexus = document.getElementById('back-to-nexus');

const fontInput = document.getElementById('font-name');
let fileQueue = [];
let processingQueue = false;
const completedDownloads = [];
let failureDetails = [];
let lastStatusMessage = { key: 'status.ready', replacements: undefined };
let lastProgressMessage = null;
let currentUsername = '';
let pendingUserStatusKey = 'auth.checking';

const translateText = (key, replacements) => {
  if (window.i18n && typeof window.i18n.translate === 'function') {
    return window.i18n.translate(key, replacements);
  }
  return key;
};

updateAuthDisplays();

async function init() {
  setStatus('status.waitingUpload');
  attachEventListeners();
  await checkAuthentication();
  await fetchLanguages();
}

async function checkAuthentication() {
  try {
    const response = await fetch('/api/user', {
      credentials: 'include'
    });

    if (response.ok) {
      const data = await response.json();
      if (data.authenticated && data.username) {
        currentUsername = data.display_name || data.username || data.email || '';
        pendingUserStatusKey = null;
        updateAuthDisplays();
        backToNexus.href = '/api/auth/logout';
        backToNexus.onclick = null;
      } else {
        window.location.href = '/login';
      }
    } else {
      window.location.href = '/login';
    }
  } catch (error) {
    console.error('Auth check failed:', error);
    window.location.href = '/login';
  }
}

document.addEventListener('DOMContentLoaded', init);

document.addEventListener('i18n:languagechange', () => {
  renderQueue();
  renderDownloadList();
  renderFailureSummary();
  refreshStatus();
  refreshProgress();
  updateAuthDisplays();
});

function attachEventListeners() {
  fileInput.addEventListener('change', event => {
    const files = Array.from(event.target.files || []);
    if (files.length) {
      addFilesToQueue(files);
      fileInput.value = '';
    }
  });

  ['dragover', 'dragenter'].forEach(eventName => {
    dropZone.addEventListener(eventName, event => {
      event.preventDefault();
      dropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, event => {
      event.preventDefault();
      dropZone.classList.remove('dragover');
    });
  });

  dropZone.addEventListener('drop', event => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files || []);
    if (files.length) {
      addFilesToQueue(files);
    }
  });

  translateForm.addEventListener('submit', handleTranslate);
  targetSelect.addEventListener('change', handleTargetLanguageChange);
  fontInput.addEventListener('input', () => {
    if (fontInput.dataset.autoAssigned) {
      delete fontInput.dataset.autoAssigned;
    }
  });


  fileQueueList.addEventListener('click', event => {
    const button = event.target.closest('[data-remove-index]');
    if (!button || processingQueue) return;
    const index = Number(button.dataset.removeIndex);
    if (!Number.isNaN(index)) {
      fileQueue.splice(index, 1);
      renderQueue();
      if (!fileQueue.length) {
        setStatus('status.waitingUpload');
      }
    }
  });
}

function addFilesToQueue(files) {
  const uniqueFiles = files.filter(
    file => !fileQueue.some(queued => isSameFile(queued, file))
  );

  if (!uniqueFiles.length) {
    setStatus('status.filesAlreadyQueued');
    return;
  }

  fileQueue = fileQueue.concat(uniqueFiles);
  renderQueue();
  const count = fileQueue.length;
  const suffix = count === 1 ? '' : 's';
  setStatus('status.filesQueued', { count, suffix });
}

function isSameFile(fileA, fileB) {
  return fileA.name === fileB.name && fileA.size === fileB.size && fileA.lastModified === fileB.lastModified;
}

function renderQueue() {
  if (!fileQueue.length) {
    fileInfo.classList.add('hidden');
    fileQueueList.innerHTML = '';
    return;
  }

  fileInfo.classList.remove('hidden');
  fileQueueList.innerHTML = '';
  fileQueue.forEach((file, index) => {
    const li = document.createElement('li');
    li.className = 'file-queue-item';

    const meta = document.createElement('div');
    meta.className = 'file-meta';

    const nameEl = document.createElement('span');
    nameEl.textContent = file.name;

    const sizeEl = document.createElement('span');
    sizeEl.className = 'file-size';
    sizeEl.textContent = formatBytes(file.size);

    meta.append(nameEl, sizeEl);

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.dataset.removeIndex = String(index);
    removeBtn.textContent = translateText('queue.remove');

    li.append(meta, removeBtn);
    fileQueueList.appendChild(li);
  });
}
async function fetchLanguages() {
  try {
    const response = await fetch('/languages');
    if (!response.ok) throw new Error('Failed to load languages');
    const languages = await response.json();

    sourceSelect.innerHTML = '';
    targetSelect.innerHTML = '';

    languages.forEach(({ code, label }) => {
      if (code === 'auto') {
        sourceSelect.add(new Option(label, code, true, true));
      } else {
        sourceSelect.add(new Option(label, code));
        targetSelect.add(new Option(label, code));
      }
    });

    if (targetSelect.options.length > 0) {
      targetSelect.options[0].selected = true;
    }
    handleTargetLanguageChange();
  } catch (error) {
    console.error(error);
    setStatus('status.languagesError');
  }
}

async function handleTranslate(event) {
  event.preventDefault();

  if (!fileQueue.length && !processingQueue) {
    setStatus('status.addFile');
    return;
  }
  if (processingQueue) {
    setStatus('status.processingQueue');
    return;
  }

  if (!targetSelect.value) {
    setStatus('status.chooseTarget');
    return;
  }

  const queuedFiles = [...fileQueue];
  fileQueue = [];
  renderQueue();
  resetDownloadSection();
  translateBtn.disabled = true;
  processingQueue = true;

  const failures = [];
  for (let index = 0; index < queuedFiles.length; index += 1) {
    const file = queuedFiles[index];
    try {
      showProgress('progress.uploading', {
        name: file.name,
        current: index + 1,
        total: queuedFiles.length
      });
      const uploadResponse = await uploadFile(file);
      showProgress('progress.translating', {
        name: file.name,
        current: index + 1,
        total: queuedFiles.length
      });
      const translateResponse = await translateFile(uploadResponse.file_id);
      appendDownloadLink(translateResponse, file.name);
      setStatus('status.finishedFile', { name: file.name });
    } catch (error) {
      console.error(error);
      const reason = error.message || translateText('common.translationFailed');
      failures.push({ name: file.name, reason });
      setStatus('status.skipFile', { name: file.name, reason });
    }
  }

  hideProgress();
  translateBtn.disabled = false;
  processingQueue = false;

  if (failures.length) {
    showFailureSummary(failures);
    setStatus('status.queueWithErrors');
  } else if (completedDownloads.length) {
    clearFailureSummary();
    setStatus('status.queueSuccess');
  } else {
    clearFailureSummary();
    setStatus('status.queueEmpty');
  }
}

async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/upload', {
    method: 'POST',
    body: formData,
    credentials: 'include'
  });

  if (response.status === 401 || response.status === 403) {
    const data = await response.json();
    if (data.redirect) {
      window.location.href = data.redirect;
    } else {
      window.location.href = '/login';
    }
    throw new Error('Authentication required');
  }

  if (!response.ok) {
    const error = await parseError(response);
    throw new Error(error || 'Upload failed');
  }

  return response.json();
}

async function translateFile(fileId) {
  const sideBySideCheckbox = document.getElementById('side-by-side');
  const payload = {
    file_id: fileId,
    source_lang: sourceSelect.value,
    target_lang: targetSelect.value,
    font: fontInput.value,
    side_by_side: sideBySideCheckbox.checked || false,
  };

  const response = await fetch('/translate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(payload),
  });

  if (response.status === 401 || response.status === 403) {
    const data = await response.json();
    if (data.redirect) {
      window.location.href = data.redirect;
    } else {
      window.location.href = '/login';
    }
    throw new Error('Authentication required');
  }

  if (!response.ok) {
    const error = await parseError(response);
    // Provide more context for common errors
    if (response.status === 502) {
      throw new Error(`Translation service error: ${error || 'The server encountered an error processing your request. Please try again.'}`);
    }
    throw new Error(error || 'Translation failed');
  }

  return response.json();
}

function showProgress(messageKey, replacements) {
  lastProgressMessage = { key: messageKey, replacements };
  progressIndicator.classList.remove('hidden');
  refreshProgress();
  setStatus(messageKey, replacements);
}

function hideProgress() {
  progressIndicator.classList.add('hidden');
  lastProgressMessage = null;
  refreshProgress();
}

function resetDownloadSection() {
  completedDownloads.length = 0;
  downloadList.innerHTML = '';
  failureDetails = [];
  renderDownloadList();
  renderFailureSummary();
  downloadCard.classList.add('hidden');
}

function appendDownloadLink({ download_url, filename, target_lang }, originalName) {
  completedDownloads.push({
    download_url,
    filename,
    target_lang,
    originalName: originalName || filename
  });
  renderDownloadList();
}

function renderDownloadList() {
  downloadList.innerHTML = '';
  completedDownloads.forEach(({ download_url, filename, target_lang, originalName }) => {
    const item = document.createElement('li');
    item.className = 'download-item';

    const meta = document.createElement('div');
    meta.className = 'download-meta';

    const nameEl = document.createElement('span');
    nameEl.className = 'download-filename';
    nameEl.textContent = originalName;

    const langEl = document.createElement('span');
    langEl.className = 'file-size';
    langEl.textContent = target_lang ? `→ ${target_lang.toUpperCase()}` : '';

    meta.append(nameEl, langEl);

    const link = document.createElement('a');
    link.href = download_url;
    link.download = filename;
    link.textContent = translateText('downloads.link');

    item.append(meta, link);
    downloadList.appendChild(item);
  });

  if (completedDownloads.length) {
    downloadCard.classList.remove('hidden');
  } else if (!failureDetails.length) {
    downloadCard.classList.add('hidden');
  }
}

function showFailureSummary(failures) {
  failureDetails = failures.slice();
  renderFailureSummary();
}

function renderFailureSummary() {
  if (!failureDetails.length) {
    failedSummary.classList.add('hidden');
    failedSummary.textContent = '';
    if (!completedDownloads.length) {
      downloadCard.classList.add('hidden');
    }
    return;
  }

  downloadCard.classList.remove('hidden');
  failedSummary.innerHTML = '';
  failedSummary.classList.remove('hidden');

  const heading = document.createElement('div');
  heading.textContent = translateText('failures.heading');
  failedSummary.appendChild(heading);

  const list = document.createElement('ul');
  failureDetails.forEach(({ name, reason }) => {
    const item = document.createElement('li');
    item.textContent = `${name} — ${reason}`;
    list.appendChild(item);
  });
  failedSummary.appendChild(list);
}

function clearFailureSummary() {
  failureDetails = [];
  renderFailureSummary();
}

function setStatus(messageKey, replacements) {
  lastStatusMessage = { key: messageKey, replacements };
  refreshStatus();
}

function refreshStatus() {
  if (!lastStatusMessage || !lastStatusMessage.key) return;
  statusMessage.textContent = translateText(lastStatusMessage.key, lastStatusMessage.replacements);
}

function refreshProgress() {
  if (lastProgressMessage) {
    progressText.textContent = translateText(lastProgressMessage.key, lastProgressMessage.replacements);
  } else {
    progressText.textContent = translateText('progress.default');
  }
}

function updateAuthDisplays() {
  if (userStatus) {
    if (currentUsername) {
      userStatus.textContent = `👤 ${currentUsername}`;
      userStatus.style.color = '#10b981';
    } else {
      userStatus.textContent = translateText(pendingUserStatusKey || 'auth.checking');
      userStatus.style.color = '';
    }
  }

  if (backToNexus) {
    backToNexus.textContent = translateText('auth.logout');
  }
}

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const size = bytes / Math.pow(1024, exponent);
  return `${size.toFixed(1)} ${units[exponent]}`;
}

async function parseError(response) {
  try {
    const data = await response.json();
    // Flask abort() uses 'description' field for error messages
    return data?.description || data?.message || data?.error || response.statusText;
  } catch (error) {
    return response.statusText;
  }
}

function handleTargetLanguageChange() {
  if (targetSelect.value === 'en') {
    if (!fontInput.value) {
      fontInput.value = 'Arial';
      fontInput.dataset.autoAssigned = 'true';
    }
  } else if (fontInput.dataset.autoAssigned === 'true') {
    fontInput.value = '';
    delete fontInput.dataset.autoAssigned;
  }
}
