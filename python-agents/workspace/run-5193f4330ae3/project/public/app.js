/* Star field implementation */
const canvas = document.getElementById('starCanvas');
const ctx = canvas.getContext('2d');
let width, height;

function resize() {
  width = canvas.width = window.innerWidth;
  height = canvas.height = window.innerHeight;
}
window.addEventListener('resize', resize);
resize();

const stars = [];
const STAR_COUNT = 200;
for (let i = 0; i < STAR_COUNT; i++) {
  stars.push({
    x: Math.random() * width,
    y: Math.random() * height,
    radius: Math.random() * 1.5 + 0.5,
    alpha: Math.random() * 0.5 + 0.5,
    alphaChange: Math.random() * 0.02 + 0.01
  });
}

function drawStars() {
  ctx.clearRect(0, 0, width, height);
  stars.forEach(star => {
    star.alpha += star.alphaChange;
    if (star.alpha >= 1 || star.alpha <= 0.2) star.alphaChange *= -1;
    ctx.globalAlpha = star.alpha;
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.globalAlpha = 1;
}

/* Animation on button click */
const btn = document.getElementById('clickBtn');
const animations = [];

btn.addEventListener('click', () => {
  const rect = btn.getBoundingClientRect();
  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;
  animations.push({
    x: centerX,
    y: centerY,
    radius: 0,
    maxRadius: 80,
    alpha: 1
  });
});

function drawAnimations() {
  animations.forEach((anim, index) => {
    anim.radius += 4;
    anim.alpha -= 0.02;
    if (anim.alpha <= 0) {
      animations.splice(index, 1);
      return;
    }
    ctx.save();
    ctx.globalAlpha = anim.alpha;
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(anim.x, anim.y, anim.radius, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  });
}

function animate() {
  drawStars();
  drawAnimations();
  requestAnimationFrame(animate);
}
animate();