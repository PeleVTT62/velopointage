/**
 * utils.js - Fonctions utilitaires
 */

/**
 * Attend un délai spécifié
 * @param {number} ms - Délai en millisecondes
 * @returns {Promise<void>}
 */
export const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Debounce une fonction
 * @param {Function} func - Fonction à debouncer
 * @param {number} wait - Délai d'attente en ms
 * @returns {Function}
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Throttle une fonction
 * @param {Function} func - Fonction à throttler
 * @param {number} limit - Limite en ms
 * @returns {Function}
 */
export function throttle(func, limit) {
  let inThrottle;
  return function executedFunction(...args) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

/**
 * Formatte une date
 * @param {Date|string} date - Date à formater
 * @param {boolean} includeTime - Inclure l'heure
 * @returns {string}
 */
export function formatDate(date, includeTime = true) {
  const d = typeof date === 'string' ? new Date(date) : date;
  
  if (!(d instanceof Date) || isNaN(d)) {
    return 'Date invalide';
  }
  
  const options = {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  };
  
  if (includeTime) {
    options.hour = '2-digit';
    options.minute = '2-digit';
  }
  
  return d.toLocaleString('fr-FR', options);
}

/**
 * Génère un ID unique
 * @returns {string}
 */
export function generateId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Vérifie si on est en mode online
 * @returns {boolean}
 */
export function isOnline() {
  return navigator.onLine;
}

/**
 * Ajoute des listeners pour les changements online/offline
 * @param {Function} onOnline - Callback quand online
 * @param {Function} onOffline - Callback quand offline
 */
export function addNetworkListeners(onOnline, onOffline) {
  window.addEventListener('online', onOnline);
  window.addEventListener('offline', onOffline);
  
  // Retourne une fonction de nettoyage
  return () => {
    window.removeEventListener('online', onOnline);
    window.removeEventListener('offline', onOffline);
  };
}

/**
 * Vibration haptique (si supporté)
 * @param {string} type - Type de feedback ('light', 'medium', 'heavy', 'error', 'success')
 */
export function hapticFeedback(type = 'light') {
  if (!navigator.vibrate) return;
  
  const patterns = {
    light: 10,
    medium: 20,
    heavy: 30,
    error: [10, 50, 10],
    success: [10, 30, 10, 30]
  };
  
  // Tenter la vibration, ignorer silencieusement les erreurs (restriction navigateur)
  try {
    navigator.vibrate(patterns[type] || patterns.light);
  } catch (e) {
    // Vibration bloquée par le navigateur (pas d'interaction utilisateur)
  }
}

/**
 * Copie du texte dans le presse-papier
 * @param {string} text - Texte à copier
 * @returns {Promise<boolean>}
 */
export async function copyToClipboard(text) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
    
    // Fallback pour anciens navigateurs
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    const success = document.execCommand('copy');
    document.body.removeChild(textArea);
    return success;
  } catch (error) {
    console.error('Erreur copie presse-papier:', error);
    return false;
  }
}

/**
 * Télécharge un fichier
 * @param {string} content - Contenu du fichier
 * @param {string} filename - Nom du fichier
 * @param {string} mimeType - Type MIME
 */
export function downloadFile(content, filename, mimeType = 'text/plain') {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Détecte le type d'appareil
 * @returns {Object} Info sur l'appareil
 */
export function getDeviceInfo() {
  const ua = navigator.userAgent;
  
  return {
    isMobile: /Mobile|Android|iPhone/i.test(ua),
    isTablet: /Tablet|iPad/i.test(ua),
    isIOS: /iPhone|iPad|iPod/i.test(ua),
    isAndroid: /Android/i.test(ua),
    isSafari: /Safari/i.test(ua) && !/Chrome/i.test(ua),
    isChrome: /Chrome/i.test(ua),
    isFirefox: /Firefox/i.test(ua),
    isStandalone: window.matchMedia('(display-mode: standalone)').matches
  };
}

/**
 * Logger amélioré
 */
export const logger = {
  info: (...args) => console.log('ℹ️', ...args),
  success: (...args) => console.log('✅', ...args),
  warn: (...args) => console.warn('⚠️', ...args),
  error: (...args) => console.error('❌', ...args),
  debug: (...args) => {
    if (window.DEBUG_MODE) {
      console.log('🐛', ...args);
    }
  }
};

/**
 * Gestion du localStorage avec try/catch
 */
export const storage = {
  get: (key, defaultValue = null) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      logger.error('Erreur lecture localStorage:', error);
      return defaultValue;
    }
  },
  
  set: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      logger.error('Erreur écriture localStorage:', error);
      return false;
    }
  },
  
  remove: (key) => {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      logger.error('Erreur suppression localStorage:', error);
      return false;
    }
  },
  
  clear: () => {
    try {
      localStorage.clear();
      return true;
    } catch (error) {
      logger.error('Erreur clear localStorage:', error);
      return false;
    }
  }
};
