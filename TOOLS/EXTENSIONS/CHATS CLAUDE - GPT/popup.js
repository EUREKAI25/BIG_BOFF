document.addEventListener('DOMContentLoaded', function() {
  console.log('🎮 Universal AI Conversation Saver popup v1.1 loaded');
  
  // Éléments du DOM
  const extractBtn = document.getElementById('extractBtn');
  const downloadBtn = document.getElementById('downloadBtn');
  const copyBtn = document.getElementById('copyBtn');
  const extractCustomBtn = document.getElementById('extractCustomBtn');
  const status = document.getElementById('status');
  const preview = document.getElementById('preview');
  const previewContent = document.getElementById('previewContent');
  const filenameInput = document.getElementById('filename');
  const customUrlInput = document.getElementById('customUrl');
  const outputDirectory = document.getElementById('outputDirectory');
  const customDirectory = document.getElementById('customDirectory');
  const platformIndicator = document.getElementById('platformIndicator');
  const stats = document.getElementById('stats');
  const messageCount = document.getElementById('messageCount');
  const platformSpan = document.getElementById('platform');
  const recentUrls = document.getElementById('recentUrls');
  
  let currentConversationData = null;
  
  // ===== GESTION DES ONGLETS =====
  
  document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
      const tabId = button.dataset.tab;
      
      // Activer l'onglet
      document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      
      button.classList.add('active');
      document.getElementById(tabId + '-tab').classList.add('active');
    });
  });
  
  // ===== GESTION DU RÉPERTOIRE =====
  
  outputDirectory.addEventListener('change', function() {
    if (this.value === 'custom') {
      customDirectory.classList.remove('hidden');
      customDirectory.focus();
    } else {
      customDirectory.classList.add('hidden');
    }
  });
  
  // ===== GESTION DES URLs RÉCENTES =====
  
  function loadRecentUrls() {
    const recent = JSON.parse(localStorage.getItem('recentUrls') || '[]');
    recentUrls.innerHTML = '';
    
    recent.slice(0, 3).forEach(url => {
      const urlElement = document.createElement('div');
      urlElement.className = 'recent-url';
      urlElement.textContent = url.length > 60 ? url.substring(0, 60) + '...' : url;
      urlElement.addEventListener('click', () => {
        customUrlInput.value = url;
      });
      recentUrls.appendChild(urlElement);
    });
  }
  
  function saveRecentUrl(url) {
    let recent = JSON.parse(localStorage.getItem('recentUrls') || '[]');
    recent = recent.filter(u => u !== url); // Enlever les doublons
    recent.unshift(url); // Ajouter en premier
    recent = recent.slice(0, 5); // Garder seulement 5
    localStorage.setItem('recentUrls', JSON.stringify(recent));
    loadRecentUrls();
  }
  
  // ===== UTILITAIRES =====
  
  function normalizeString(str) {
    return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }
  
  function showStatus(message, type = 'success') {
    console.log(`📢 Status: ${message} (${type})`);
    status.textContent = message;
    status.className = `status ${type}`;
    status.classList.remove('hidden');
    
    setTimeout(() => {
      status.classList.add('hidden');
    }, 5000);
  }
  
  function updatePlatformIndicator(platform) {
    platformIndicator.textContent = platform === 'claude' ? '🟦 Claude' : 
                                   platform === 'chatgpt' ? '🟢 ChatGPT' : 
                                   '❓ Inconnue';
    platformIndicator.className = `platform-indicator ${platform}`;
  }
  
  function generateDefaultFilename(platform, title) {
    const timestamp = new Date().toISOString().split('T')[0];
    
    if (!title) return `${platform}_conversation_${timestamp}`;
    
    const cleanTitle = normalizeString(title)
      .replace(/\s*-\s*(Claude|ChatGPT).*$/i, '')
      .replace(/[^a-z0-9]/gi, '_')
      .replace(/_+/g, '_')
      .toLowerCase()
      .substring(0, 50)
      .replace(/^_|_$/g, '');
    
    const finalTitle = cleanTitle.length > 2 ? cleanTitle : 'conversation';
    return `${platform}_${finalTitle}_${timestamp}`;
  }
  
  // ===== DÉTECTION DE PLATEFORME =====
  
  async function checkPlatform() {
    return new Promise((resolve) => {
      chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (!tabs[0]) {
          resolve('unknown');
          return;
        }
        
        const url = tabs[0].url.toLowerCase();
        if (url.includes('claude.ai')) {
          resolve('claude');
        } else if (url.includes('chatgpt.com') || url.includes('chat.openai.com')) {
          resolve('chatgpt');
        } else {
          resolve('unknown');
        }
      });
    });
  }
  
  // ===== INJECTION DU SCRIPT =====
  
  async function injectContentScript() {
    return new Promise((resolve) => {
      chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (!tabs[0]) {
          resolve(false);
          return;
        }
        
        console.log('💉 Injecting content script manually...');
        
        chrome.scripting.executeScript({
          target: { tabId: tabs[0].id },
          files: ['content.js']
        }, (result) => {
          if (chrome.runtime.lastError) {
            console.error('❌ Injection error:', chrome.runtime.lastError);
            resolve(false);
          } else {
            console.log('✅ Content script injected successfully');
            resolve(true);
          }
        });
      });
    });
  }
  
  // ===== EXTRACTION LOCALE (PAGE COURANTE) =====
  
  async function executeAction(action) {
    console.log(`🚀 Executing action: ${action}`);
    
    const platform = await checkPlatform();
    if (platform === 'unknown') {
      showStatus('Allez sur claude.ai ou chatgpt.com pour utiliser cette extension', 'error');
      return;
    }
    
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {action: action}, async function(response) {
        
        if (chrome.runtime.lastError || !response) {
          console.log('📤 Direct communication failed, trying manual injection...');
          
          const injected = await injectContentScript();
          if (!injected) {
            showStatus('Erreur d\'injection du script', 'error');
            return;
          }
          
          setTimeout(() => {
            chrome.tabs.sendMessage(tabs[0].id, {action: action}, function(response) {
              handleActionResponse(response, action, platform);
            });
          }, 1000);
          
        } else {
          handleActionResponse(response, action, platform);
        }
      });
    });
  }
  
  // ===== EXTRACTION DISTANTE (URL PERSONNALISÉE) =====
  
  async function executeCustomExtraction() {
    const url = customUrlInput.value.trim();
    if (!url) {
      showStatus('Veuillez saisir une URL', 'error');
      return;
    }
    
    // Validation URL
    if (!url.includes('claude.ai') && !url.includes('chatgpt.com')) {
      showStatus('URL non supportée. Utilisez Claude.ai ou ChatGPT.com', 'error');
      return;
    }
    
    const outputDir = outputDirectory.value === 'custom' ? 
                     customDirectory.value.trim() : 
                     outputDirectory.value;
    
    if (!outputDir) {
      showStatus('Veuillez sélectionner un répertoire', 'error');
      return;
    }
    
    showStatus('🌐 Extraction en cours...', 'info');
    
    try {
      // Appeler le script Python via le background
      chrome.runtime.sendMessage({
        action: 'extractRemoteConversation',
        url: url,
        outputDir: outputDir
      }, function(response) {
        if (response && response.success) {
          showStatus(`✅ Conversation extraite: ${response.messageCount} messages`, 'success');
          saveRecentUrl(url);
          
          // Afficher dans les stats
          stats.classList.remove('hidden');
          messageCount.textContent = `${response.messageCount} messages`;
          platformSpan.textContent = response.platform;
          
        } else {
          const errorMsg = response ? response.error : 'Erreur inconnue';
          showStatus(`❌ Erreur: ${errorMsg}`, 'error');
        }
      });
      
    } catch (error) {
      showStatus(`❌ Erreur: ${error.message}`, 'error');
    }
  }
  
  function handleActionResponse(response, action, platform) {
    console.log('📥 Response received:', response);
    
    if (chrome.runtime.lastError) {
      console.error('❌ Runtime error:', chrome.runtime.lastError);
      showStatus('Erreur: ' + chrome.runtime.lastError.message, 'error');
      return;
    }
    
    if (response && response.success) {
      handleActionSuccess(response, action, platform);
    } else {
      const errorMsg = response ? response.error : 'Erreur inconnue';
      console.error('❌ Action error:', errorMsg);
      showStatus(`Erreur: ${errorMsg}`, 'error');
    }
  }
  
  function handleActionSuccess(response, action, platform) {
    const data = response.data;
    
    if (action === 'extractConversation') {
      currentConversationData = data;
      
      stats.classList.remove('hidden');
      messageCount.textContent = `${data.conversation.messageCount} messages`;
      platformSpan.textContent = data.conversationMetadata.platform || platform;
      
      showStatus(`${data.conversation.messageCount} messages extraits`, 'success');
      previewContent.textContent = JSON.stringify(data, null, 2);
      preview.classList.remove('hidden');
      
      if (!filenameInput.value.trim() && data.conversationMetadata.suggestedFilename) {
        const suggestedName = data.conversationMetadata.suggestedFilename.replace('.json', '');
        filenameInput.value = suggestedName;
      }
      
    } else if (action === 'downloadConversation') {
      showStatus('Fichier téléchargé avec succès !', 'success');
      
    } else if (action === 'copyConversation') {
      showStatus('Conversation copiée dans le presse-papiers !', 'success');
    }
  }
  
  function downloadWithCustomName() {
    if (!currentConversationData) {
      showStatus('Veuillez d\'abord extraire la conversation', 'error');
      return;
    }
    
    const customFilename = filenameInput.value.trim();
    if (!customFilename) {
      showStatus('Veuillez entrer un nom de fichier', 'error');
      return;
    }
    
    const selectedPath = document.getElementById('downloadPath')?.value || 'CHATS';
    const safeFilename = customFilename.replace(/[^a-z0-9_-]/gi, '_').toLowerCase() + '.json';
    
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {
        action: 'downloadConversation',
        customFilename: safeFilename,
        suggestedPath: selectedPath
      }, function(response) {
        if (response && response.success) {
          showStatus(`Téléchargement: ${safeFilename} → ${selectedPath}`, 'success');
        } else {
          showStatus('Erreur de téléchargement', 'error');
        }
      });
    });
  }
  
  // ===== EVENT LISTENERS =====
  
  extractBtn.addEventListener('click', () => executeAction('extractConversation'));
  
  downloadBtn.addEventListener('click', () => {
    if (currentConversationData && filenameInput.value.trim()) {
      downloadWithCustomName();
    } else {
      executeAction('downloadConversation');
    }
  });
  
  copyBtn.addEventListener('click', () => executeAction('copyConversation'));
  
  extractCustomBtn.addEventListener('click', executeCustomExtraction);
  
  // ===== INITIALISATION =====
  
  loadRecentUrls();
  
  checkPlatform().then(platform => {
    updatePlatformIndicator(platform);
    
    if (platform !== 'unknown') {
      chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (tabs[0] && tabs[0].title) {
          const defaultName = generateDefaultFilename(platform, tabs[0].title);
          filenameInput.value = defaultName;
        }
      });
    } else {
      showStatus('Naviguez vers claude.ai ou chatgpt.com', 'error');
    }
  });
});