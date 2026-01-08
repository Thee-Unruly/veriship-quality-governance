Playwright E2E tests

Setup (run in repository root):

1. Install dev dependency:

```bash
npm install --save-dev @playwright/test
npx playwright install --with-deps
```

2. Run tests (adjust `BASE_URL` to your running frontend):

```bash
# example: frontend on localhost:3000 or frontend static server
BASE_URL=http://localhost:3000 npm run test:e2e
```

Notes:
- The sample test navigates to the app and looks for a Copilot link. Adjust selectors in `load-tests/e2e.spec.ts` to match your app.
- For CI or Docker, install browsers with `npx playwright install --with-deps` inside the pipeline image.
- To debug in headed mode: `BASE_URL=http://localhost:3000 npx playwright test --headed`
