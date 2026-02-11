/**
 * BIG_BOFF Identity Onboarding
 * Module d'initialisation de l'identité P2P décentralisée
 *
 * Usage: Importer dans popup.js et appeler checkIdentityStatus() au chargement
 */

const ONBOARDING_API = "http://127.0.0.1:7777";

/**
 * Vérifie le statut de l'identité et affiche l'onboarding si nécessaire
 */
async function checkIdentityStatus() {
  try {
    const response = await fetch(`${ONBOARDING_API}/api/identity/status`);
    const status = await response.json();

    // Si identité non initialisée, afficher onboarding
    if (!status.initialized) {
      showOnboarding();
    }
  } catch (error) {
    console.warn("Impossible de vérifier le statut de l'identité :", error);
    // Ne pas bloquer l'app si le module identity n'est pas disponible
  }
}

/**
 * Injecte et affiche le modal d'onboarding
 */
function showOnboarding() {
  // HTML du modal d'onboarding
  const onboardingHTML = `
    <div id="onboarding-overlay" style="
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.6);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
      animation: fadeIn 0.3s ease;
    ">
      <div id="onboarding-card" style="
        background: white;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        width: 460px;
        max-width: 90vw;
        padding: 32px;
        animation: slideUp 0.3s ease;
      ">
        <div style="text-align: center; margin-bottom: 24px;">
          <h1 style="font-size: 24px; font-weight: 600; color: #333; margin-bottom: 8px;">
            Identité décentralisée
          </h1>
          <p style="font-size: 14px; color: #777;">
            Générez votre identité cryptographique unique
          </p>
        </div>

        <!-- Étape 1 : Formulaire -->
        <div id="ob-step-form" class="ob-step" style="display: block;">
          <div style="margin-bottom: 20px;">
            <label style="display: block; font-size: 13px; font-weight: 500; color: #555; margin-bottom: 6px;">
              Alias (optionnel)
            </label>
            <input type="text" id="ob-alias-input" placeholder="Votre nom ou pseudo" style="
              width: 100%;
              padding: 10px 12px;
              border: 1px solid #ddd;
              border-radius: 8px;
              font-size: 14px;
            ">
          </div>

          <div style="display: flex; align-items: center; margin-bottom: 16px;">
            <input type="checkbox" id="ob-protect-checkbox" style="
              width: 18px; height: 18px; margin-right: 8px; cursor: pointer;
            ">
            <label for="ob-protect-checkbox" style="font-size: 13px; color: #555; cursor: pointer;">
              Protéger avec un mot de passe
            </label>
          </div>

          <div id="ob-password-section" style="display: none; margin-bottom: 16px;">
            <label style="display: block; font-size: 13px; font-weight: 500; color: #555; margin-bottom: 6px;">
              Mot de passe
            </label>
            <input type="password" id="ob-password-input" placeholder="Minimum 8 caractères" style="
              width: 100%;
              padding: 10px 12px;
              border: 1px solid #ddd;
              border-radius: 8px;
              font-size: 14px;
            ">
          </div>

          <button id="ob-generate-btn" style="
            width: 100%;
            padding: 12px 16px;
            font-size: 14px;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
            color: white;
            transition: all 0.2s ease;
          ">
            Générer mon identité
          </button>
        </div>

        <!-- Étape 2 : Loading -->
        <div id="ob-step-loading" class="ob-step" style="display: none; text-align: center; padding: 20px 0;">
          <div style="
            width: 50px; height: 50px;
            margin: 0 auto 20px;
            border: 4px solid #f0f0f0;
            border-top-color: #FF6B35;
            border-radius: 50%;
            animation: spin 1s linear infinite;
          "></div>
          <p style="font-size: 15px; color: #666; margin-bottom: 8px;">Génération en cours...</p>
          <small style="font-size: 12px; color: #999;">
            Création des clés cryptographiques RSA-4096 + Ed25519
          </small>
        </div>

        <!-- Étape 3 : Succès -->
        <div id="ob-step-success" class="ob-step" style="display: none; text-align: center;">
          <div style="
            width: 64px; height: 64px;
            background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
          ">
            <svg viewBox="0 0 24 24" style="
              width: 36px; height: 36px;
              stroke: white; stroke-width: 3; fill: none;
              stroke-linecap: round; stroke-linejoin: round;
            ">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          </div>

          <h2 style="font-size: 20px; font-weight: 600; color: #333; margin-bottom: 12px;">
            Identité créée !
          </h2>
          <p style="font-size: 14px; color: #666; margin-bottom: 20px;">
            Votre User ID unique :
          </p>

          <div id="ob-user-id-display" style="
            background: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 20px;
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            color: #333;
            word-break: break-all;
          ">
            bigboff_...
          </div>

          <div style="display: flex; gap: 8px;">
            <button id="ob-backup-btn" style="
              flex: 1;
              padding: 12px 16px;
              font-size: 14px;
              font-weight: 600;
              border: none;
              border-radius: 8px;
              cursor: pointer;
              background: #f5f5f5;
              color: #555;
            ">
              Sauvegarder
            </button>
            <button id="ob-start-btn" style="
              flex: 1;
              padding: 12px 16px;
              font-size: 14px;
              font-weight: 600;
              border: none;
              border-radius: 8px;
              cursor: pointer;
              background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%);
              color: white;
            ">
              Commencer
            </button>
          </div>
        </div>
      </div>
    </div>

    <style>
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      @keyframes slideUp {
        from { transform: translateY(30px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
      }
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
    </style>
  `;

  // Injecter dans le DOM
  document.body.insertAdjacentHTML('beforeend', onboardingHTML);

  // Attacher les event listeners
  attachOnboardingListeners();
}

