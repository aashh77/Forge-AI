# Agent Execution Plan

## Summary
Re‑planned to add missing static assets, remove server code, provide deployment documentation, audit security, and run tests to satisfy reviewer findings.

## Schedule

### patch-1 — frontend (patch)
- **Reason:** Reviewer requested missing elements in index.html.
- **Context:** Ensure static index.html contains coffee‑themed UI, links, search input, and catalogue container.
- **Instructions:** Modify public/index.html:
1. Add a CSP meta tag in the <head>:
   <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;">
2. Ensure the page links to the CSS and JS:
   <link rel="stylesheet" href="styles.css">
   <script src="app.js" defer></script>
3. Add a search input and catalogue container inside the <body>:
   <input type="text" id="search" placeholder="Search coffee…" aria-label="Search coffee items">
   <div id="catalogue" role="list"></div>
- **Depends on:** none

### patch-2 — frontend (patch)
- **Reason:** Patch to satisfy reviewer’s security and functionality requirements.
- **Context:** Implement client‑side search and secure rendering.
- **Instructions:** Update public/app.js:
1. Add a helper to escape HTML:
   function escapeHtml(str){
     const div=document.createElement('div');
     div.textContent=str;
     return div.innerHTML;
   }
2. Fetch catalogue.json and render items into #catalogue using createElement and textContent.
3. Add event listener on #search to filter items client‑side.
4. Ensure all text inserted via textContent or escapeHtml to prevent XSS.
- **Depends on:** patch-1

### patch-3 — backend (patch)
- **Reason:** Reviewer requested removal of server dependencies for a static site.
- **Context:** Eliminate unnecessary Express server dependencies.
- **Instructions:** Modify package.json:
1. Remove any dependencies related to Express, cors, or other server modules.
2. Remove scripts that reference a server (e.g., "start": "node server.js").
3. Keep only build or dev scripts needed for static hosting (e.g., "build": "echo 'Static site'").
- **Depends on:** none

### patch-4 — backend (patch)
- **Reason:** Reviewer explicitly asked to delete server.js.
- **Context:** No server code should exist for a static deployment.
- **Instructions:** Delete server.js from the project root.
- **Depends on:** patch-3

### patch-5 — frontend (patch)
- **Reason:** Reviewer requested a README with deployment guidance.
- **Context:** Provide deployment instructions for static hosting.
- **Instructions:** Create README.md with content:
# Coffee Café Static Site

This is a simple coffee‑themed static website that displays a small catalogue of coffee items.

## Deployment

You can deploy this site to any static host such as Netlify or GitHub Pages.

### Netlify
1. Connect your repo to Netlify.
2. Set the build command to `echo "Static site"` and publish directory to `public`.
3. Deploy.

### GitHub Pages
1. Push the `public` folder to the `gh-pages` branch.
2. Enable GitHub Pages in the repository settings pointing to the `gh-pages` branch.

## Local Development

```bash
# No build step required – just open public/index.html in a browser
```
- **Depends on:** patch-1, patch-2

### audit-1 — security (audit)
- **Reason:** Security audit must precede testing and deployment.
- **Context:** Ensure the static site adheres to security best practices.
- **Instructions:** Run a security audit on the updated static assets. Verify CSP meta tag, no inline scripts, proper escaping, and HTTPS usage for external resources.
- **Depends on:** patch-5

### test-1 — qa (test)
- **Reason:** Testing confirms that patches meet requirements and the site is stable.
- **Context:** Validate functionality and security after patches.
- **Instructions:** Run smoke tests:
1. Open public/index.html in a headless browser.
2. Verify the catalogue loads and search filters items.
3. Ensure no console errors and CSP is enforced.
4. Run fuzz tests on app.js to confirm no XSS vulnerabilities.
- **Depends on:** audit-1

