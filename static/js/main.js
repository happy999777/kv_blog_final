/* ============================================================
   KV BLOG — Premium JavaScript
   ============================================================ */

'use strict';

/* ── Page Loader ─────────────────────────────────────────── */
window.addEventListener('load', () => {
  const loader = document.getElementById('page-loader');
  if (loader) {
    setTimeout(() => loader.classList.add('hidden'), 400);
  }
  // Trigger page transition
  document.body.classList.add('page-transition');
});

/* ── Navbar Scroll Effect ────────────────────────────────── */
(function initNavbar() {
  const nav = document.getElementById('mainNav');
  if (!nav) return;
  const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 40);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();

/* ── Live Search Suggestions ─────────────────────────────── */
(function initSearch() {
  const input = document.getElementById('navSearchInput');
  const box   = document.getElementById('searchSuggestions');
  if (!input || !box) return;

  let timer;
  input.addEventListener('input', () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (q.length < 2) { box.style.display = 'none'; return; }
    timer = setTimeout(() => fetchSuggestions(q), 280);
  });

  async function fetchSuggestions(q) {
    try {
      const r = await fetch(`/api/search/?q=${encodeURIComponent(q)}&limit=5`);
      const data = await r.json();
      if (!data.results || !data.results.length) { box.style.display = 'none'; return; }
      box.innerHTML = data.results.map(p => `
        <a href="${p.url}" class="suggestion-item">
          <img src="${p.image || '/static/images/placeholder.jpg'}" class="suggestion-img" alt="">
          <div>
            <div class="suggestion-title">${p.title}</div>
            <div class="suggestion-cat">${p.category || ''}</div>
          </div>
        </a>`).join('');
      box.style.display = 'block';
    } catch(e) { box.style.display = 'none'; }
  }

  document.addEventListener('click', e => {
    if (!input.contains(e.target) && !box.contains(e.target)) box.style.display = 'none';
  });
})();

/* ── Hero Image Slider ───────────────────────────────────── */
(function initSlider() {
  const slider = document.querySelector('.hero-slider');
  if (!slider) return;
  const track  = slider.querySelector('.slider-track');
  const slides  = slider.querySelectorAll('.slide');
  const dots    = slider.querySelectorAll('.slider-dot');
  if (!slides.length) return;

  let current = 0, timer, paused = false;

  function goTo(n) {
    current = (n + slides.length) % slides.length;
    track.style.transform = `translateX(-${current * 100}%)`;
    dots.forEach((d, i) => d.classList.toggle('active', i === current));
  }

  function next() { goTo(current + 1); }
  function prev() { goTo(current - 1); }

  function startTimer() { timer = setInterval(next, 5000); }
  function stopTimer()  { clearInterval(timer); }

  slider.querySelector('.slider-next')?.addEventListener('click', () => { stopTimer(); next(); startTimer(); });
  slider.querySelector('.slider-prev')?.addEventListener('click', () => { stopTimer(); prev(); startTimer(); });
  dots.forEach((d, i) => d.addEventListener('click', () => { stopTimer(); goTo(i); startTimer(); }));

  slider.addEventListener('mouseenter', stopTimer);
  slider.addEventListener('mouseleave', startTimer);

  // Touch support
  let tx = 0;
  slider.addEventListener('touchstart', e => { tx = e.touches[0].clientX; stopTimer(); }, { passive: true });
  slider.addEventListener('touchend',   e => {
    const dx = e.changedTouches[0].clientX - tx;
    if (Math.abs(dx) > 50) dx < 0 ? next() : prev();
    startTimer();
  });

  goTo(0);
  startTimer();
})();

