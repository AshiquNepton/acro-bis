function minimizeForm(formId) {
    const form = document.getElementById(formId);
    const overlay = document.getElementById(formId + '-overlay');
    if (form) {
        const currentState = form.getAttribute('data-state');
        if (currentState === 'minimized') {
            form.setAttribute('data-state', 'normal');
            if (overlay) overlay.classList.add('active');
        } else {
            form.setAttribute('data-state', 'minimized');
            if (overlay) overlay.classList.remove('active');
        }
    }
}

function maximizeForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        const currentState = form.getAttribute('data-state');
        if (currentState === 'maximized') {
            form.setAttribute('data-state', 'normal');
        } else {
            form.setAttribute('data-state', 'maximized');
        }
    }
}

function closeForm(formId) {
    const form = document.getElementById(formId);
    const overlay = document.getElementById(formId + '-overlay');
    const formElement = document.getElementById(formId + '-form');
    let hasData = false;
    if (formElement) {
        const inputs = formElement.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            if (input.value && input.value.trim() !== '') {
                hasData = true;
            }
        });
    }
    const _doClose = () => {
        if (form) {
            form.setAttribute('data-state', 'hidden');
        }
        if (overlay) {
            overlay.classList.remove('active');
        }
    };
    
    if (hasData) {
        if (typeof window.showConfirm === 'function') {
            window.showConfirm('Form has unsaved data. Are you sure you want to close?', function(ok) {
                if (ok) _doClose();
            }, 'warning', 'Unsaved Data', 'Yes, Close', 'Cancel');
        } else {
            _doClose();
        }
    } else {
        _doClose();
    }
}

function openForm(formId) {
    const form = document.getElementById(formId);
    const overlay = document.getElementById(formId + '-overlay');
    if (form) {
        form.setAttribute('data-state', 'normal');
    }
    if (overlay) {
        overlay.classList.add('active');
    }
}

function validateForm(formId) {
    const formElement = document.getElementById(formId + '-form');
    if (!formElement) {
        console.error('Form not found:', formId);
        return false;
    }
    if (!formElement.checkValidity()) {
        formElement.reportValidity();
        return false;
    }
    return true;
}

function resetForm(formId) {
    const formElement = document.getElementById(formId + '-form');
    if (formElement) {
        const _doReset = () => {
            formElement.reset();
            const inputs = formElement.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.classList.remove('error');
            });
        };
        
        if (typeof window.showConfirm === 'function') {
            window.showConfirm('Are you sure you want to reset the form?', function(ok) {
                if (ok) _doReset();
            }, 'warning', 'Reset Form', 'Yes, Reset', 'Cancel');
        } else {
            _doReset();
        }
    }
}

function makeFormDraggable(formId) {
    const form = document.getElementById(formId);
    const header = form.querySelector('.form-header');
    if (!form || !header) return;
    let isDragging = false;
    let currentX, currentY, initialX, initialY, xOffset = 0, yOffset = 0;
    header.addEventListener('mousedown', dragStart);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', dragEnd);
    function dragStart(e) {
        const state = form.getAttribute('data-state');
        if (state === 'maximized' || state === 'minimized') return;
        initialX = e.clientX - xOffset;
        initialY = e.clientY - yOffset;
        if (e.target === header || header.contains(e.target)) {
            isDragging = true;
        }
    }
    function drag(e) {
        if (isDragging) {
            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;
            xOffset = currentX;
            yOffset = currentY;
            form.style.transform = `translate(calc(-50% + ${currentX}px), calc(-50% + ${currentY}px))`;
        }
    }
    function dragEnd() {
        initialX = currentX;
        initialY = currentY;
        isDragging = false;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('.base-form-container');
    forms.forEach(form => {
        makeFormDraggable(form.id);
    });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const visibleForm = document.querySelector('.base-form-container[data-state="normal"], .base-form-container[data-state="maximized"]');
            if (visibleForm) {
                closeForm(visibleForm.id);
            }
        }
    });
});