/**
 * Attache tous les event listeners du modal d'onboarding
 */
function attachOnboardingListeners() {
  const protectCheckbox = document.getElementById("ob-protect-checkbox");
  const passwordSection = document.getElementById("ob-password-section");
  const passwordInput = document.getElementById("ob-password-input");
  const aliasInput = document.getElementById("ob-alias-input");
  const generateBtn = document.getElementById("ob-generate-btn");
  const startBtn = document.getElementById("ob-start-btn");
  const backupBtn = document.getElementById("ob-backup-btn");
  const userIdDisplay = document.getElementById("ob-user-id-display");

  let generatedUserId = null;

  // Toggle section mot de passe
  protectCheckbox.addEventListener("change", () => {
    passwordSection.style.display = protectCheckbox.checked ? "block" : "none";
    if (protectCheckbox.checked) {
      passwordInput.focus();
    }
  });

  // Générer identité
  generateBtn.addEventListener("click", async () => {
    const alias = aliasInput.value.trim() || "User";
    const protect = protectCheckbox.checked;
    const password = protect ? passwordInput.value : null;

    // Validation
    if (protect && (!password || password.length < 8)) {
      alert("Le mot de passe doit contenir au moins 8 caractères");
      return;
    }

    // Passer à l'étape loading
    showStep("loading");

    try {
      const response = await fetch(`${ONBOARDING_API}/api/identity/init`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ alias, password })
      });

      const result = await response.json();

      if (result.error) {
        alert(`Erreur : ${result.error}`);
        showStep("form");
        return;
      }

      if (result.success) {
        generatedUserId = result.user_id;
        userIdDisplay.textContent = result.user_id;

        // Petit délai pour effet UX
        setTimeout(() => showStep("success"), 500);
      }
    } catch (error) {
      console.error("Erreur génération identité :", error);
      alert("Erreur de connexion au serveur. Vérifiez qu'il est démarré.");
      showStep("form");
    }
  });

  // Bouton Commencer
  startBtn.addEventListener("click", () => {
    document.getElementById("onboarding-overlay").remove();
    // Recharger la page si nécessaire
    if (typeof refreshApp === "function") {
      refreshApp();
    }
  });

  // Bouton Sauvegarder
  backupBtn.addEventListener("click", async () => {
    try {
      const response = await fetch(`${ONBOARDING_API}/api/identity/public_key`);
      const identity = await response.json();

      const backup = {
        user_id: identity.user_id,
        public_key_rsa: identity.public_key_rsa,
        public_key_ed25519: identity.public_key_ed25519,
        backup_date: new Date().toISOString()
      };

      const blob = new Blob([JSON.stringify(backup, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = `bigboff_identity_${identity.user_id.slice(8, 16)}.json`;
      a.click();

      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Erreur backup :", error);
      alert("Erreur lors de la sauvegarde");
    }
  });

  /**
   * Affiche une étape spécifique du modal
   */
  function showStep(step) {
    document.getElementById("ob-step-form").style.display = step === "form" ? "block" : "none";
    document.getElementById("ob-step-loading").style.display = step === "loading" ? "block" : "none";
    document.getElementById("ob-step-success").style.display = step === "success" ? "block" : "none";
  }
}

// Export pour utilisation dans popup.js
if (typeof module !== "undefined" && module.exports) {
  module.exports = { checkIdentityStatus };
}
