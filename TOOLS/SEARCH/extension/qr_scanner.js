/**
 * BIG_BOFF Search — QR Scanner
 * Scan QR codes de partage via caméra (Phase 4 P2P)
 *
 * Utilise html5-qrcode pour scanner QR codes
 * https://github.com/mebjas/html5-qrcode
 */

class QRScanner {
    constructor() {
        this.scanner = null;
        this.isScanning = false;
        this.onSuccess = null;
        this.onError = null;
    }

    /**
     * Démarre le scan QR via caméra
     * @param {string} elementId - ID de l'élément DOM pour la vidéo
     * @param {function} onSuccess - Callback succès (data)
     * @param {function} onError - Callback erreur (error)
     */
    async start(elementId, onSuccess, onError) {
        this.onSuccess = onSuccess;
        this.onError = onError;

        try {
            // Vérifier si html5-qrcode est chargé
            if (typeof Html5Qrcode === 'undefined') {
                throw new Error('Bibliothèque html5-qrcode non chargée');
            }

            this.scanner = new Html5Qrcode(elementId);

            const config = {
                fps: 10,
                qrbox: { width: 250, height: 250 },
                aspectRatio: 1.0
            };

            await this.scanner.start(
                { facingMode: "environment" }, // Caméra arrière si mobile
                config,
                this._onScanSuccess.bind(this),
                this._onScanError.bind(this)
            );

            this.isScanning = true;
            console.log('QR Scanner démarré');

        } catch (error) {
            console.error('Erreur démarrage scanner:', error);
            if (this.onError) {
                this.onError(error);
            }
        }
    }

    /**
     * Arrête le scan
     */
    async stop() {
        if (this.scanner && this.isScanning) {
            try {
                await this.scanner.stop();
                this.isScanning = false;
                console.log('QR Scanner arrêté');
            } catch (error) {
                console.error('Erreur arrêt scanner:', error);
            }
        }
    }

    /**
     * Callback succès scan
     * @private
     */
    _onScanSuccess(decodedText) {
        console.log('QR Code scanné:', decodedText.substring(0, 50) + '...');

        // Arrêter le scan après succès
        this.stop();

        // Décoder et vérifier QR
        const shareData = this._verifyQR(decodedText);

        if (shareData && this.onSuccess) {
            this.onSuccess(shareData);
        } else if (this.onError) {
            this.onError(new Error('QR code invalide ou expiré'));
        }
    }

    /**
     * Callback erreur scan (ignorée, erreurs normales pendant scan)
     * @private
     */
    _onScanError(error) {
        // Ignorer les erreurs de scan normales (pas de QR visible)
        // console.log('Scan...', error);
    }

    /**
     * Vérifie et décode un QR code
     * @param {string} qrData - Données QR en base64
     * @returns {object|null} Données décodées si valide
     */
    _verifyQR(qrData) {
        try {
            // Décoder base64
            const shareJson = atob(qrData);
            const shareData = JSON.parse(shareJson);

            // Vérifier version
            if (shareData.version !== '1.0') {
                console.error('Version QR incompatible:', shareData.version);
                return null;
            }

            // Vérifier type
            if (shareData.type !== 'share_permission') {
                console.error('Type QR invalide:', shareData.type);
                return null;
            }

            // Vérifier expiration
            if (shareData.expires_at) {
                const expiresAt = new Date(shareData.expires_at);
                const now = new Date();
                if (now > expiresAt) {
                    console.error('QR code expiré');
                    return null;
                }
            }

            // TODO Phase 4 : Vérifier signature Ed25519
            // Pour l'instant, on fait confiance si le format est correct

            console.log('QR code valide:', shareData);
            return shareData;

        } catch (error) {
            console.error('Erreur décodage QR:', error);
            return null;
        }
    }
}

/**
 * Affiche modal preview partage avec accept/refuse
 * @param {object} shareData - Données QR décodées
 * @param {function} onAccept - Callback si accepté
 * @param {function} onRefuse - Callback si refusé
 */
function showSharePreview(shareData, onAccept, onRefuse) {
    const modal = document.createElement('div');
    modal.id = 'share-preview-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;

    const perm = shareData.permission;
    const fromAlias = shareData.from_alias || 'Utilisateur';
    const fromId = shareData.from_user_id;
    const scope = `${perm.scope_type}:${perm.scope_value}`;
    const mode = perm.mode === 'consultation' ? 'Consultation (temps réel)' : 'Partage (copie)';

    modal.innerHTML = `
        <div style="background: white; padding: 30px; border-radius: 12px; max-width: 500px; width: 90%;">
            <h2 style="margin-top: 0; color: #333;">
                <i class="fa-solid fa-share-nodes" style="color: #4CAF50; margin-right: 10px;"></i>
                Partage reçu
            </h2>

            <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 5px 0;">
                    <strong>De :</strong> ${fromAlias}
                </p>
                <p style="margin: 5px 0; font-size: 12px; color: #666;">
                    ${fromId}
                </p>
                <p style="margin: 15px 0 5px 0;">
                    <strong>Scope :</strong> ${scope}
                </p>
                <p style="margin: 5px 0;">
                    <strong>Mode :</strong> ${mode}
                </p>
            </div>

            <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; font-size: 14px;">
                ${perm.mode === 'consultation' ?
                    '<i class="fa-solid fa-eye"></i> Vous verrez les éléments en temps réel. Révocable instantanément.' :
                    '<i class="fa-solid fa-copy"></i> Vous recevrez une copie locale. Snapshot figé si révoqué.'
                }
            </div>

            <div style="display: flex; gap: 10px; margin-top: 25px;">
                <button id="refuse-share" style="
                    flex: 1;
                    padding: 12px;
                    border: 1px solid #ccc;
                    background: white;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                ">
                    <i class="fa-solid fa-times"></i> Refuser
                </button>
                <button id="accept-share" style="
                    flex: 1;
                    padding: 12px;
                    border: none;
                    background: #4CAF50;
                    color: white;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: bold;
                ">
                    <i class="fa-solid fa-check"></i> Accepter
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Event listeners
    document.getElementById('refuse-share').addEventListener('click', () => {
        modal.remove();
        if (onRefuse) onRefuse();
    });

    document.getElementById('accept-share').addEventListener('click', () => {
        modal.remove();
        if (onAccept) onAccept(shareData);
    });
}

/**
 * Accepte un partage (appel API permissions/grant)
 * @param {object} shareData - Données QR
 */
async function acceptShare(shareData) {
    try {
        // Appeler API locale pour accepter
        // L'API locale fera appel au relay avec JWT token

        const response = await fetch('http://127.0.0.1:7777/api/share/accept', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                from_user_id: shareData.from_user_id,
                permission: shareData.permission,
                signature: shareData.signature
            })
        });

        const result = await response.json();

        if (result.success) {
            showNotification('✅ Partage accepté !', 'success');
            // Refresh results si nécessaire
        } else {
            showNotification('❌ Erreur : ' + result.error, 'error');
        }

    } catch (error) {
        console.error('Erreur accept share:', error);
        showNotification('❌ Erreur lors de l\'acceptation', 'error');
    }
}

/**
 * Affiche notification toast
 * @param {string} message - Message
 * @param {string} type - Type (success, error, info)
 */
function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        z-index: 10001;
        font-size: 14px;
    `;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = 'opacity 0.3s';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Export pour utilisation dans l'extension
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { QRScanner, showSharePreview, acceptShare };
}
