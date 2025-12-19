const loginForm = document.getElementById('login-form');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
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

async function handleLogin(event) {
  event.preventDefault();

  const username = usernameInput.value.trim();
  const password = passwordInput.value;

  if (!username || !password) {
    showError('login.error.missingFields');
    return;
  }

  loginButton.disabled = true;
  loginButtonState = 'loading';
  updateLoginButton();
  hideError();

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (response.ok && data.success) {
      window.location.href = '/';
      return;
    }

    showError(data.error || 'login.error.invalid');
    loginButton.disabled = false;
    loginButtonState = 'idle';
    updateLoginButton();
  } catch (error) {
    showError('login.error.connection');
    loginButton.disabled = false;
    loginButtonState = 'idle';
    updateLoginButton();
  }
}

function initLoginForm() {
  updateLoginButton();
  checkAuthenticationStatus();

  loginForm.addEventListener('submit', handleLogin);

  [usernameInput, passwordInput].forEach((input) => {
    input.addEventListener('keypress', (event) => {
      if (event.key === 'Enter') {
        loginForm.requestSubmit();
      }
    });
  });
}

function handleLanguageChange() {
  updateLoginButton();
  if (lastErrorMessageKey) {
    errorMessage.textContent = translate(lastErrorMessageKey, lastErrorReplacements);
  }
}

document.addEventListener('i18n:languagechange', handleLanguageChange);

document.addEventListener('DOMContentLoaded', initLoginForm);
