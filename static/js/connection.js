/**
 * connection.js - Gestion de la connexion API
 */

import { delay, logger, hapticFeedback, addNetworkListeners } from './utils.js';

// Configuration
const CONFIG = {
  API_ENDPOINT: '/api/passages',
  CONNECTION_TIMEOUT: 5000,
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000,
  CHECK_INTERVAL: 30000 // Vérification toutes les 30s
};

/**
 * Gestionnaire de connexion API
 */
class ConnectionManager {
  constructor() {
    this.isConnected = false;
    this.checkInterval = null;
    this.listeners = [];
    this.retryCount = 0;
    
    // Écouter les changements online/offline
    this.setupNetworkListeners();
  }
  
  /**
   * Configure les listeners réseau
   */
  setupNetworkListeners() {
    addNetworkListeners(
      () => this.handleOnline(),
      () => this.handleOffline()
    );
  }
  
  /**
   * Quand on passe en ligne
   */
  handleOnline() {
    logger.info('Connexion internet détectée');
    window.toast?.success('🌐 Connexion rétablie');
    hapticFeedback('success');
    this.checkConnection();
  }
  
  /**
   * Quand on passe hors ligne
   */
  handleOffline() {
    logger.warn('Connexion internet perdue');
    window.toast?.warning('⚠️ Hors ligne - Mode dégradé activé', 5000);
    hapticFeedback('error');
    this.setConnected(false);
  }
  
  /**
   * Vérifie la connexion à l'API
   * @param {number} retries - Nombre de tentatives restantes
   * @returns {Promise<boolean>}
   */
  async checkConnection(retries = CONFIG.MAX_RETRIES) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), CONFIG.CONNECTION_TIMEOUT);
      
      const response = await fetch(CONFIG.API_ENDPOINT, { 
        method: 'GET',
        signal: controller.signal,
        cache: 'no-cache'
      });
      
      clearTimeout(timeoutId);
      
      const isConnected = response.ok;
      this.setConnected(isConnected);
      this.retryCount = 0; // Reset le compteur en cas de succès
      
      return isConnected;
    } catch (error) {
      logger.warn(`Tentative de connexion échouée (${CONFIG.MAX_RETRIES - retries + 1}/${CONFIG.MAX_RETRIES}):`, error.message);
      
      if (retries > 0) {
        await delay(CONFIG.RETRY_DELAY);
        return this.checkConnection(retries - 1);
      }
      
      this.setConnected(false);
      this.retryCount++;
      
      // Afficher un message après plusieurs échecs
      if (this.retryCount >= 3) {
        window.toast?.error('❌ Impossible de se connecter au serveur', 0);
      }
      
      return false;
    }
  }
  
  /**
   * Définit l'état de connexion
   * @param {boolean} connected
   */
  setConnected(connected) {
    const wasConnected = this.isConnected;
    this.isConnected = connected;
    
    // Notifier les listeners
    if (wasConnected !== connected) {
      this.notifyListeners(connected);
    }
    
    // Mettre à jour l'UI
    if (window.connectionStatus) {
      window.connectionStatus.setConnected(connected);
    }
  }
  
  /**
   * Ajoute un listener de changement de connexion
   * @param {Function} callback
   * @returns {Function} Fonction pour retirer le listener
   */
  addListener(callback) {
    this.listeners.push(callback);
    
    // Retourne une fonction de nettoyage
    return () => {
      this.listeners = this.listeners.filter(cb => cb !== callback);
    };
  }
  
  /**
   * Notifie tous les listeners
   * @param {boolean} connected
   */
  notifyListeners(connected) {
    this.listeners.forEach(callback => {
      try {
        callback(connected);
      } catch (error) {
        logger.error('Erreur dans listener de connexion:', error);
      }
    });
  }
  
  /**
   * Démarre la vérification périodique
   */
  startPeriodicCheck() {
    if (this.checkInterval) {
      return; // Déjà démarré
    }
    
    logger.info('Démarrage de la vérification périodique de connexion');
    
    // Vérification immédiate
    this.checkConnection();
    
    // Puis vérification périodique
    this.checkInterval = setInterval(() => {
      this.checkConnection();
    }, CONFIG.CHECK_INTERVAL);
  }
  
  /**
   * Arrête la vérification périodique
   */
  stopPeriodicCheck() {
    if (this.checkInterval) {
      logger.info('Arrêt de la vérification périodique');
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
  }
  
  /**
   * Obtient l'état actuel
   * @returns {boolean}
   */
  getStatus() {
    return this.isConnected;
  }
  
  /**
   * Force une reconnexion
   */
  async reconnect() {
    logger.info('Tentative de reconnexion forcée...');
    window.toast?.info('🔄 Reconnexion...', 2000);
    
    const success = await this.checkConnection();
    
    if (success) {
      window.toast?.success('✅ Reconnecté !');
      hapticFeedback('success');
    } else {
      window.toast?.error('❌ Échec de reconnexion');
      hapticFeedback('error');
    }
    
    return success;
  }
}

// Instance singleton
const connectionManager = new ConnectionManager();

// Export pour utilisation globale
export default connectionManager;

// Export également sur window pour compatibilité
if (typeof window !== 'undefined') {
  window.connectionManager = connectionManager;
}
