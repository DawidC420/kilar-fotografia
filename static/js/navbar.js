// Zmiana klasy header po scrollu i zmiana logo
window.addEventListener('scroll', () => {
  const header = document.getElementById('mainHeader');
  const logo = document.getElementById('logoImg');
  const logoNormal = logo.getAttribute('data-logo');
  const logoInverted = logo.getAttribute('data-logo-inverted');

  if (window.scrollY > 80) {
    header.classList.add('scrolled');
    logo.src = logoInverted;
  } else {
    header.classList.remove('scrolled');
    logo.src = logoNormal;
  }
});

// Hamburger menu toggle
document.getElementById('hamburgerBtn').onclick = function() {
  document.querySelector('.nav-links').classList.toggle('active');
};

// Zamknięcie menu po kliknięciu w link
document.querySelectorAll('.nav-links a').forEach(link => {
  link.onclick = () => document.querySelector('.nav-links').classList.remove('active');
});
