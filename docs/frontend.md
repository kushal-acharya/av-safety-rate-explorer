# Frontend guide

The deployed frontend is semantic HTML, dedicated CSS and modular JavaScript.
`web-src/` contains the maintainable JavaScript sources; esbuild bundles them into
`web/waymo-project/app.js`. That generated file should not be edited by hand.
The statistics are validated against the Python reference, and study data is exported
from the reproducible Python pipelines.

The standalone `web/waymo-project/brief.html` is the portfolio entry point. It uses
`brief.css`, system fonts and no JavaScript. Its links open the existing analysis views.
The brief is an editorial summary of the frozen studies; update its illustrative numbers
only alongside verified source changes, never from a newer unrelated dashboard release.

Stylesheets have distinct scopes:

- `style.css`: dashboard shell, controls, DMV views and shared design tokens.
- `replication.css`: publication note and shared research-note components.
- `geography.css`: exposure matching controls, charts and audit layout.
- `brief.css`: standalone project brief, responsive layout and print styles.

All stylesheets are readable source files, formatted with the pinned Prettier version.
CI rejects formatting drift. Keep the existing token palette and use semantic HTML,
visible keyboard focus, reduced-motion support and scrollable wide data tables.

```bash
npm ci
npm run format:css
npm run check:css
npm test
npm run build
npx wrangler dev --port 8789
# In another terminal:
npm run test:browser
node scripts/test_accessibility.js
```

The browser suite checks rendering without JavaScript, tests layout and accessibility
at 320, 390, 768 and 1440 pixels, and follows all three research entry points. The six
analysis views have interaction, mobile and accessibility checks of their own.
TypeScript is not currently required; avoid a framework migration merely to change
file extensions. If types are introduced, start at numerical interfaces and retain the
Python/JavaScript parity checks.
