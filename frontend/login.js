const loginForm = document.getElementById('login-form');
const loginButton = document.getElementById('login-button');
const errorMessage = document.getElementById('error-message');

const translate = (key, replacements) => {
  if (window.i18n && typeof window.i18n.translate === 'function') {
    return window.i18n.translate(key, replacements);
  }
  return key;
};

let loginButtonState = 'idle';
let lastErrorMessageKey = null;
let lastErrorReplacements;

function updateLoginButton() {
  const key = loginButtonState === 'loading' ? 'login.buttonWorking' : 'login.button';
  loginButton.textContent = translate(key);
}

function showError(messageKey, replacements) {
  lastErrorMessageKey = messageKey;
  lastErrorReplacements = replacements;
  errorMessage.textContent = translate(messageKey, replacements);
  errorMessage.classList.add('show');
}

function hideError() {
  errorMessage.classList.remove('show');
  lastErrorMessageKey = null;
  lastErrorReplacements = undefined;
}

async function checkAuthenticationStatus() {
  try {
    const response = await fetch('/api/auth/check', {
      credentials: 'include'
    });
    const data = await response.json();
    if (data && data.authenticated) {
      window.location.href = '/';
    }
  } catch (error) {
    // Ignore errors, user can still log in
  }
}

function readErrorFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const error = params.get('error');
  if (!error) {
    return;
  }

  if (error === 'teacher_only') {
    showError('login.error.teacherOnly');
    return;
  }

  if (error === 'login_failed') {
    showError('login.error.ssoFailed');
  }
}

async function handleLogin(event) {
  event.preventDefault();
  loginButton.disabled = true;
  loginButtonState = 'loading';
  updateLoginButton();
  hideError();
  window.location.href = '/api/auth/microsoft?redirect=/';
}

function initLoginForm() {
  updateLoginButton();
  checkAuthenticationStatus();
  readErrorFromUrl();

  loginForm.addEventListener('submit', handleLogin);
}

function handleLanguageChange() {
  updateLoginButton();
  if (lastErrorMessageKey) {
    errorMessage.textContent = translate(lastErrorMessageKey, lastErrorReplacements);
  }
}

document.addEventListener('i18n:languagechange', handleLanguageChange);

document.addEventListener('DOMContentLoaded', initLoginForm);
