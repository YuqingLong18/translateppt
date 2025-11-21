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

const fontInput = document.getElementById('font-name');
let fileQueue = [];
let processingQueue = false;

async function init() {
  await checkAuthentication();
  await fetchLanguages();
  attachEventListeners();
  setStatus('Waiting for file upload.');
}

async function checkAuthentication() {
  try {
    const response = await fetch('/api/user', {
      credentials: 'include'
    });

    const userStatus = document.getElementById('user-status');
    const backToNexus = document.getElementById('back-to-nexus');

    if (response.ok) {
      const data = await response.json();
      if (data.authenticated && data.username) {
        userStatus.textContent = `👤 ${data.username}`;
        userStatus.style.color = '#10b981';
        backToNexus.textContent = '← Logout';
        backToNexus.href = '#';
        backToNexus.onclick = async (e) => {
          e.preventDefault();
          await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include'
          });
          window.location.href = '/login';
        };
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
        setStatus('Waiting for file upload.');
      }
    }
  });
}

function addFilesToQueue(files) {
  const uniqueFiles = files.filter(
    file => !fileQueue.some(queued => isSameFile(queued, file))
  );

  if (!uniqueFiles.length) {
    setStatus('Selected files are already queued.');
    return;
  }

  fileQueue = fileQueue.concat(uniqueFiles);
  renderQueue();
  const count = fileQueue.length;
  setStatus(`${count} file${count === 1 ? '' : 's'} queued. Configure settings and click Translate.`);
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
    removeBtn.textContent = 'Remove';

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
    setStatus('Unable to load languages. Refresh the page and try again.');
  }
}

async function handleTranslate(event) {
  event.preventDefault();

  if (!fileQueue.length && !processingQueue) {
    setStatus('Add at least one file to the queue before translating.');
    return;
  }
  if (processingQueue) {
    setStatus('A queue is already processing. Please wait.');
    return;
  }

  if (!targetSelect.value) {
    setStatus('Choose a target language to continue.');
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
      showProgress(`Uploading ${file.name} (${index + 1}/${queuedFiles.length})...`);
      const uploadResponse = await uploadFile(file);
      showProgress(`Translating ${file.name} (${index + 1}/${queuedFiles.length})...`);
      const translateResponse = await translateFile(uploadResponse.file_id);
      appendDownloadLink(translateResponse, file.name);
      setStatus(`Finished ${file.name}.`);
    } catch (error) {
      console.error(error);
      failures.push({ name: file.name, reason: error.message || 'Translation failed' });
      setStatus(`Skipped ${file.name}: ${error.message || 'Translation failed'}. Continuing...`);
    }
  }

  hideProgress();
  translateBtn.disabled = false;
  processingQueue = false;

  if (failures.length) {
    showFailureSummary(failures);
    setStatus('Queue finished with some errors. See details below.');
  } else if (downloadList.children.length) {
    clearFailureSummary();
    setStatus('All queued files translated successfully.');
  } else {
    clearFailureSummary();
    setStatus('No files were translated.');
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
  const payload = {
    file_id: fileId,
    source_lang: sourceSelect.value,
    target_lang: targetSelect.value,
    font: fontInput.value,
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
    throw new Error(error || 'Translation failed');
  }

  return response.json();
}

function showProgress(message) {
  progressIndicator.classList.remove('hidden');
  progressText.textContent = message;
  setStatus(message);
}

function hideProgress() {
  progressIndicator.classList.add('hidden');
}

function resetDownloadSection() {
  downloadList.innerHTML = '';
  downloadCard.classList.add('hidden');
  clearFailureSummary();
}

function appendDownloadLink({ download_url, filename, target_lang }, originalName) {
  downloadCard.classList.remove('hidden');
  const item = document.createElement('li');
  item.className = 'download-item';

  const meta = document.createElement('div');
  meta.className = 'download-meta';

  const nameEl = document.createElement('span');
  nameEl.className = 'download-filename';
  nameEl.textContent = originalName || filename;

  const langEl = document.createElement('span');
  langEl.className = 'file-size';
  langEl.textContent = target_lang ? `→ ${target_lang.toUpperCase()}` : '';

  meta.append(nameEl, langEl);

  const link = document.createElement('a');
  link.href = download_url;
  link.download = filename;
  link.textContent = 'Download';

  item.append(meta, link);
  downloadList.appendChild(item);
}

function showFailureSummary(failures) {
  if (!failures.length) {
    clearFailureSummary();
    return;
  }
  downloadCard.classList.remove('hidden');
  failedSummary.innerHTML = '';
  failedSummary.classList.remove('hidden');

  const heading = document.createElement('div');
  heading.textContent = 'Unable to translate:';
  failedSummary.appendChild(heading);

  const list = document.createElement('ul');
  failures.forEach(({ name, reason }) => {
    const item = document.createElement('li');
    item.textContent = `${name} — ${reason}`;
    list.appendChild(item);
  });
  failedSummary.appendChild(list);
}

function clearFailureSummary() {
  failedSummary.classList.add('hidden');
  failedSummary.textContent = '';
}

function setStatus(message) {
  statusMessage.textContent = message;
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
    return data?.message || data?.error || response.statusText;
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
