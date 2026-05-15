/* ─────────────────────────────────────────────
   Qlockain — Global JavaScript
   All interactions, animations, utilities
───────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  initScrollAnimations();
  initNavHighlight();
  initCopyHashes();
  initTooltips();
  startPulseIndicators();
  initSidebarActive();
  animateStatCounters();
  initConsoleBranding();
  initKeyboardShortcuts();
});

/* ── Scroll-triggered fade animations ────────────── */
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.fade-in').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = 'opacity 0.55s cubic-bezier(0.4,0,0.2,1), transform 0.55s cubic-bezier(0.4,0,0.2,1)';
    observer.observe(el);
  });
}

/* ── Navbar active link highlight ────────────────── */
function initNavHighlight() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '#' && path.startsWith(href) && href !== '/') {
      link.classList.add('active');
    }
  });
}

/* ── Click-to-copy on hash displays ──────────────── */
function initCopyHashes() {
  document.querySelectorAll('.hash-display').forEach(el => {
    el.style.cursor = 'pointer';
    el.title = 'Click to copy hash';

    el.addEventListener('click', async () => {
      const text = el.textContent.trim().replace(/\s+/g, '');
      try {
        await navigator.clipboard.writeText(text);
        const saved = el.innerHTML;
        const savedColor = el.style.borderColor;
        el.style.borderColor = 'var(--green)';
        el.innerHTML = '<span style="color:var(--green);">✓ Copied to clipboard!</span>';
        setTimeout(() => {
          el.innerHTML = saved;
          el.style.borderColor = savedColor;
        }, 1400);
      } catch (err) {
        // Fallback
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
    });
  });
}

/* ── Bootstrap Tooltips init ─────────────────────── */
function initTooltips() {
  if (typeof bootstrap !== 'undefined') {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
      new bootstrap.Tooltip(el, { trigger: 'hover' });
    });
  }
}

/* ── Pulsing glow indicators ─────────────────────── */
function startPulseIndicators() {
  document.querySelectorAll('.pulse-glow').forEach(el => {
    let bright = false;
    setInterval(() => {
      bright = !bright;
      el.style.transition = 'box-shadow 0.7s ease';
      el.style.boxShadow = bright
        ? '0 0 35px rgba(0,245,212,0.55), 0 0 70px rgba(0,245,212,0.25)'
        : '0 0 12px rgba(0,245,212,0.2)';
    }, 2800);
  });
}

/* ── Sidebar active state ────────────────────────── */
function initSidebarActive() {
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar-nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && path === href) {
      link.classList.add('active');
    }
  });
}

/* ── Animated stat counters ──────────────────────── */
function animateStatCounters() {
  const counters = document.querySelectorAll('.stat-value');
  if (!counters.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const raw = el.textContent.trim();
        // Extract leading number
        const match = raw.match(/^(\d+)/);
        if (match) {
          const target = parseInt(match[1]);
          const suffix = raw.slice(match[0].length); // e.g. '+', '%', '✓', '✗'
          countUp(el, target, suffix, 1200);
        }
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.3 });

  counters.forEach(el => observer.observe(el));
}

