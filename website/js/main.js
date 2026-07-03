(function () {
  document.querySelector('.menu-btn')?.addEventListener('click', () => {
    document.querySelector('.nav')?.classList.toggle('open');
  });

  document.querySelectorAll('.nav a').forEach((link) => {
    link.addEventListener('click', () => {
      document.querySelector('.nav')?.classList.remove('open');
    });
  });

  function copyText(text, button) {
    navigator.clipboard.writeText(text).then(() => {
      const original = button.textContent;
      button.textContent = 'Copied';
      setTimeout(() => { button.textContent = original; }, 2000);
    });
  }

  document.querySelectorAll('[data-copy]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const el = document.querySelector(btn.dataset.copy);
      if (el) copyText(el.textContent.trim(), btn);
    });
  });

  document.querySelectorAll('.code-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      const win = tab.closest('.code-window');
      const id = tab.dataset.tab;
      win.querySelectorAll('.code-tab').forEach((t) => t.classList.remove('active'));
      win.querySelectorAll('.code-panel').forEach((p) => p.classList.remove('active'));
      tab.classList.add('active');
      win.querySelector(`#${id}`)?.classList.add('active');
    });
  });

  const reveals = document.querySelectorAll('.reveal');
  if (reveals.length && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
    );
    reveals.forEach((el) => observer.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add('visible'));
  }

  const heroWord = document.querySelector('.hero-repeat');
  if (heroWord && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const words = ['remember.', 'search.', 'build.'];
    let i = 0;
    setInterval(() => {
      i = (i + 1) % words.length;
      heroWord.style.opacity = '0';
      setTimeout(() => {
        heroWord.textContent = words[i];
        heroWord.style.opacity = '1';
      }, 200);
    }, 3000);
  }

  /* ── Grok-style chat ── */
  const chatInput = document.getElementById('grok-input');
  const chatResponse = document.getElementById('grok-response');
  const chatSubmit = document.getElementById('grok-submit');
  const chatSuggestions = document.querySelectorAll('.grok-suggestion');

  const demoResponses = {
    'How do I fix ModuleNotFoundError?':
      'Check which Python environment you are using. Activate your virtualenv and run pip list to verify the package is installed.',
    'Search my past conversations about Python':
      'Found 3 similar messages (sim=0.51). Top match: "Check which Python environment you are using." from session Debugging Python.',
    'Store that my favorite language is Python':
      'Memory saved: key=fav_language, value=Python for user alice. Stored in memories.json — cat it anytime.',
    default:
      'neuDB would embed your query, search_similar across messages, and return the top matches by cosine similarity.',
  };

  function runChatQuery(query) {
    if (!query.trim() || !chatResponse) return;
    chatInput.value = query;
    chatResponse.hidden = false;
    chatResponse.classList.remove('visible');
    chatResponse.innerHTML = '<span class="grok-thinking">Searching memory…</span>';

    setTimeout(() => {
      const answer = demoResponses[query] || demoResponses.default;
      chatResponse.innerHTML = `<p class="grok-answer">${answer}</p>`;
      chatResponse.classList.add('visible');

      const memoryCard = document.getElementById('card-memory');
      if (memoryCard) {
        const prompt = memoryCard.querySelector('.mock-prompt strong');
        const response = memoryCard.querySelector('.mock-response');
        if (prompt) prompt.textContent = query;
        if (response) response.textContent = answer;
      }
    }, 600);
  }

  chatSubmit?.addEventListener('click', () => runChatQuery(chatInput?.value || ''));
  chatInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      runChatQuery(chatInput.value);
    }
  });

  chatSuggestions.forEach((chip) => {
    chip.addEventListener('click', () => runChatQuery(chip.dataset.query || chip.textContent));
  });

  /* ── Sticky product nav ── */
  const productNav = document.getElementById('product-nav');
  const productLinks = document.querySelectorAll('.product-nav-link');
  const productCards = document.querySelectorAll('[data-product-card]');
  const showcase = document.getElementById('showcase');

  productLinks.forEach((link) => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(link.getAttribute('href'));
      if (target) {
        const top = target.getBoundingClientRect().top + window.scrollY - 140;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });

  if (showcase && productNav) {
    const navObserver = new IntersectionObserver(
      ([entry]) => {
        productNav.classList.toggle('is-visible', entry.isIntersecting || entry.boundingClientRect.top < 200);
      },
      { threshold: 0, rootMargin: '-80px 0px 0px 0px' }
    );
    navObserver.observe(showcase);

    const cardObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const id = entry.target.id;
            productLinks.forEach((link) => {
              link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
            });
            productCards.forEach((card) => {
              card.classList.toggle('is-highlighted', card.id === id);
            });
          }
        });
      },
      { threshold: 0.4, rootMargin: '-140px 0px -40% 0px' }
    );
    productCards.forEach((card) => cardObserver.observe(card));
  }
})();