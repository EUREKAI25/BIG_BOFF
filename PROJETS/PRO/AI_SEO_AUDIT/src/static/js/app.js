// AI SEO Audit - Frontend Logic

const API_BASE = window.location.origin;

// Start audit
async function startAudit(formData) {
    const response = await fetch(`${API_BASE}/api/audit/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Audit creation failed');
    }

    return await response.json();
}

// Poll audit status
async function pollAuditStatus(auditId) {
    const response = await fetch(`${API_BASE}/api/audit/${auditId}/status`);

    if (!response.ok) {
        throw new Error('Failed to get audit status');
    }

    return await response.json();
}

// Get audit results
async function getAuditResults(auditId) {
    const response = await fetch(`${API_BASE}/api/audit/${auditId}/results`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to get results');
    }

    return await response.json();
}

// Create checkout session
async function createCheckout(auditId, plan) {
    const response = await fetch(`${API_BASE}/api/payment/create-checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            audit_id: auditId,
            plan: plan,
            success_url: `${window.location.origin}/success?audit_id=${auditId}`,
            cancel_url: `${window.location.origin}/results/${auditId}`
        })
    });

    if (!response.ok) {
        throw new Error('Failed to create checkout session');
    }

    return await response.json();
}

// Format score color
function getScoreColor(score) {
    if (score >= 75) return '#48bb78';  // green
    if (score >= 50) return '#f6ad55';  // orange
    return '#fc8181';  // red
}

// Format score gauge (simple circular progress)
function renderScoreGauge(score) {
    const color = getScoreColor(score);
    const percent = score;

    return `
        <div class="score-gauge">
            <svg width="200" height="200" viewBox="0 0 200 200">
                <circle cx="100" cy="100" r="90" fill="none" stroke="#e2e8f0" stroke-width="12"/>
                <circle cx="100" cy="100" r="90" fill="none" stroke="${color}" stroke-width="12"
                    stroke-dasharray="${percent * 5.65} 565"
                    stroke-linecap="round"
                    transform="rotate(-90 100 100)"/>
            </svg>
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">
                <div class="score-number">${Math.round(score)}</div>
                <div class="score-label">/ 100</div>
            </div>
        </div>
    `;
}

// Handle form submission
document.addEventListener('DOMContentLoaded', () => {
    const auditForm = document.getElementById('auditForm');

    if (auditForm) {
        auditForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = {
                company_name: document.getElementById('company_name').value,
                sector: document.getElementById('sector').value,
                location: document.getElementById('location').value,
                email: document.getElementById('email').value,
                plan: document.getElementById('plan').value,
                language: document.getElementById('language').value || 'fr'
            };

            const submitBtn = auditForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Démarrage de l\'audit...';

            try {
                const audit = await startAudit(formData);

                // Redirect to results page
                window.location.href = `/results/${audit.audit_id}`;

            } catch (error) {
                alert(`Erreur: ${error.message}`);
                submitBtn.disabled = false;
                submitBtn.textContent = 'Lancer l\'audit gratuit';
            }
        });
    }
});

// Auto-redirect to results when audit completes (for results page polling)
async function waitForAuditCompletion(auditId) {
    const maxAttempts = 60;  // 2 minutes max (2s interval)
    let attempts = 0;

    const poll = setInterval(async () => {
        attempts++;

        try {
            const status = await pollAuditStatus(auditId);

            // Update progress if element exists
            const progressEl = document.getElementById('progress');
            if (progressEl) {
                progressEl.textContent = `${status.progress}%`;
            }

            const stepEl = document.getElementById('currentStep');
            if (stepEl) {
                stepEl.textContent = status.current_step;
            }

            if (status.status === 'completed') {
                clearInterval(poll);
                window.location.reload();  // Reload to show results
            } else if (status.status === 'failed' || attempts >= maxAttempts) {
                clearInterval(poll);
                alert('L\'audit a échoué ou a pris trop de temps. Veuillez réessayer.');
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 2000);  // Poll every 2 seconds
}
