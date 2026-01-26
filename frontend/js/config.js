/**
 * Satellite GIS Extractor - Configuration
 * Settings button → Modal panel approach
 */

const CONFIG = {
    // API endpoint
    API_BASE_URL: 'http://localhost:5001/api',

    // Storage key
    STORAGE_KEY_MAPS_API: 'satellite_gis_google_maps_api_key',

    getGoogleMapsApiKey: function() {
        return localStorage.getItem(this.STORAGE_KEY_MAPS_API) || '';
    },

    setGoogleMapsApiKey: function(key) {
        localStorage.setItem(this.STORAGE_KEY_MAPS_API, key);
    },

    isConfigured: function() {
        return !!this.getGoogleMapsApiKey();
    },

    updateSettingsButton: function() {
        const btn = document.getElementById('settings-btn');
        if (btn) {
            if (this.isConfigured()) {
                btn.classList.add('configured');
            } else {
                btn.classList.remove('configured');
            }
        }
    },

    loadGoogleMapsAPI: function() {
        const apiKey = this.getGoogleMapsApiKey();

        if (!apiKey) {
            this.updateSettingsButton();
            return;
        }

        // Remove existing script if reloading
        const existingScript = document.querySelector('script[src*="maps.googleapis.com"]');
        if (existingScript) {
            existingScript.remove();
        }

        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=drawing,geometry&callback=initializeIntegratedGIS&loading=async`;
        script.async = true;
        script.defer = true;

        script.onload = () => {
            this.updateSettingsButton();
        };

        script.onerror = () => {
            alert('Failed to load Google Maps API. Please check your API key in Settings.');
            this.updateSettingsButton();
        };

        document.body.appendChild(script);
    }
};

// Open settings modal
function openSettings() {
    const modal = document.getElementById('settings-modal');
    const input = document.getElementById('api-key-input');

    if (modal) {
        modal.classList.add('visible');
    }

    // Populate with saved key
    if (input) {
        input.value = CONFIG.getGoogleMapsApiKey();
        input.type = 'password'; // Reset to hidden
    }

    // Reset toggle icon
    const toggle = document.querySelector('.input-toggle');
    if (toggle) toggle.textContent = '👁';
}

// Close settings modal
function closeSettings() {
    const modal = document.getElementById('settings-modal');
    if (modal) {
        modal.classList.remove('visible');
    }
}

// Close on backdrop click
function closeSettingsOnBackdrop(event) {
    if (event.target.id === 'settings-modal') {
        closeSettings();
    }
}

// Save settings and apply
function saveSettings() {
    const input = document.getElementById('api-key-input');
    const key = input.value.trim();

    if (!key) {
        alert('Please enter an API key');
        return;
    }

    if (!key.startsWith('AIza')) {
        alert('Invalid format. Google Maps API keys start with "AIza"');
        return;
    }

    CONFIG.setGoogleMapsApiKey(key);
    closeSettings();
    CONFIG.loadGoogleMapsAPI();
}

// Toggle API key visibility
function toggleApiKeyVisibility() {
    const input = document.getElementById('api-key-input');
    const toggle = document.querySelector('.input-toggle');

    if (input.type === 'password') {
        input.type = 'text';
        toggle.textContent = '🔒';
    } else {
        input.type = 'password';
        toggle.textContent = '👁';
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    CONFIG.updateSettingsButton();

    // Auto-load if already configured
    if (CONFIG.isConfigured()) {
        CONFIG.loadGoogleMapsAPI();
    }
});
