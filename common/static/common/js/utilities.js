function getCsrfToken() {
    var m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
}

// Replace all inline showNotification() copies with this:
function showNotification(message, type) {
    if (typeof showToast === 'function') {
        showToast(message, type);  // delegates to alerts.html's showToast
    }
}