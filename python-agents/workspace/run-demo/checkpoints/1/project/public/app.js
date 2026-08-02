document.addEventListener("DOMContentLoaded", () => {
  const starsContainer = document.querySelector(".stars");
  if (!starsContainer) return;

  // Add a handful of extra stars dynamically for browsers that run JS.
  const extraCount = 24;
  for (let i = 0; i < extraCount; i++) {
    const star = document.createElement("div");
    star.style.position = "absolute";
    star.style.left = `${Math.random() * 100}%`;
    star.style.top = `${Math.random() * 100}%`;
    star.style.width = "2px";
    star.style.height = "2px";
    star.style.background = "rgba(255, 255, 255, 0.9)";
    star.style.borderRadius = "50%";
    star.style.opacity = `${0.3 + Math.random() * 0.7}`;
    star.style.animation = `twinkle ${1.5 + Math.random() * 2.5}s ease-in-out infinite alternate`;
    star.style.animationDelay = `${Math.random() * 3}s`;
    starsContainer.appendChild(star);
  }
});
