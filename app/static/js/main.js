/**
 * FoodBridge - Main Client JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
  initNotificationCenter();
  initToastSystem();
  initModals();
  initCountdownTimers();
});

/* --------------------------------------------------------------------------
   Mobile Navigation Toggle
   -------------------------------------------------------------------------- */
function initMobileNav() {
  const toggleBtn = document.getElementById('navToggle');
  const navMenu = document.getElementById('navMenu');

  if (toggleBtn && navMenu) {
    toggleBtn.addEventListener('click', () => {
      navMenu.classList.toggle('show');
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!toggleBtn.contains(e.target) && !navMenu.contains(e.target)) {
        navMenu.classList.remove('show');
      }
    });
  }
}

/* --------------------------------------------------------------------------
   Toast Notification System
   -------------------------------------------------------------------------- */
function showToast(title, message, type = 'info', duration = 5000) {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = {
    success: 'fa-check-circle',
    danger: 'fa-exclamation-circle',
    warning: 'fa-triangle-exclamation',
    info: 'fa-circle-info'
  };

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <i class="fa-solid ${icons[type] || 'fa-bell'} toast-icon"></i>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
    <button class="toast-close" aria-label="Close">&times;</button>
  `;

  container.appendChild(toast);

  const closeBtn = toast.querySelector('.toast-close');
  closeBtn.addEventListener('click', () => removeToast(toast));

  if (duration > 0) {
    setTimeout(() => removeToast(toast), duration);
  }
}

function removeToast(toast) {
  toast.style.opacity = '0';
  toast.style.transform = 'translateX(100%)';
  setTimeout(() => {
    if (toast.parentElement) {
      toast.parentElement.removeChild(toast);
    }
  }, 200);
}

function initToastSystem() {
  // Translate Flask flashed messages embedded in DOM to interactive toasts
  const flashMessages = document.querySelectorAll('.flask-flash-message');
  flashMessages.forEach(el => {
    const category = el.dataset.category || 'info';
    const message = el.innerText.trim();
    const title = category === 'danger' ? 'Attention' : category.charAt(0).toUpperCase() + category.slice(1);
    showToast(title, message, category);
    el.remove();
  });
}

/* --------------------------------------------------------------------------
   In-App Notification Center
   -------------------------------------------------------------------------- */
function initNotificationCenter() {
  const bellBtn = document.getElementById('notificationBellBtn');
  const dropdown = document.getElementById('notificationDropdown');
  const badge = document.getElementById('notificationBadge');
  const list = document.getElementById('notificationList');
  const markAllBtn = document.getElementById('markAllReadBtn');

  if (!bellBtn || !dropdown) return;

  // Toggle notification dropdown
  bellBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.toggle('show');
    if (dropdown.classList.contains('show')) {
      fetchNotifications();
    }
  });

  // Close dropdown on outside click
  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target) && !bellBtn.contains(e.target)) {
      dropdown.classList.remove('show');
    }
  });

  // Mark all read button
  if (markAllBtn) {
    markAllBtn.addEventListener('click', async () => {
      try {
        const csrfToken = getCsrfToken();
        const res = await fetch('/api/notifications/mark-all-read', {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
          }
        });
        if (res.ok) {
          if (badge) badge.style.display = 'none';
          document.querySelectorAll('.notification-item.unread').forEach(item => {
            item.classList.remove('unread');
          });
          showToast('Updated', 'All notifications marked as read.', 'success');
        }
      } catch (err) {
        console.error('Error marking all read:', err);
      }
    });
  }

  // Fetch notifications
  async function fetchNotifications() {
    if (!list) return;
    try {
      const res = await fetch('/api/notifications');
      if (res.ok) {
        const data = await res.json();
        renderNotificationItems(data.notifications || []);
      }
    } catch (err) {
      console.error('Failed to load notifications:', err);
    }
  }

  function renderNotificationItems(notifications) {
    if (!notifications.length) {
      list.innerHTML = `
        <li style="padding: 2rem 1rem; text-align: center; color: var(--text-muted); font-size: 0.88rem;">
          <i class="fa-regular fa-bell-slash" style="font-size: 1.5rem; margin-bottom: 0.5rem; display: block; opacity: 0.5;"></i>
          No notifications yet
        </li>
      `;
      return;
    }

    list.innerHTML = notifications.map(n => `
      <li class="notification-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}">
        <div class="notif-title">${escapeHtml(n.title)}</div>
        <div class="notif-msg">${escapeHtml(n.message)}</div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.25rem;">
          <span class="notif-time">${n.created_at}</span>
          ${n.link ? `<a href="${n.link}" style="font-size:0.75rem; font-weight:600; color:var(--primary-700);">View &rarr;</a>` : ''}
        </div>
      </li>
    `).join('');

    // Mark as read when clicking an unread item
    list.querySelectorAll('.notification-item.unread').forEach(item => {
      item.addEventListener('click', async () => {
        const notifId = item.dataset.id;
        try {
          const csrfToken = getCsrfToken();
          await fetch(`/api/notifications/mark-read/${notifId}`, {
            method: 'POST',
            headers: {
              'X-CSRFToken': csrfToken,
              'Content-Type': 'application/json'
            }
          });
          item.classList.remove('unread');
          updateUnreadBadge();
        } catch (err) {
          console.error(err);
        }
      });
    });
  }

  async function updateUnreadBadge() {
    try {
      const res = await fetch('/api/notifications/unread-count');
      if (res.ok) {
        const data = await res.json();
        if (badge) {
          if (data.unread_count > 0) {
            badge.innerText = data.unread_count;
            badge.style.display = 'flex';
          } else {
            badge.style.display = 'none';
          }
        }
      }
    } catch (err) {}
  }
}

/* --------------------------------------------------------------------------
   Confirmation Modal System
   -------------------------------------------------------------------------- */
function initModals() {
  // Auto-bind data-modal-trigger buttons
  document.querySelectorAll('[data-confirm-modal]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const form = btn.closest('form');
      const title = btn.dataset.modalTitle || 'Confirm Action';
      const body = btn.dataset.modalBody || 'Are you sure you want to proceed with this action?';
      const confirmText = btn.dataset.modalConfirmText || 'Confirm';
      const confirmClass = btn.dataset.modalConfirmClass || 'btn-danger';

      openModal({
        title,
        body,
        confirmBtnText: confirmText,
        confirmBtnClass: confirmClass,
        onConfirm: () => {
          if (form) form.submit();
        }
      });
    });
  });
}

function openModal({ title, body, confirmBtnText = 'Confirm', confirmBtnClass = 'btn-primary', onConfirm }) {
  let modalBackdrop = document.getElementById('globalModalBackdrop');
  if (!modalBackdrop) {
    modalBackdrop = document.createElement('div');
    modalBackdrop.id = 'globalModalBackdrop';
    modalBackdrop.className = 'modal-backdrop';
    modalBackdrop.innerHTML = `
      <div class="modal-dialog">
        <div class="modal-header">
          <h3 class="modal-title" id="globalModalTitle">Modal Title</h3>
          <button class="modal-close" id="globalModalCloseBtn">&times;</button>
        </div>
        <div class="modal-body" id="globalModalBody">Modal content</div>
        <div class="modal-footer">
          <button class="btn btn-secondary btn-sm" id="globalModalCancelBtn">Cancel</button>
          <button class="btn btn-sm" id="globalModalConfirmBtn">Confirm</button>
        </div>
      </div>
    `;
    document.body.appendChild(modalBackdrop);
  }

  const titleEl = document.getElementById('globalModalTitle');
  const bodyEl = document.getElementById('globalModalBody');
  const confirmBtn = document.getElementById('globalModalConfirmBtn');
  const cancelBtn = document.getElementById('globalModalCancelBtn');
  const closeBtn = document.getElementById('globalModalCloseBtn');

  titleEl.innerText = title;
  bodyEl.innerHTML = typeof body === 'string' ? body : '';
  confirmBtn.innerText = confirmBtnText;
  confirmBtn.className = `btn btn-sm ${confirmBtnClass}`;

  modalBackdrop.classList.add('show');

  const closeModal = () => {
    modalBackdrop.classList.remove('show');
  };

  closeBtn.onclick = closeModal;
  cancelBtn.onclick = closeModal;
  modalBackdrop.onclick = (e) => {
    if (e.target === modalBackdrop) closeModal();
  };

  confirmBtn.onclick = () => {
    closeModal();
    if (typeof onConfirm === 'function') onConfirm();
  };
}

/* --------------------------------------------------------------------------
   Live Urgency Countdown Timers
   -------------------------------------------------------------------------- */
function initCountdownTimers() {
  const countdownElements = document.querySelectorAll('[data-deadline]');
  if (!countdownElements.length) return;

  function updateCountdowns() {
    const now = new Date().getTime();

    countdownElements.forEach(el => {
      const deadlineStr = el.dataset.deadline;
      const deadlineTime = new Date(deadlineStr).getTime();
      const distance = deadlineTime - now;

      if (distance <= 0) {
        el.innerText = 'Expired';
        el.className = 'badge urgency-critical';
      } else {
        const hours = Math.floor(distance / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));

        if (hours < 1) {
          el.innerText = `${minutes}m remaining`;
          el.className = 'badge urgency-critical';
        } else if (hours < 6) {
          el.innerText = `${hours}h ${minutes}m left`;
          el.className = 'badge urgency-high';
        } else {
          el.innerText = `${hours}h remaining`;
        }
      }
    });
  }

  updateCountdowns();
  setInterval(updateCountdowns, 60000); // refresh every minute
}

/* --------------------------------------------------------------------------
   Utilities
   -------------------------------------------------------------------------- */
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

function escapeHtml(text) {
  if (!text) return '';
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}
