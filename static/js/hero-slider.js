document.addEventListener('DOMContentLoaded', function() {
  const heroSection = document.getElementById('heroSection');
  const bgLayer1 = document.getElementById('bgLayer1');
  const bgLayer2 = document.getElementById('bgLayer2');

  // Pobierz i sparsuj tablicę obrazów z data-attributes
  const backgroundImages = JSON.parse(heroSection.getAttribute('data-images'));

  let currentIndex = 0;
  let visibleLayer = 1;

  bgLayer1.style.backgroundImage = `url("${backgroundImages[0]}")`;
  bgLayer1.classList.add('visible');

  function changeBackground() {
    const nextIndex = (currentIndex + 1) % backgroundImages.length;

    if (visibleLayer === 1) {
      bgLayer2.style.backgroundImage = `url("${backgroundImages[nextIndex]}")`;
      bgLayer2.classList.add('visible');
      bgLayer1.classList.remove('visible');
      visibleLayer = 2;
    } else {
      bgLayer1.style.backgroundImage = `url("${backgroundImages[nextIndex]}")`;
      bgLayer1.classList.add('visible');
      bgLayer2.classList.remove('visible');
      visibleLayer = 1;
    }

    currentIndex = nextIndex;
  }

  setInterval(changeBackground, 4000);
});
