// Service Worker pour l'extension Chrome Éditeur Accordéons

const EDITOR_URL = 'http://localhost:5173';

// Création des menus contextuels au démarrage
chrome.runtime.onInstalled.addListener(() => {
  // Menu contextuel pour ajouter du contenu sélectionné
  chrome.contextMenus.create({
    id: 'add-to-accordion',
    title: 'Ajouter à l\'Éditeur Accordéons',
    contexts: ['selection', 'page', 'link']
  });

  console.log('Extension Éditeur Accordéons installée');
});

// Gestion du clic sur l'icône de l'extension
chrome.action.onClicked.addListener((tab) => {
  openEditor();
});

// Gestion des menus contextuels
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'add-to-accordion') {
    handleAddToAccordion(info, tab);
  }
});

/**
 * Ouvre l'éditeur dans un nouvel onglet
 */
function openEditor() {
  chrome.tabs.create({ url: EDITOR_URL });
}

/**
 * Gère l'ajout de contenu depuis le menu contextuel
 */
async function handleAddToAccordion(info, tab) {
  try {
    // Récupérer les informations
    const content = info.selectionText || '';
    const pageTitle = tab.title || '';
    const pageUrl = info.linkUrl || tab.url || '';
    
    // Construire le texte à ajouter
    let textToAdd = '';
    
    if (content) {
      textToAdd = `# ${pageTitle}\n\n${content}\n\nSource: ${pageUrl}`;
    } else {
      textToAdd = `# ${pageTitle}\n\nLien: ${pageUrl}`;
    }
    
    // Stocker temporairement les données pour que l'éditeur les récupère
    const captureData = {
      text: textToAdd,
      source: 'contextmenu',
      timestamp: Date.now(),
      pageTitle,
      pageUrl,
      selectedText: content
    };
    
    // Utiliser chrome.storage pour passer les données
    await chrome.storage.local.set({ 
      pendingCapture: captureData 
    });
    
    // Ouvrir l'éditeur
    const editorTab = await chrome.tabs.create({ url: EDITOR_URL });
    
    // Attendre que l'éditeur soit chargé et notifier
    chrome.tabs.onUpdated.addListener(function listener(tabId, changeInfo) {
      if (tabId === editorTab.id && changeInfo.status === 'complete') {
        chrome.tabs.onUpdated.removeListener(listener);
        
        // Envoyer un message à l'éditeur pour qu'il récupère les données
        chrome.tabs.sendMessage(editorTab.id, {
          action: 'loadPendingCapture'
        }).catch(() => {
          // Si le content script n'est pas chargé, ce n'est pas grave
          // L'éditeur vérifiera chrome.storage au chargement
        });
      }
    });
    
    // Notification de succès
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon-48.png',
      title: 'Éditeur Accordéons',
      message: 'Contenu ajouté à l\'éditeur'
    });
    
  } catch (error) {
    console.error('Erreur lors de l\'ajout:', error);
    
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon-48.png',
      title: 'Éditeur Accordéons',
      message: 'Erreur lors de l\'ajout du contenu'
    });
  }
}

// Écouter les messages des content scripts ou de l'éditeur
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'openEditor') {
    openEditor();
    sendResponse({ success: true });
  }
  return true;
});
