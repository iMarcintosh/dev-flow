# Browser regression tests

From `frontend`, run `npm ci`, then `npx playwright install chromium` and `npm run test:browser`.

If Chromium is already installed, set `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` to its executable instead of downloading a browser. For this cloud environment:

```bash
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium npm run test:browser
```

Playwright starts the Vite development server or reuses one already running locally. The authentication responses are mocked, so no backend, account, or provider API key is required. The tests exercise the actual application API client and login form in Chromium.

Covered behavior: rejected login retains the form and error without refreshing, protected requests still refresh and retry, and explicit refresh failures do not trigger another refresh. Failure screenshots are written under `test-results`.
