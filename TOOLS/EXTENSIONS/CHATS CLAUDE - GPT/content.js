// Content script pour l'extraction de conversations
(function() {
    'use strict';
    
    console.log('🚀 AI Conversation Saver loaded');
    
    // Variables globales sécurisées
    let currentUrl = '';
    let currentTitle = '';
    
    // Initialisation sécurisée
    function safeInit() {
        try {
            currentUrl = location.href || '';
            currentTitle = document.title || '';
            console.log('✅ Initialized on:', currentUrl);
        } catch (e) {
            console.warn('Init error:', e);
        }
    }
    
    // Détecter la plateforme
    function getPlatform() {
        if (currentUrl.includes('claude.ai')) return 'claude';
        if (currentUrl.includes('chatgpt.com')) return 'chatgpt';
        return 'unknown';
    }
    
    // Extraction précise pour Claude
    function extractClaudeMessages() {
        const messages = [];
        
        console.log('🔍 Starting Claude message extraction...');
        
        // Méthode 1: Chercher les vrais messages dans la structure Claude
        // Claude organise les messages dans une structure spécifique
        let messageElements = [];
        
        // Sélecteurs spécifiques à la nouvelle interface Claude
        const claudeSelectors = [
            // Messages dans la conversation principale
            'div[data-testid*="message"]',
            'div[role="presentation"] > div > div > div',
            'main div > div > div > div[class*="font-"]',
            // Structure plus récente de Claude
            'div[class*="group"] div[class*="whitespace-pre-wrap"]',
            'div[class*="prose"] div',
            // Tentative générique pour les conteneurs de texte
            'main div[class*="max-w"] > div > div'
        ];
        
        for (const selector of claudeSelectors) {
            const elements = document.querySelectorAll(selector);
            if (elements.length > 1) {
                messageElements = Array.from(elements);
                console.log(`✅ Found ${elements.length} elements with selector: ${selector}`);
                break;
            }
        }
        
        // Méthode 2: Analyse intelligente de la zone de conversation
        if (messageElements.length === 0) {
            console.log('🔄 Analyzing conversation area structure...');
            
            // Chercher la zone principale de conversation
            const possibleContainers = [
                document.querySelector('main'),
                document.querySelector('[role="main"]'),
                document.querySelector('div[class*="conversation"]'),
                document.querySelector('div[class*="chat"]')
            ];
            
            for (const container of possibleContainers) {
                if (!container) continue;
                
                // Chercher les divs qui contiennent du texte substantiel
                const textDivs = container.querySelectorAll('div');
                const candidates = Array.from(textDivs).filter(div => {
                    const text = div.textContent?.trim();
                    
                    // Critères stricts pour les vrais messages
                    if (!text || text.length < 30) return false;
                    
                    // Doit avoir du contenu conversationnel
                    const hasConversationalContent = 
                        text.includes('.') || text.includes('?') || text.includes('!') ||
                        text.length > 100;
                    
                    // Ne doit pas être un élément d'interface
                    const isNotInterface = 
                        !text.includes('popup.js') &&
                        !text.includes('manifest.json') &&
                        !text.includes('@keyframes') &&
                        !text.includes('Artéfacts') &&
                        !text.includes('Contrôles') &&
                        !text.includes('En savoir plus') &&
                        !text.includes('Sonnet 4') &&
                        !text.includes('Cliquez pour ouvrir') &&
                        !text.includes('lignes') &&
                        !text.startsWith('RécentsSans titre') &&
                        !text.includes('intercom-lightweight') &&
                        !div.className.includes('sidebar') &&
                        !div.className.includes('header');
                    
                    // Vérifier que c'est un élément terminal (peu d'enfants)
                    const isTerminalElement = div.children.length <= 3;
                    
                    // Vérifier la visibilité
                    const rect = div.getBoundingClientRect();
                    const isVisible = rect.width > 50 && rect.height > 20;
                    
                    return hasConversationalContent && isNotInterface && isTerminalElement && isVisible;
                });
                
                if (candidates.length > 0) {
                    messageElements = candidates;
                    console.log(`✅ Found ${candidates.length} message candidates in ${container.tagName}`);
                    break;
                }
            }
        }
        
        // Méthode 3: Extraction par reconnaissance de patterns
        if (messageElements.length === 0) {
            console.log('🔄 Using pattern recognition...');
            
            // Chercher tous les éléments avec du texte
            const allElements = document.querySelectorAll('*');
            const textElements = [];
            
            Array.from(allElements).forEach(el => {
                const text = el.textContent?.trim();
                
                if (text && text.length > 50 && text.length < 3000) {
                    // Vérifier que c'est probablement un message
                    const looksLikeMessage = 
                        // Contient de la ponctuation normale
                        (text.match(/[.!?]/g) || []).length > 0 &&
                        // Pas de code ou interface
                        !text.includes('function') &&
                        !text.includes('const ') &&
                        !text.includes('popup.js') &&
                        !text.includes('keyframes') &&
                        !text.includes('Artéfacts') &&
                        !text.includes('manifes') &&
                        !text.includes('lignes') &&
                        !text.startsWith('Récents') &&
                        // Pas trop d'enfants (élément terminal)
                        el.children.length < 3;
                    
                    if (looksLikeMessage) {
                        textElements.push({
                            element: el,
                            text: text,
                            length: text.length
                        });
                    }
                }
            });
            
            // Trier par pertinence (longueur et position)
            textElements.sort((a, b) => {
                const aRect = a.element.getBoundingClientRect();
                const bRect = b.element.getBoundingClientRect();
                // Préférer les éléments centraux et longs
                return (bRect.left + b.length) - (aRect.left + a.length);
            });
            
            messageElements = textElements.slice(0, 15).map(item => item.element);
            console.log(`📝 Pattern recognition found ${messageElements.length} elements`);
        }
        
        // Traitement des messages trouvés
        let lastRole = 'assistant'; // Pour l'alternance
        
        messageElements.forEach((element, index) => {
            try {
                let content = element.textContent?.trim();
                if (!content || content.length < 20) return;
                
                // Nettoyage agressif
                content = content
                    .replace(/\s+/g, ' ')
                    .replace(/^(Human|Assistant|User|Claude):\s*/i, '')
                    .replace(/\s*(Modifier|Réessayer|Copier)\s*$/gi, '')
                    .trim();
                
                // Dernière vérification: ne pas ajouter les éléments d'interface
                if (content.includes('popup.js') ||
                    content.includes('manifest') ||
                    content.includes('lignes') ||
                    content.includes('keyframes') ||
                    content.startsWith('Récents') ||
                    content.includes('Artéfacts') ||
                    content.length < 15) {
                    return;
                }
                
                // Détermination intelligente du rôle
                let role = 'assistant';
                
                // Analyser le contenu pour deviner le rôle
                const contentLower = content.toLowerCase();
                if (contentLower.includes('je vais analyser') ||
                    contentLower.includes('voici') ||
                    contentLower.includes('j\'ai corrigé') ||
                    contentLower.startsWith('oui,') ||
                    contentLower.startsWith('non,') ||
                    contentLower.includes('claude')) {
                    role = 'assistant';
                } else if (content.endsWith('?') ||
                           contentLower.includes('peux-tu') ||
                           contentLower.includes('pouvez-vous') ||
                           contentLower.includes('extension') ||
                           contentLower.includes('cookies =')) {
                    role = 'user';
                } else {
                    // Alterner par rapport au dernier rôle
                    role = lastRole === 'user' ? 'assistant' : 'user';
                }
                
                lastRole = role;
                
                messages.push({
                    id: `claude_msg_${messages.length}`,
                    role: role,
                    content: content,
                    timestamp: new Date().toISOString(),
                    originalIndex: index,
                    extractionMethod: 'precise'
                });
                
            } catch (error) {
                console.warn(`⚠️ Error processing element ${index}:`, error);
            }
        });
        
        console.log(`✅ Final extraction: ${messages.length} clean messages`);
        
        // Debug: afficher les premiers messages trouvés
        if (messages.length > 0) {
            console.log('📋 First few messages:', messages.slice(0, 3).map(m => ({
                role: m.role,
                preview: m.content.substring(0, 100) + '...'
            })));
        }
        
        return messages;
    }
    
    // Extraction simple pour ChatGPT (inchangée)
    function extractChatGPTMessages() {
        const messages = [];
        
        // Essayer les sélecteurs ChatGPT
        let elements = document.querySelectorAll('[data-message-id]');
        
        if (elements.length === 0) {
            elements = document.querySelectorAll('[data-testid="conversation-turn"]');
        }
        
        Array.from(elements).forEach((el, index) => {
            const text = el.textContent?.trim();
            const role = el.getAttribute('data-message-author-role');
            
            if (text && text.length > 10) {
                messages.push({
                    id: `chatgpt_${index}`,
                    role: role === 'user' ? 'user' : 'assistant',
                    content: text,
                    timestamp: new Date().toISOString()
                });
            }
        });
        
        return messages;
    }
    
    // Génération intelligente du nom de fichier
    function generateSmartFilename(platform, title) {
        // Nettoyer le titre pour en faire un nom de fichier valide
        let cleanTitle = title
            .replace(/\s*-\s*(Claude|ChatGPT).*$/i, '') // Enlever " - Claude" à la fin seulement
            .replace(/\s*\|\s*(Claude|ChatGPT).*$/i, '') // Enlever " | Claude" à la fin
            .normalize('NFD') // Décomposer les caractères accentués
            .replace(/[\u0300-\u036f]/g, '') // Enlever les accents
            .replace(/[^\w\s]/g, '') // Enlever caractères spéciaux SAUF espaces
            .replace(/\s+/g, '_') // Remplacer espaces par underscores
            .replace(/_+/g, '_') // Éviter les underscores multiples
            .toLowerCase()
            .substring(0, 50) // Limiter la longueur
            .replace(/^_|_$/g, ''); // Enlever underscores en début/fin
        
        // Valeurs par défaut si le titre est vide ou invalide
        if (!cleanTitle || cleanTitle === 'untitled' || cleanTitle === 'new_conversation' || cleanTitle.length < 3) {
            cleanTitle = 'conversation';
        }
        
        // Ajouter timestamp pour éviter les conflits
        const timestamp = new Date().toISOString().split('T')[0];
        
        // Format final : platform_titre_propre_date.json
        return `${platform}_${cleanTitle}.json`;
    }
    
    // Extraire l'ID de conversation depuis l'URL
    function extractConversationId() {
        try {
            if (currentUrl.includes('claude.ai')) {
                const match = currentUrl.match(/\/chat\/([a-f0-9-]+)/);
                return match ? match[1] : null;
            } else if (currentUrl.includes('chatgpt.com')) {
                const match = currentUrl.match(/\/c\/([a-f0-9-]+)/);
                return match ? match[1] : null;
            }
        } catch (error) {
            console.warn('❌ Error extracting conversation ID:', error);
        }
        
        return null;
    }
    
    // Extraction principale
    function extractConversation() {
        const platform = getPlatform();
        let messages = [];
        
        console.log(`🔍 Extracting conversation for platform: ${platform}`);
        
        if (platform === 'claude') {
            messages = extractClaudeMessages();
        } else if (platform === 'chatgpt') {
            messages = extractChatGPTMessages();
        }
        
        // Générer nom de fichier basé sur le titre de la conversation
        const conversationTitle = document.title;
        const cleanTitle = generateSmartFilename(platform, conversationTitle);
        const conversationId = extractConversationId();
        
        const result = {
            conversationMetadata: {
                platform: platform,
                extractedAt: new Date().toISOString(),
                extractorVersion: '1.1',
                url: currentUrl,
                title: conversationTitle,
                conversationId: conversationId,
                suggestedFilename: cleanTitle
            },
            conversation: {
                messageCount: messages.length,
                messages: messages
            },
            technicalInfo: {
                userAgent: navigator.userAgent || 'Unknown',
                pageLanguage: document.documentElement?.lang || 'unknown',
                extractionSuccess: messages.length > 0,
                error: messages.length === 0 ? 'No messages found' : null,
                domInfo: {
                    totalElements: document.querySelectorAll('*').length,
                    bodyText: document.body?.textContent?.length || 0
                }
            }
        };
        
        console.log(`📊 Extraction complete: ${messages.length} messages`);
        return result;
    }
    
    // Téléchargement
    function downloadConversation(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        chrome.runtime.sendMessage({
            action: 'download',
            url: url,
            filename: filename,
            saveAs: true
        });
    }
    
    // Copie dans le presse-papiers
    async function copyToClipboard(data) {
        try {
            await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
            return 'Copied successfully';
        } catch (error) {
            return 'Copy failed: ' + error.message;
        }
    }
    
    // Event listener pour les messages du popup
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        console.log('📨 Received:', request.action);
        
        try {
            if (request.action === 'extractConversation') {
                const data = extractConversation();
                sendResponse({ success: true, data: data });
                
            } else if (request.action === 'downloadConversation') {
                const data = extractConversation();
                const filename = request.customFilename || data.conversationMetadata.suggestedFilename;
                downloadConversation(data, filename);
                sendResponse({ success: true });
                
            } else if (request.action === 'copyConversation') {
                const data = extractConversation();
                copyToClipboard(data).then(result => {
                    sendResponse({ success: true, result: result });
                });
                return true; // Async response
            }
        } catch (error) {
            console.error('❌ Error:', error);
            sendResponse({ success: false, error: error.message });
        }
        
        return true;
    });
    
    // Initialiser quand la page est prête
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', safeInit);
    } else {
        safeInit();
    }
    
})();