/* ── Animated Counters ───────────────────────────────────── */
function animateCounter(el) {
  const target = parseInt(el.dataset.count || el.textContent, 10);
  if (isNaN(target)) return;
  const duration = 1800;
  const step = target / (duration / 16);
  let current = 0;
  const update = () => {
    current = Math.min(current + step, target);
    el.textContent = Math.floor(current).toLocaleString();
    if (current < target) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

/* ── Intersection Observer (fade-up + counters) ─────────── */
(function initObserver() {
  const io = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      el.classList.add('visible');
      if (el.classList.contains('stat-number') || el.classList.contains('counter-number')) {
        animateCounter(el);
      }
      io.unobserve(el);
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('.fade-up, .stat-number, .counter-number').forEach(el => io.observe(el));
})();

/* ── Reading Progress Bar ────────────────────────────────── */
(function initReadingProgress() {
  const bar = document.getElementById('readingProgressBar');
  if (!bar) return;
  window.addEventListener('scroll', () => {
    const h = document.documentElement;
    const pct = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
    bar.style.width = Math.min(pct, 100) + '%';
  }, { passive: true });
})();

/* ── Toast Notifications ─────────────────────────────────── */
window.KVToast = {
  show(msg, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const icons = { success:'fa-check-circle', error:'fa-times-circle', warning:'fa-exclamation-triangle', info:'fa-info-circle' };
    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    toast.innerHTML = `
      <i class="fas ${icons[type] || icons.info} toast-icon toast-${type}"></i>
      <span class="toast-msg">${msg}</span>
      <button class="toast-close" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.classList.add('hiding');
      setTimeout(() => toast.remove(), 400);
    }, duration);
  }
};

// Show Django messages as toasts
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-toast]').forEach(el => {
    KVToast.show(el.dataset.toast, el.dataset.toastType || 'info');
    el.remove();
  });
});

/* ── Newsletter Popup ────────────────────────────────────── */
(function initPopup() {
  const popup = document.getElementById('newsletterPopup');
  if (!popup) return;
  if (localStorage.getItem('kv_popup_seen')) return;
  setTimeout(() => popup.classList.add('show'), 8000);
  popup.querySelector('.popup-close')?.addEventListener('click', closePopup);
  popup.addEventListener('click', e => { if (e.target === popup) closePopup(); });
  function closePopup() {
    popup.classList.remove('show');
    localStorage.setItem('kv_popup_seen', '1');
  }
  // Newsletter submit
  popup.querySelector('form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    closePopup();
    KVToast.show('🎉 Subscribed successfully!', 'success');
  });
})();

/* ── Like Button ─────────────────────────────────────────── */
document.querySelectorAll('.like-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const identifier = btn.dataset.blogId || btn.dataset.slug;
    if (!identifier) return;

    try {
      const r = await fetch(`/blogs/${identifier}/like/`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': getCsrf(),
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({})
      });

      const data = await (r.headers.get('content-type')?.includes('application/json') ? r.json() : Promise.resolve({}));
      if (!r.ok) {
        throw new Error(data.error || 'Please login to like posts');
      }

      btn.classList.toggle('liked', data.liked === true);
      const countEl = btn.querySelector('.like-count');
      if (countEl && typeof data.count !== 'undefined') countEl.textContent = data.count;
    } catch (error) {
      KVToast.show(error.message || 'Please login to like posts', 'warning');
    }
  });
});

/* ── Share Buttons ───────────────────────────────────────── */
document.querySelectorAll('.share-copy').forEach(btn => {
  btn.addEventListener('click', () => {
    navigator.clipboard?.writeText(window.location.href)
      .then(() => KVToast.show('Link copied to clipboard!', 'success'))
      .catch(() => KVToast.show('Could not copy link', 'error'));
  });
});

/* ── Image Upload Preview ────────────────────────────────── */
(function initImageUpload() {
  const zone    = document.querySelector('.image-upload-zone');
  const input   = document.getElementById('id_featured_image') || document.getElementById('imageInput');
  const preview = document.querySelector('.image-preview');
  if (!zone || !input || !preview) return;

  zone.addEventListener('click', () => input.click());
  ['dragenter','dragover'].forEach(e => zone.addEventListener(e, (ev) => { ev.preventDefault(); zone.classList.add('dragover'); }));
  ['dragleave','drop'].forEach(e => zone.addEventListener(e, (ev) => { ev.preventDefault(); zone.classList.remove('dragover'); }));
  zone.addEventListener('drop', e => { if (e.dataTransfer.files[0]) showPreview(e.dataTransfer.files[0]); });
  input.addEventListener('change', () => { if (input.files[0]) showPreview(input.files[0]); });

  function showPreview(file) {
    const reader = new FileReader();
    reader.onload = e => { preview.src = e.target.result; preview.style.display = 'block'; };
    reader.readAsDataURL(file);
  }
})();

/* ── Bookmark Toggle ─────────────────────────────────────── */
document.querySelectorAll('.bookmark-btn, .bookmark-action-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const identifier = btn.dataset.blogId || btn.dataset.slug;
    if (!identifier) return;

    try {
      const r = await fetch(`/blogs/${identifier}/bookmark/`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': getCsrf(),
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({})
      });

      const data = await (r.headers.get('content-type')?.includes('application/json') ? r.json() : Promise.resolve({}));
      if (!r.ok) {
        throw new Error(data.error || 'Please login to bookmark');
      }

      const isBookmarked = data.bookmarked === true;
      btn.classList.toggle('active', isBookmarked);
      btn.classList.toggle('bookmarked', isBookmarked);
      const icon = btn.querySelector('i');
      if (icon) {
        icon.classList.toggle('fas', isBookmarked);
        icon.classList.toggle('far', !isBookmarked);
      }
      const textEl = btn.querySelector('span');
      if (textEl) textEl.textContent = isBookmarked ? 'Saved' : 'Save';
      KVToast.show(isBookmarked ? 'Bookmarked!' : 'Bookmark removed', 'success');
    } catch (error) {
      KVToast.show(error.message || 'Please login to bookmark', 'warning');
    }
  });
});

/* ── Comment Reply Toggle ────────────────────────────────── */
document.querySelectorAll('.comment-reply-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const commentId = btn.dataset.commentId;
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    if (replyForm) {
      replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
      replyForm.querySelector('textarea')?.focus();
    }
  });
});

/* ── Comment Form AJAX ───────────────────────────────────── */
document.querySelectorAll('.comment-ajax-form').forEach(form => {
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const textarea = form.querySelector('textarea[name="content"]');
    
    // Validation: Check if content is empty
    if (!textarea.value.trim()) {
      KVToast.show('Comment cannot be empty', 'warning');
      textarea.focus();
      return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Posting...';
    
    try {
      const formData = new FormData(form);
      const r = await fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': getCsrf(),
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      
      const data = await r.json();
      
      if (r.ok && data.success) {
        form.reset();
        KVToast.show('Comment posted successfully!', 'success');
        
        // Create new comment HTML and prepend it
        const commentHtml = createCommentHtml(data.comment);
        const commentsContainer = document.getElementById('comments-section');
        const noCommentsMsg = commentsContainer?.querySelector('.text-center.py-4');
        if (noCommentsMsg) noCommentsMsg.remove();
        
        // Insert at the beginning of comments list
        const firstComment = commentsContainer?.querySelector('.comment-card');
        if (firstComment) {
          firstComment.insertAdjacentHTML('beforebegin', commentHtml);
        } else {
          // Use the h3 element as reference and insert after it
          const commentsHeader = commentsContainer?.querySelector('h3');
          if (commentsHeader) {
            commentsHeader.insertAdjacentHTML('afterend', commentHtml);
          }
        }
        
        // Update comment count
        updateCommentCount(1);
        
        // Re-attach reply button events
        attachReplyEvents();
      } else if (data.error) {
        KVToast.show(data.error, 'error');
      } else if (data.message) {
        KVToast.show(data.message, 'warning');
      } else {
        KVToast.show('Something went wrong. Please try again.', 'error');
      }
    } catch(err) {
      console.error('Comment submission error:', err);
      KVToast.show('Network error. Please check your connection.', 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-paper-plane"></i> Post Comment';
    }
  });
});

function createCommentHtml(comment) {
  const isReply = comment.is_reply ? 'style="display:none"' : '';
  return `
    <div class="comment-card" data-comment-id="${comment.id}">
      <div class="d-flex align-items-center gap-3 mb-2">
        <img src="${comment.avatar}" class="comment-avatar" alt="">
        <div>
          <div class="comment-author">${comment.author}</div>
          <div class="comment-time">Just now</div>
        </div>
      </div>
      <p class="comment-text">${escapeHtml(comment.content)}</p>
    </div>
  `;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function updateCommentCount(delta) {
  const countSpan = document.querySelector('#comments-section h3 span');
  if (countSpan) {
    const match = countSpan.textContent.match(/\((\d+)\)/);
    if (match) {
      const newCount = parseInt(match[1]) + delta;
      countSpan.textContent = `(${newCount})`;
    }
  }
}

function attachReplyEvents() {
  document.querySelectorAll('.comment-reply-btn').forEach(btn => {
    // Remove existing listeners to avoid duplicates
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);
    newBtn.addEventListener('click', () => {
      const commentId = newBtn.dataset.commentId;
      const replyForm = document.getElementById(`reply-form-${commentId}`);
      if (replyForm) {
        replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
        replyForm.querySelector('textarea')?.focus();
      }
    });
  });
}

/* ── Load More Posts ─────────────────────────────────────── */
(function initLoadMore() {
  const btn = document.querySelector('.load-more-btn');
  if (!btn) return;
  let page = 2;
  btn.addEventListener('click', async () => {
    btn.classList.add('loading');
    const url = btn.dataset.url || window.location.pathname;
    const params = new URLSearchParams(window.location.search);
    params.set('page', page);
    try {
      const r = await fetch(`${url}?${params}&ajax=1`);
      const data = await r.json();
      const grid = document.getElementById('blog-grid');
      if (grid && data.html) {
        grid.insertAdjacentHTML('beforeend', data.html);
        page++;
        // Re-observe new fade-up elements
        document.querySelectorAll('.fade-up:not(.visible)').forEach(el => {
          const io = new IntersectionObserver((entries) => {
            entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); } });
          }, { threshold: 0.1 });
          io.observe(el);
        });
      }
      if (!data.has_next) btn.style.display = 'none';
    } catch(e) { KVToast.show('Error loading posts', 'error'); }
    finally { btn.classList.remove('loading'); }
  });
})();

/* ── Dashboard Sidebar Toggle ────────────────────────────── */
(function initDashboardSidebar() {
  const sidebar  = document.querySelector('.dashboard-sidebar');
  const overlay  = document.querySelector('.sidebar-overlay');
  const openBtn  = document.querySelector('.topbar-menu-btn');
  const closeBtn = document.querySelector('.sidebar-close');
  if (!sidebar) return;

  function openSidebar()  { sidebar.classList.add('open'); overlay?.classList.add('show'); }
  function closeSidebar() { sidebar.classList.remove('open'); overlay?.classList.remove('show'); }

  openBtn?.addEventListener('click', openSidebar);
  closeBtn?.addEventListener('click', closeSidebar);
  overlay?.addEventListener('click', closeSidebar);
})();

/* ── Admin Charts ─────────────────────────────────────────── */
(function initCharts() {
  const chartEl = document.getElementById('adminChart');
  const viewsEl = document.getElementById('viewsChart');
  if (!window.Chart) return;

  const orange = '#FF6B35';
  const pale   = 'rgba(255,107,53,0.1)';
  const defaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { backgroundColor:'#1A1A2E', titleColor:'#fff', bodyColor:'rgba(255,255,255,.8)', padding:10, cornerRadius:8 } },
    scales: {
      x: { grid: { display: false }, ticks: { color:'#8A95A3', font: { size: 11 } } },
      y: { grid: { color:'rgba(0,0,0,.05)' }, ticks: { color:'#8A95A3', font: { size: 11 } }, beginAtZero: true }
    }
  };

  if (chartEl) {
    const labels = JSON.parse(chartEl.dataset.labels || '[]');
    const values = JSON.parse(chartEl.dataset.values || '[]');
    new Chart(chartEl, {
      type: 'bar',
      data: {
        labels,
        datasets: [{ label:'Posts', data: values, backgroundColor: orange, borderRadius: 6, hoverBackgroundColor: '#E5541E' }]
      },
      options: { ...defaults, plugins: { ...defaults.plugins, tooltip: { ...defaults.plugins.tooltip, callbacks: { label: c => ` ${c.raw} posts` } } } }
    });
  }

  if (viewsEl) {
    const labels = JSON.parse(viewsEl.dataset.labels || '[]');
    const values = JSON.parse(viewsEl.dataset.values || '[]');
    new Chart(viewsEl, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label:'Views', data: values,
          borderColor: orange, backgroundColor: pale,
          borderWidth: 2.5, pointRadius: 4, pointBackgroundColor: orange,
          fill: true, tension: 0.4
        }]
      },
      options: defaults
    });
  }
})();

/* ── Password Toggle ─────────────────────────────────────── */
document.querySelectorAll('.password-toggle').forEach(btn => {
  btn.addEventListener('click', () => {
    const input = btn.previousElementSibling || btn.closest('.input-icon-wrap')?.querySelector('input');
    if (!input) return;
    const isText = input.type === 'text';
    input.type = isText ? 'password' : 'text';
    btn.querySelector('i')?.classList.toggle('fa-eye', isText);
    btn.querySelector('i')?.classList.toggle('fa-eye-slash', !isText);
  });
});

/* ── Admin Approve/Reject ────────────────────────────────── */
document.querySelectorAll('[data-action]').forEach(btn => {
  btn.addEventListener('click', async () => {
    const action = btn.dataset.action;
    const id     = btn.dataset.id;
    const type   = btn.dataset.type || 'blog';
    if (!action || !id) return;
    if (action === 'delete' && !confirm('Are you sure you want to delete this?')) return;
    try {
      const r = await fetch(`/dashboard/admin/${type}/${id}/${action}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrf() }
      });
      const data = await r.json();
      if (data.success) {
        KVToast.show(data.message || 'Done!', 'success');
        const row = btn.closest('tr');
        if (row) {
          if (action === 'delete') {
            row.style.transition = 'opacity .3s';
            row.style.opacity = '0';
            setTimeout(() => row.remove(), 300);
          } else {
            const statusEl = row.querySelector('.status-badge');
            if (statusEl) {
              statusEl.className = 'status-badge status-' + (action === 'approve' ? 'published' : 'rejected');
              statusEl.textContent = action === 'approve' ? 'Published' : 'Rejected';
            }
          }
        }
      } else { KVToast.show(data.error || 'Error', 'error'); }
    } catch(e) { KVToast.show('Network error', 'error'); }
  });
});

