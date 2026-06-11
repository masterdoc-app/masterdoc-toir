(function () {
  const params = new URLSearchParams(window.location.search);
  ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach((key) => {
    const el = document.getElementById(key);
    const val = params.get(key);
    if (el && val) el.value = val;
  });

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
          ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach((key) => {
            const el = document.getElementById(key);
            const val = params.get(key);
            if (el && val) el.value = val;
          });
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
