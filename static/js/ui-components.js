/**
 * ui-components.js - Composants UI réutilisables
 * À importer sur toutes les pages : <script src="/static/js/ui-components.js"></script>
 */

// ========== TOAST NOTIFICATIONS ==========
class ToastManager {
  constructor() {
    this.container = this.createContainer();
  }

  createContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  show(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');

    this.container.appendChild(toast);

    // Auto-remove après duration
    if (duration > 0) {
      setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => this.container.removeChild(toast), 300);
      }, duration);
    }

    return toast;
  }

  success(message, duration = 3000) {
    return this.show(message, 'success', duration);
  }

  error(message, duration = 5000) {
    return this.show(message, 'error', duration);
  }

  warning(message, duration = 4000) {
    return this.show(message, 'warning', duration);
  }

  info(message, duration = 3000) {
    return this.show(message, 'info', duration);
  }
}

// Singleton global
window.toast = new ToastManager();

// ========== CONNECTION STATUS INDICATOR ==========
class ConnectionStatus {
  constructor() {
    this.connected = false;
    this.createIndicator();
  }

  createIndicator() {
    let status = document.getElementById('connection-status');
    if (!status) {
      status = document.createElement('div');
      status.id = 'connection-status';
      status.innerHTML = `
        <span id="status-indicator" class="disconnected">●</span>
        <span id="status-text">Déconnecté</span>
      `;
      document.body.appendChild(status);
    }
    this.statusEl = status;
  }

  setConnected(connected) {
    this.connected = connected;
    const indicator = document.getElementById('status-indicator');
    const text = document.getElementById('status-text');

    if (connected) {
      indicator.className = 'connected';
      text.textContent = 'Connecté';
      this.statusEl.style.background = 'rgba(40, 167, 69, 0.1)';
      this.statusEl.style.color = '#28a745';
    } else {
      indicator.className = 'disconnected';
      text.textContent = 'Déconnecté';
      this.statusEl.style.background = 'rgba(220, 53, 69, 0.1)';
      this.statusEl.style.color = '#dc3545';
    }
  }

  isConnected() {
    return this.connected;
  }
}

// Singleton global
window.connectionStatus = new ConnectionStatus();

// ========== MODAL DIALOG ==========
class Modal {
  constructor(title, content, options = {}) {
    this.title = title;
    this.content = content;
    this.options = {
      size: 'md', // sm, md, lg
      closeable: true,
      actions: [], // [{label, color, callback}]
      ...options
    };
    this.element = null;
  }

  create() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    
    const sizeClass = `modal-${this.options.size}`;
    const content = document.createElement('div');
    content.className = `modal ${sizeClass}`;

    // Header
    const header = document.createElement('div');
    header.className = 'modal-header';
    header.innerHTML = `<h2>${this.title}</h2>`;
    
    if (this.options.closeable) {
      const closeBtn = document.createElement('button');
      closeBtn.innerHTML = '×';
      closeBtn.className = 'modal-close';
      closeBtn.onclick = () => this.close();
      header.appendChild(closeBtn);
    }

    // Body
    const body = document.createElement('div');
    body.className = 'modal-body';
    if (typeof this.content === 'string') {
      body.innerHTML = this.content;
    } else {
      body.appendChild(this.content);
    }

    // Footer avec actions
    const footer = document.createElement('div');
    footer.className = 'modal-footer';
    
    this.options.actions.forEach(action => {
      const btn = document.createElement('button');
      btn.textContent = action.label;
      btn.className = `btn btn-${action.color || 'secondary'}`;
      btn.onclick = () => {
        if (action.callback) action.callback();
        this.close();
      };
      footer.appendChild(btn);
    });

    // Fermer si pas d'action
    if (this.options.actions.length === 0 && this.options.closeable) {
      const closeBtn = document.createElement('button');
      closeBtn.textContent = 'Fermer';
      closeBtn.className = 'btn btn-secondary';
      closeBtn.onclick = () => this.close();
      footer.appendChild(closeBtn);
    }

    content.appendChild(header);
    content.appendChild(body);
    content.appendChild(footer);
    modal.appendChild(content);

    modal.onclick = (e) => {
      if (e.target === modal) this.close();
    };

    this.element = modal;
    return modal;
  }

  show() {
    if (!this.element) this.create();
    document.body.appendChild(this.element);
    document.body.style.overflow = 'hidden';
  }

  close() {
    if (this.element && this.element.parentNode) {
      this.element.parentNode.removeChild(this.element);
      document.body.style.overflow = 'auto';
    }
  }

  static confirm(title, message, onConfirm) {
    const modal = new Modal(title, message, {
      actions: [
        { label: 'Annuler', color: 'secondary' },
        { label: 'Confirmer', color: 'danger', callback: onConfirm }
      ]
    });
    modal.show();
  }

  static alert(title, message) {
    const modal = new Modal(title, message, {
      actions: [
        { label: 'OK', color: 'primary' }
      ]
    });
    modal.show();
  }
}

