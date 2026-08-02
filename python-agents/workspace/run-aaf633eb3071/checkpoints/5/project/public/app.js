// Create twinkling stars
const starsContainer = document.getElementById('stars');
const starCount = 200;
for (let i = 0; i < starCount; i++) {
  const star = document.createElement('div');
  star.className = 'star';
  const size = Math.random() * 2 + 1; // 1-3px
  star.style.width = size + 'px';
  star.style.height = size + 'px';
  star.style.top = Math.random() * 100 + '%';
  star.style.left = Math.random() * 100 + '%';
  star.style.animationDelay = Math.random() * 2 + 's';
  starsContainer.appendChild(star);
}

// Burst animation on button click
const button = document.getElementById('burstBtn');
button.addEventListener('click', () => {
  const burst = document.createElement('div');
  burst.className = 'burst';
  const rect = button.getBoundingClientRect();
  burst.style.top = (rect.top + rect.height / 2) + 'px';
  burst.style.left = (rect.left + rect.width / 2) + 'px';
  document.body.appendChild(burst);
  burst.addEventListener('animationend', () => {
    burst.remove();
  });
});