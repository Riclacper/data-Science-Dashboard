const topbar = document.querySelector('.topbar');
const topbarContent = document.querySelector('.topbar__content');
const desktopNavigation = document.querySelector('.topbar__nav');
const codeLink = document.querySelector('.topbar__actions .button');
const apiStatus = document.getElementById('apiStatus');

if (topbar && topbarContent && desktopNavigation && codeLink && apiStatus) {
  const menuButton = document.createElement('button');
  menuButton.id = 'mobileMenuButton';
  menuButton.className = 'mobile-menu-button';
  menuButton.type = 'button';
  menuButton.setAttribute('aria-expanded', 'false');
  menuButton.setAttribute('aria-controls', 'mobileNavigation');
  menuButton.setAttribute('aria-label', 'Abrir menu de navegação');
  menuButton.innerHTML = '<span></span><span></span><span></span>';

  const mobileNavigation = document.createElement('div');
  mobileNavigation.id = 'mobileNavigation';
  mobileNavigation.className = 'mobile-navigation';
  mobileNavigation.hidden = true;

  const mobileLinks = document.createElement('nav');
  mobileLinks.className = 'mobile-navigation__links';
  mobileLinks.setAttribute('aria-label', 'Navegação mobile');

  const desktopLinks = [...desktopNavigation.querySelectorAll('a')];
  const clonedLinks = desktopLinks.map((link) => {
    const clone = link.cloneNode(true);
    mobileLinks.appendChild(clone);
    return clone;
  });

  const mobileStatus = apiStatus.cloneNode(true);
  mobileStatus.removeAttribute('id');
  mobileStatus.removeAttribute('aria-live');
  mobileStatus.classList.add('mobile-navigation__status');

  const mobileCodeLink = codeLink.cloneNode(true);
  mobileCodeLink.classList.add('mobile-navigation__code');

  mobileNavigation.append(mobileLinks, mobileStatus, mobileCodeLink);
  topbarContent.appendChild(menuButton);
  topbar.appendChild(mobileNavigation);

  function syncActiveLink() {
    desktopLinks.forEach((link, index) => {
      if (link.getAttribute('aria-current') === 'page') {
        clonedLinks[index].setAttribute('aria-current', 'page');
      } else {
        clonedLinks[index].removeAttribute('aria-current');
      }
    });
  }

  function syncStatus() {
    mobileStatus.className = `${apiStatus.className} mobile-navigation__status`;
    mobileStatus.innerHTML = apiStatus.innerHTML;
  }

  function setMenuOpen(open, returnFocus = false) {
    menuButton.setAttribute('aria-expanded', String(open));
    menuButton.setAttribute('aria-label', open ? 'Fechar menu de navegação' : 'Abrir menu de navegação');
    mobileNavigation.hidden = !open;
    document.body.classList.toggle('mobile-menu-open', open);
    if (!open && returnFocus) menuButton.focus();
  }

  menuButton.addEventListener('click', () => {
    setMenuOpen(menuButton.getAttribute('aria-expanded') !== 'true');
  });

  mobileNavigation.addEventListener('click', (event) => {
    if (event.target.closest('a')) setMenuOpen(false);
  });

  document.addEventListener('click', (event) => {
    if (menuButton.getAttribute('aria-expanded') === 'true' && !topbar.contains(event.target)) {
      setMenuOpen(false);
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') {
      setMenuOpen(false, true);
    }
  });

  const mobileBreakpoint = window.matchMedia('(max-width: 1100px)');
  mobileBreakpoint.addEventListener('change', (event) => {
    if (!event.matches) setMenuOpen(false);
  });

  const activeLinkObserver = new MutationObserver(syncActiveLink);
  desktopLinks.forEach((link) => activeLinkObserver.observe(link, {
    attributes: true,
    attributeFilter: ['aria-current'],
  }));

  const statusObserver = new MutationObserver(syncStatus);
  statusObserver.observe(apiStatus, {
    attributes: true,
    childList: true,
    subtree: true,
    characterData: true,
  });

  syncActiveLink();
  syncStatus();
}
