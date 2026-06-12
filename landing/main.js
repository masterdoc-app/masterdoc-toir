(function () {
  const header = document.querySelector('.site-header');
  if (header && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    let lastY = window.scrollY;
    let ticking = false;
    const threshold = 72;

    function updateHeader() {
      const y = window.scrollY;
      if (y <= threshold) {
        header.classList.remove('is-hidden');
      } else if (y > lastY + 8) {
        header.classList.add('is-hidden');
      } else if (y < lastY - 8) {
        header.classList.remove('is-hidden');
      }
      lastY = y;
      ticking = false;
    }

    window.addEventListener(
      'scroll',
      () => {
        if (!ticking) {
          requestAnimationFrame(updateHeader);
          ticking = true;
        }
      },
      { passive: true }
    );
  }

  const variants = window.AB_VARIANTS || {};
  const params = new URLSearchParams(window.location.search);

  const abState = {
    layout: 'full',
    h1: '',
    eyebrow: '',
    bullets: '',
    copy: '',
    hero: '',
  };

  function resolveLayout(raw) {
    if (raw === 'lean') return 'lean';
    return 'full';
  }

  function applyH1(key) {
    const el = document.getElementById('hero-h1');
    if (!el || !key || !variants.h1?.[key]) return;
    el.textContent = variants.h1[key];
    abState.h1 = key;
  }

  function applyEyebrow(key) {
    const el = document.getElementById('hero-eyebrow');
    if (!el || !key) return;

    if (key === 'none') {
      el.hidden = true;
      abState.eyebrow = key;
      return;
    }

    if (variants.eyebrow?.[key]) {
      el.textContent = variants.eyebrow[key];
      el.hidden = false;
      abState.eyebrow = key;
    }
  }

  function applyBullets(key) {
    const el = document.getElementById('hero-bullets');
    const items = variants.bullets?.[key];
    if (!el || !items?.length) return;

    el.replaceChildren();
    items.forEach((text) => {
      const li = document.createElement('li');
      li.textContent = text;
      el.appendChild(li);
    });
    el.hidden = false;
    abState.bullets = key;
  }

  function applyCopy(key) {
    const el = document.getElementById('hero-desc');
    if (!el || !key || !variants.copy?.[key]) return;
    el.textContent = variants.copy[key];
    abState.copy = key;
  }

  function applyHero(key) {
    const heroVariant = variants.hero?.[key];
    const heroScene = document.querySelector('.hero-scene');
    const heroPhoto = document.querySelector('.hero-scene__photo');
    if (!heroPhoto || !heroVariant) return;

    heroPhoto.src = heroVariant.src;
    heroPhoto.alt = heroVariant.alt;
    if (heroScene) {
      heroScene.classList.toggle('hero-scene--no-ui', Boolean(heroVariant.hideUi));
    }
    abState.hero = key;
  }

  function renderTrustStrip() {
    const strip = document.getElementById('trust-strip');
    const list = document.getElementById('trust-strip-list');
    if (!strip || !list || !variants.trust?.length) return;

    list.replaceChildren();
    variants.trust.forEach((text) => {
      const li = document.createElement('li');
      li.textContent = text;
      list.appendChild(li);
    });
  }

  function applyLayout(layout) {
    abState.layout = layout;
    document.body.classList.toggle('layout-lean', layout === 'lean');

    document.querySelectorAll('[data-ab-hide-layout="lean"]').forEach((section) => {
      section.hidden = layout === 'lean';
    });

    document.querySelectorAll('[data-ab-show-layout="lean"]').forEach((section) => {
      section.hidden = layout !== 'lean';
    });
  }

  function fillHiddenFields() {
    const utmKeys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'];
    utmKeys.forEach((key) => {
      const el = document.getElementById(key);
      const val = params.get(key);
      if (el) el.value = val || '';
    });

    const abFields = {
      ab_layout: abState.layout,
      ab_h1: abState.h1,
      ab_eyebrow: abState.eyebrow,
      ab_bullets: abState.bullets,
      ab_copy: abState.copy,
      ab_hero: abState.hero,
    };

    Object.entries(abFields).forEach(([id, value]) => {
      const el = document.getElementById(id);
      if (el) el.value = value || '';
    });
  }

  function restoreHiddenFieldsAfterReset() {
    fillHiddenFields();
  }

  function initAb() {
    renderTrustStrip();

    const layout = resolveLayout(params.get('layout'));
    applyLayout(layout);

    const h1Key = params.get('h1');
    if (h1Key && h1Key !== 'default') applyH1(h1Key);

    const eyebrowKey = params.get('eyebrow');
    if (eyebrowKey && eyebrowKey !== 'default') applyEyebrow(eyebrowKey);

    const bulletsKey = params.get('bullets');
    if (bulletsKey) applyBullets(bulletsKey);

    const copyKey = params.get('copy');
    if (copyKey) applyCopy(copyKey);

    const heroKey = params.get('hero');
    if (heroKey) applyHero(heroKey);

    fillHiddenFields();
  }

  initAb();

  const tabButtons = document.querySelectorAll('[data-platform-tab]');
  const tabPanels = document.querySelectorAll('[data-platform-panel]');

  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.platformTab;
      tabButtons.forEach((b) => b.classList.toggle('active', b === btn));
      tabPanels.forEach((p) => p.classList.toggle('active', p.dataset.platformPanel === id));
    });
  });

  document.querySelectorAll('.faq-q').forEach((btn) => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.faq-item');
      const isOpen = item.classList.contains('open');
      document.querySelectorAll('.faq-item.open').forEach((el) => {
        el.classList.remove('open');
        el.querySelector('.faq-q').setAttribute('aria-expanded', 'false');
      });
      if (!isOpen) {
        item.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });

  const demoForm = document.getElementById('demo-form');
  const demoFormStatus = document.getElementById('demo-form-status');

  if (demoForm) {
    demoForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = demoForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      demoFormStatus.hidden = true;
      demoFormStatus.className = 'demo-form__status';

      try {
        const res = await fetch(demoForm.action, {
          method: 'POST',
          body: new FormData(demoForm),
          headers: { Accept: 'application/json' },
        });

        if (res.ok) {
          if (typeof ym === 'function') ym(109561586, 'reachGoal', 'demo_form_submit');
          demoForm.reset();
          restoreHiddenFieldsAfterReset();
          demoFormStatus.textContent = 'Спасибо! Заявка отправлена — свяжемся с вами в ближайшее время.';
          demoFormStatus.classList.add('demo-form__status--ok');
        } else {
          throw new Error('submit failed');
        }
      } catch {
        demoFormStatus.textContent = 'Не удалось отправить заявку. Попробуйте ещё раз или напишите нам напрямую.';
        demoFormStatus.classList.add('demo-form__status--err');
      }

      demoFormStatus.hidden = false;
      submitBtn.disabled = false;
    });
  }

  document.querySelectorAll('.demo-link').forEach((link) => {
    link.addEventListener('click', () => {
      const nameInput = demoForm?.querySelector('[name="name"]');
      if (nameInput && !nameInput.matches(':focus')) {
        setTimeout(() => nameInput.focus(), 400);
      }
    });
  });

  const copilotFloor = document.querySelector('.copilot-floor');
  if (copilotFloor) {
    const buttons = copilotFloor.querySelectorAll('.nav-btn');
    const screens = copilotFloor.querySelectorAll('.scr');
    const stage = copilotFloor.querySelector('#copilotPhoneStage');
    if (buttons.length && screens.length) {
      const total = buttons.length;
      let idx = Array.from(buttons).findIndex((b) => b.classList.contains('active'));
      if (idx < 0) idx = 0;
      let autoTimer = null;
      let userPaused = false;
      let inView = false;

      function show(target) {
        buttons.forEach((b) => b.classList.toggle('active', b.dataset.target === String(target)));
        screens.forEach((s) => s.classList.toggle('active', s.dataset.screen === String(target)));
      }
      function tick() {
        idx = (idx + 1) % total;
        show(buttons[idx].dataset.target);
      }
      function startAuto() {
        if (autoTimer || userPaused || !inView) return;
        autoTimer = setInterval(tick, 3200);
      }
      function stopAuto() {
        if (autoTimer) {
          clearInterval(autoTimer);
          autoTimer = null;
        }
      }
      function pauseFromUser() {
        userPaused = true;
        stopAuto();
      }

      buttons.forEach((btn, i) => {
        btn.addEventListener('click', () => {
          idx = i;
          show(btn.dataset.target);
          pauseFromUser();
        });
      });

      if (stage) {
        stage.addEventListener('mouseenter', stopAuto);
        stage.addEventListener('mouseleave', startAuto);
      }

      const phoneIO = new IntersectionObserver((ents) => {
        ents.forEach((en) => {
          inView = en.isIntersecting;
          if (inView) startAuto();
          else stopAuto();
        });
      }, { threshold: 0.25 });
      if (stage) phoneIO.observe(stage);

      if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        userPaused = true;
      }
    }
  }
})();
