/**
 * common/static/common/js/csrf.js
 * Single shared CSRF-token reader. Load this before any script that
 * needs it (payroll_form.js, documents_modal.js, future modals).
 */
window.getCsrf = function () {
    var m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
};