function countUp(el, target, suffix, duration) {
  const start = performance.now();
  const easeOut = t => 1 - Math.pow(1 - t, 3);

  function frame(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const current = Math.round(easeOut(progress) * target);
    el.textContent = current + (suffix || '');
    if (progress < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

/* ── Keyboard shortcuts ──────────────────────────── */
function initKeyboardShortcuts() {
  document.addEventListener('keydown', e => {
    // Only trigger if not in an input/textarea
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.altKey) {
      switch (e.key) {
        case 'b': e.preventDefault(); navigate('/blockchain'); break;
        case 'd': e.preventDefault(); navigate('/dashboard'); break;
        case 'v': e.preventDefault(); navigate('/verify'); break;
        case 'a': e.preventDefault(); navigate('/alerts'); break;
        case 'u': e.preventDefault(); navigate('/upload'); break;
      }
    }
  });
}

function navigate(path) {
  window.location.href = path;
}

/* ── Console branding ────────────────────────────── */
function initConsoleBranding() {
  console.log(
    '\n%c  QLOCKAIN  \n',
    'background:linear-gradient(135deg,#00f5d4,#0066ff);color:#050a18;font-size:1.6rem;font-weight:900;padding:0.75rem 3rem;border-radius:6px;'
  );
  console.log(
    '%c  Blockchain-Powered Digital Identity Vault  ',
    'color:#00f5d4;font-size:0.85rem;font-family:monospace;letter-spacing:0.08em;'
  );
  console.log(
    '%c  ⚠  All activity is logged and anchored to the blockchain.  ',
    'color:#ff3366;font-size:0.75rem;font-family:monospace;'
  );
  console.log(
    '%c  Alt+D=Dashboard  Alt+B=Blockchain  Alt+V=Verify  Alt+A=Alerts  ',
    'color:#4a5568;font-size:0.7rem;font-family:monospace;'
  );
}

/* ── File drag-and-drop global helper ────────────── */
function initDropZone(dropZoneId, fileInputId, previewCallback) {
  const zone = document.getElementById(dropZoneId);
  const input = document.getElementById(fileInputId);
  if (!zone || !input) return;

  ['dragenter', 'dragover'].forEach(evt => {
    zone.addEventListener(evt, e => {
      e.preventDefault();
      zone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(evt => {
    zone.addEventListener(evt, e => {
      e.preventDefault();
      zone.classList.remove('dragover');
    });
  });

  zone.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files.length) {
      input.files = files;
      if (previewCallback) previewCallback(input);
    }
  });
}

/* ── Toast notification system ───────────────────── */
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('flashContainer') || createToastContainer();
  const toast = document.createElement('div');
  toast.className = `flash-msg ${type}`;

  const icons = { success: 'check-circle', danger: 'exclamation-triangle', warning: 'exclamation-circle', info: 'info-circle' };
  const icon = icons[type] || 'info-circle';

  toast.innerHTML = `
    <i class="bi bi-${icon} ${type === 'success' ? 'text-success' : type === 'danger' ? 'text-danger' : type === 'warning' ? 'text-warning' : ''}"></i>
    <span>${message}</span>
    <button onclick="this.parentElement.remove()" style="margin-left:auto;background:none;border:none;color:var(--text-dim);cursor:pointer;">&times;</button>
  `;

  container.appendChild(toast);

  // Animate in
  toast.style.opacity = '0';
  toast.style.transform = 'translateX(20px)';
  requestAnimationFrame(() => {
    toast.style.transition = 'all 0.3s ease';
    toast.style.opacity = '1';
    toast.style.transform = 'translateX(0)';
  });

  // Auto remove
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function createToastContainer() {
  const div = document.createElement('div');
  div.id = 'flashContainer';
  div.className = 'flash-container';
  document.body.appendChild(div);
  return div;
}

/* ── Confirm delete with styled dialog ───────────── */
function confirmDelete(message, formId) {
  // Use native confirm as fallback (can be enhanced later)
  if (confirm(message)) {
    document.getElementById(formId).submit();
  }
}

/* ── Format bytes to human-readable ─────────────── */
function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/* ── Relative time formatting ────────────────────── */
function timeAgo(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - date) / 1000);

  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

/* ── Truncate hash for display ───────────────────── */
function truncateHash(hash, chars = 16) {
  if (!hash) return '—';
  return hash.slice(0, chars) + '...' + hash.slice(-8);
}

/* ── Live clock for dashboard ────────────────────── */
function startLiveClock(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  function tick() {
    const now = new Date();
    el.textContent = now.toLocaleTimeString('en-GB', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }
  tick();
  setInterval(tick, 1000);
}

// Auto-start live clock if element exists
startLiveClock('liveTime');

/* ── Block mining loading spinner ────────────────── */
function showMiningSpinner(buttonEl, text = 'Mining Block...') {
  if (!buttonEl) return;
  buttonEl.disabled = true;
  buttonEl.dataset.originalText = buttonEl.innerHTML;
  buttonEl.innerHTML = `
    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
    ${text}
  `;
}

function hideMiningSpinner(buttonEl) {
  if (!buttonEl || !buttonEl.dataset.originalText) return;
  buttonEl.disabled = false;
  buttonEl.innerHTML = buttonEl.dataset.originalText;
}

/* ── Password strength checker ───────────────────── */
function checkPasswordStrength(password) {
  let score = 0;
  const checks = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[^A-Za-z0-9]/.test(password)
  };
  score = Object.values(checks).filter(Boolean).length;
  const levels = [
    { label: '', color: 'transparent', width: '0%' },
    { label: 'Very Weak', color: 'var(--red)', width: '20%' },
    { label: 'Weak', color: '#ff6b35', width: '40%' },
    { label: 'Fair', color: 'var(--yellow)', width: '60%' },
    { label: 'Good', color: '#a8e063', width: '80%' },
    { label: 'Strong', color: 'var(--green)', width: '100%' }
  ];
  return { score, ...levels[Math.min(score, 5)], checks };
}

/* ── Blockchain block type colors ────────────────── */
const BLOCK_TYPE_COLORS = {
  'GENESIS': 'var(--cyan)',
  'IDENTITY_REGISTRATION': 'var(--green)',
  'DOCUMENT_UPLOAD': '#6ea8fe',
  'VERIFICATION_LOG': 'var(--yellow)',
  'DEFAULT': 'var(--text-mute)'
};

function getBlockColor(type) {
  return BLOCK_TYPE_COLORS[type] || BLOCK_TYPE_COLORS['DEFAULT'];
}

/* ── Auto-hide elements after delay ─────────────── */
function autoHide(selector, delayMs = 5000) {
  document.querySelectorAll(selector).forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s ease';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, delayMs);
  });
}

// Auto-hide flash messages
autoHide('.flash-msg', 5000);

/* ── Smooth scroll to element ────────────────────── */
function scrollTo(selector) {
  const el = document.querySelector(selector);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* ── Table row hover highlight ───────────────────── */
document.querySelectorAll('.table-ql tbody tr').forEach(row => {
  row.style.transition = 'background 0.2s ease';
  row.addEventListener('mouseenter', () => {
    row.style.background = 'rgba(0,245,212,0.04)';
  });
  row.addEventListener('mouseleave', () => {
    row.style.background = '';
  });
});

/* ── Prevent double-form-submit ──────────────────── */
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', function () {
    const submitBtns = this.querySelectorAll('[type="submit"]');
    submitBtns.forEach(btn => {
      setTimeout(() => { btn.disabled = true; }, 10);
      setTimeout(() => { btn.disabled = false; }, 8000);
    });
  });
});
