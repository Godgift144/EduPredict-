/* Global helpers for EduRisk Predictor. */

// Attach the CSRF token to every JSON/fetch write request.
const CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.content || '';

function apiFetch(url, options = {}) {
  const opts = Object.assign({}, options);
  opts.headers = Object.assign({}, opts.headers, {
    'X-CSRFToken': CSRF_TOKEN,
    'Content-Type': 'application/json',
  });
  return fetch(url, opts);
}

// Sensible Chart.js defaults shared by every chart.
if (typeof Chart !== 'undefined') {
  Chart.defaults.font.family = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif";
  Chart.defaults.font.size = 12;
}

// Auto-dismiss flashed alerts after 6 seconds.
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.alert-dismissible').forEach((el) => {
    setTimeout(() => {
      try {
        bootstrap.Alert.getOrCreateInstance(el).close();
      } catch (e) { /* ignore */ }
    }, 6000);
  });
});