// ========== DARK MODE TOGGLE ==========
class DarkModeToggle {
  constructor(buttonSelector = null) {
    this.isDark = this.loadPreference();
    this.button = buttonSelector ? document.querySelector(buttonSelector) : null;
    
    // Appliquer préférence initiale
    if (this.isDark) {
      document.body.classList.add('dark');
      if (this.button) this.button.textContent = '☀️';
    }

    // Écouter préférence système
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      this.toggle(!this.loadPreference());
    });

    // Configurer bouton si fourni
    if (this.button) {
      this.button.onclick = () => this.toggle();
    }
  }

  toggle(force = null) {
    this.isDark = force !== null ? force : !this.isDark;
    if (this.isDark) {
      document.body.classList.add('dark');
      if (this.button) this.button.textContent = '☀️';
    } else {
      document.body.classList.remove('dark');
      if (this.button) this.button.textContent = '🌙';
    }
    this.savePreference();
  }

  loadPreference() {
    const saved = localStorage.getItem('darkMode');
    if (saved !== null) return saved === 'true';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  savePreference() {
    localStorage.setItem('darkMode', this.isDark);
  }
}

// ========== SKELETON LOADER ==========
class SkeletonLoader {
  static createItem(height = '20px') {
    const div = document.createElement('div');
    div.className = 'skeleton';
    div.style.height = height;
    div.style.marginBottom = '8px';
    return div;
  }

  static fill(container, count = 3, height = '20px') {
    if (typeof container === 'string') {
      container = document.querySelector(container);
    }
    container.innerHTML = '';
    for (let i = 0; i < count; i++) {
      container.appendChild(this.createItem(height));
    }
  }

  static clear(container) {
    if (typeof container === 'string') {
      container = document.querySelector(container);
    }
    container.innerHTML = '';
  }
}

// ========== LOADING SPINNER ==========
class LoadingSpinner {
  static show(message = 'Chargement...') {
    let spinner = document.getElementById('loading-spinner');
    if (!spinner) {
      spinner = document.createElement('div');
      spinner.id = 'loading-spinner';
      spinner.className = 'loading-overlay';
      spinner.innerHTML = `
        <div class="spinner">
          <div class="spinner-ring"></div>
          <p>${message}</p>
        </div>
      `;
      document.body.appendChild(spinner);
    }
    spinner.style.display = 'flex';
  }

  static hide() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) spinner.style.display = 'none';
  }
}

// ========== HAPTIC FEEDBACK ==========
class Haptic {
  static feedback(pattern = [10]) {
    if (navigator.vibrate) {
      navigator.vibrate(pattern);
    }
  }

  static tap() {
    this.feedback([10]);
  }

  static pulse() {
    this.feedback([10, 20, 10]);
  }

  static success() {
    this.feedback([10, 20, 15, 20, 10]);
  }

  static error() {
    this.feedback([30, 30, 30]);
  }
}

// ========== CSS POUR COMPOSANTS ==========
const componentStyles = `
<style>
  /* Modal */
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    animation: fadeIn 0.2s ease;
  }

  .modal {
    background: var(--color-surface);
    border-radius: 12px;
    box-shadow: var(--shadow-lg);
    max-height: 90vh;
    overflow-y: auto;
    animation: slideUp 0.3s ease;
  }

  .modal-sm { max-width: 400px; }
  .modal-md { max-width: 600px; }
  .modal-lg { max-width: 800px; }

  .modal-header {
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--color-border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .modal-header h2 {
    margin: 0;
  }

  .modal-close {
    background: none;
    border: none;
    font-size: 1.5em;
    cursor: pointer;
    padding: 0;
    width: 40px;
    height: 40px;
    color: var(--color-text-secondary);
    min-width: auto;
    min-height: auto;
  }

  .modal-body {
    padding: var(--spacing-lg);
  }

  .modal-footer {
    padding: var(--spacing-lg);
    border-top: 1px solid var(--color-border);
    display: flex;
    gap: var(--spacing-md);
    justify-content: flex-end;
  }

  .modal-footer button {
    flex: 1;
  }

  /* Loading */
  .loading-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.3);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 2000;
  }

  .spinner {
    text-align: center;
    background: var(--color-surface);
    padding: var(--spacing-xl);
    border-radius: 12px;
    box-shadow: var(--shadow-lg);
  }

  .spinner-ring {
    width: 50px;
    height: 50px;
    border: 4px solid var(--color-border);
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin: 0 auto var(--spacing-md);
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes slideUp {
    from { 
      transform: translateY(30px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  /* Responsive modals */
  @media (max-width: 768px) {
    .modal {
      max-width: 90%;
      max-height: 95vh;
    }

    .modal-header,
    .modal-body,
    .modal-footer {
      padding: var(--spacing-md);
    }

    .modal-footer {
      flex-direction: column;
    }

    .modal-footer button {
      width: 100%;
    }
  }
</style>
`;

// Auto-injecter les styles au chargement
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    document.head.insertAdjacentHTML('beforeend', componentStyles);
  });
} else {
  document.head.insertAdjacentHTML('beforeend', componentStyles);
}

// ========== EXPORTS ==========
window.ToastManager = ToastManager;
window.Modal = Modal;
window.DarkModeToggle = DarkModeToggle;
window.SkeletonLoader = SkeletonLoader;
window.LoadingSpinner = LoadingSpinner;
window.Haptic = Haptic;
window.ConnectionStatus = ConnectionStatus;
