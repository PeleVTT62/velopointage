/**
 * auth.js - Gestion de l'authentification
 */

import { logger, hapticFeedback } from './utils.js';

// Configuration
const CONFIG = {
  LOGIN_API: '/api/auth/login',
  CONFIG_URL: '/static/configuration.html',
  MAX_ATTEMPTS: 5,
  LOCKOUT_TIME: 300000 // 5 minutes
};

/**
 * Gestionnaire d'authentification
 */
class AuthManager {
  constructor() {
    this.attempts = 0;
    this.lockoutUntil = null;
    this.modal = null;
    this.onSuccessCallback = null;
  }
  
  /**
   * Vérifie si l'utilisateur est bloqué
   * @returns {boolean}
   */
  isLockedOut() {
    if (!this.lockoutUntil) return false;
    
    const now = Date.now();
    if (now < this.lockoutUntil) {
      const remainingMinutes = Math.ceil((this.lockoutUntil - now) / 60000);
      return remainingMinutes;
    }
    
    // Réinitialiser après expiration
    this.lockoutUntil = null;
    this.attempts = 0;
    return false;
  }
  
  /**
   * Crée le modal d'authentification
   * @returns {HTMLElement}
   */
  createAuthModal() {
    const overlay = document.createElement('div');
    overlay.className = 'auth-modal-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-labelledby', 'auth-modal-title');
    
    const lockout = this.isLockedOut();
    
    overlay.innerHTML = `
      <div class="auth-modal">
        <h2 id="auth-modal-title">🔐 Configuration</h2>
        ${lockout ? `
          <p style="color: var(--error-color); text-align: center; margin-bottom: 1rem;">
            ⏱️ Trop de tentatives. Réessayez dans ${lockout} minute${lockout > 1 ? 's' : ''}.
          </p>
        ` : `
          <form class="auth-modal-form" id="auth-form">
            <input 
              type="password" 
              id="auth-password" 
              class="auth-modal-input"
              placeholder="Entrez le mot de passe"
              autocomplete="current-password"
              required
              aria-label="Mot de passe"
              ${lockout ? 'disabled' : ''}
            />
            <div class="auth-modal-actions">
              <button 
                type="button" 
                class="auth-modal-btn auth-modal-btn-secondary"
                id="auth-cancel"
              >
                Annuler
              </button>
              <button 
                type="submit" 
                class="auth-modal-btn auth-modal-btn-primary"
                id="auth-submit"
                ${lockout ? 'disabled' : ''}
              >
                Valider
              </button>
            </div>
          </form>
        `}
      </div>
    `;
    