/* ── Copy URL ────────────────────────────────────────────── */
document.querySelectorAll('[data-copy]').forEach(el => {
  el.addEventListener('click', () => {
    navigator.clipboard?.writeText(el.dataset.copy)
      .then(() => KVToast.show('Copied!', 'success'))
      .catch(() => {});
  });
});

/* ── AOS-like scroll animations ─────────────────────────── */
(function initScrollReveal() {
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const delay = e.target.dataset.delay || 0;
        setTimeout(() => e.target.classList.add('visible'), parseInt(delay));
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('[data-reveal]').forEach(el => {
    el.classList.add('fade-up');
    io.observe(el);
  });
})();

/* ── Helper: get CSRF token ──────────────────────────────── */
function getCsrf() {
  return document.querySelector('meta[name="csrf-token"]')?.content ||
         document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
         document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
}

/* ── Smooth scroll to anchors ────────────────────────────── */
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  });
});

/* ── Mark active nav link ────────────────────────────────── */
(function markActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('#mainNav .nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && path.startsWith(href)) link.classList.add('active');
    else if (href === '/' && path === '/') link.classList.add('active');
  });
})();

/* ── Mobile bottom nav active ────────────────────────────── */
(function markMobileNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.mobile-nav-item').forEach(item => {
    const href = item.getAttribute('href');
    if (href && path.startsWith(href) && href !== '/') item.classList.add('active');
    else if (href === '/' && path === '/') item.classList.add('active');
  });
})();

console.log('%cKV Blog', 'font-size:24px;font-weight:800;color:#FF6B35;font-family:sans-serif');