    return overlay;
  }
  
  /**
   * Affiche le modal d'authentification
   * @param {Function} onSuccess - Callback en cas de succès
   * @returns {Promise<boolean>}
   */
  showAuthModal(onSuccess) {
    return new Promise((resolve) => {
      // Vérifier le lockout
      const lockout = this.isLockedOut();
      if (lockout) {
        window.toast?.error(`⏱️ Trop de tentatives. Réessayez dans ${lockout} minute${lockout > 1 ? 's' : ''}.`, 0);
        hapticFeedback('error');
        resolve(false);
        return;
      }
      
      this.onSuccessCallback = onSuccess;
      
      // Créer et afficher le modal
      this.modal = this.createAuthModal();
      document.body.appendChild(this.modal);
      
      // Focus sur l'input
      setTimeout(() => {
        const input = document.getElementById('auth-password');
        if (input) input.focus();
      }, 100);
      
      // Gérer la fermeture sur overlay
      this.modal.addEventListener('click', (e) => {
        if (e.target === this.modal) {
          this.closeAuthModal();
          resolve(false);
        }
      });
      
      // Gérer le formulaire
      const form = document.getElementById('auth-form');
      if (form) {
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const success = await this.handleSubmit();
          resolve(success);
        });
      }
      
      // Bouton annuler
      const cancelBtn = document.getElementById('auth-cancel');
      if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
          this.closeAuthModal();
          resolve(false);
        });
      }
      
      // ESC pour fermer
      const handleEscape = (e) => {
        if (e.key === 'Escape') {
          this.closeAuthModal();
          resolve(false);
          document.removeEventListener('keydown', handleEscape);
        }
      };
      document.addEventListener('keydown', handleEscape);
      
      hapticFeedback('light');
    });
  }
  
  /**
   * Ferme le modal
   */
  closeAuthModal() {
    if (this.modal && this.modal.parentNode) {
      this.modal.style.animation = 'fadeOut 0.3s ease';
      setTimeout(() => {
        if (this.modal && this.modal.parentNode) {
          this.modal.parentNode.removeChild(this.modal);
        }
        this.modal = null;
      }, 300);
    }
  }
  
  /**
   * Gère la soumission du formulaire
   * @returns {Promise<boolean>}
   */
  async handleSubmit() {
    const passwordInput = document.getElementById('auth-password');
    const submitBtn = document.getElementById('auth-submit');
    
    if (!passwordInput) return false;
    
    const password = passwordInput.value.trim();
    
    if (!password) {
      window.toast?.error('❌ Veuillez entrer un mot de passe');
      hapticFeedback('error');
      passwordInput.focus();
      return false;
    }
    
    // Désactiver le bouton pendant la requête
    if (submitBtn) submitBtn.disabled = true;
    passwordInput.disabled = true;
    
    try {
      const success = await this.authenticate(password);
      
      if (success) {
        this.attempts = 0;
        this.closeAuthModal();
        
        if (this.onSuccessCallback) {
          this.onSuccessCallback();
        }
        
        return true;
      } else {
        this.attempts++;
        
        // Vérifier si on atteint la limite
        if (this.attempts >= CONFIG.MAX_ATTEMPTS) {
          this.lockoutUntil = Date.now() + CONFIG.LOCKOUT_TIME;
          window.toast?.error(`🔒 Trop de tentatives. Réessayez dans 5 minutes.`, 0);
          hapticFeedback('error');
          this.closeAuthModal();
          return false;
        }
        
        const remainingAttempts = CONFIG.MAX_ATTEMPTS - this.attempts;
        window.toast?.error(`❌ Mot de passe incorrect (${remainingAttempts} essai${remainingAttempts > 1 ? 's' : ''} restant${remainingAttempts > 1 ? 's' : ''})`);
        hapticFeedback('error');
        
        // Réactiver le formulaire
        if (submitBtn) submitBtn.disabled = false;
        passwordInput.disabled = false;
        passwordInput.value = '';
        passwordInput.focus();
        
        return false;
      }
    } catch (error) {
      logger.error('Erreur lors de l\'authentification:', error);
      window.toast?.error('❌ Erreur de connexion au serveur');
      hapticFeedback('error');
      
      // Réactiver le formulaire
      if (submitBtn) submitBtn.disabled = false;
      passwordInput.disabled = false;
      passwordInput.focus();
      
      return false;
    }
  }
  
  /**
   * Authentifie l'utilisateur via l'API
   * @param {string} password
   * @returns {Promise<boolean>}
   */
  async authenticate(password) {
    try {
      logger.info('Tentative d\'authentification...');
      
      const response = await fetch(CONFIG.LOGIN_API, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ password }),
        credentials: 'include'
      });
      
      if (response.ok) {
        logger.success('Authentification réussie');
        window.toast?.success('✅ Authentification réussie !');
        hapticFeedback('success');
        
        // Rediriger immédiatement (le modal reste visible pendant la redirection)
        window.location.href = CONFIG.CONFIG_URL;
        
        return true;
      } else {
        const error = await response.json().catch(() => ({}));
        logger.warn('Authentification échouée:', error.detail || response.statusText);
        return false;
      }
    } catch (error) {
      logger.error('Erreur réseau lors de l\'authentification:', error);
      throw error;
    }
  }
  
  /**
   * Affiche le modal et redirige en cas de succès
   * @returns {Promise<void>}
   */
  async promptForPassword() {
    await this.showAuthModal(() => {
      // La redirection est gérée dans authenticate()
    });
  }
}

// Instance singleton
const authManager = new AuthManager();

// Export pour utilisation globale
export default authManager;

// Export également sur window pour compatibilité
if (typeof window !== 'undefined') {
  window.authManager = authManager;
}
