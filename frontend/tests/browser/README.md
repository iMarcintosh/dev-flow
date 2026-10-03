# Browser regression tests

From `frontend`, run `npm ci`, then `npx playwright install chromium` and `npm run test:browser`.

If Chromium is already installed, set `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` to its executable instead of downloading a browser. For this cloud environment:

```bash
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium npm run test:browser
```

Playwright starts the Vite development server or reuses one already running locally. The authentication responses are mocked, so no backend, account, or provider API key is required. The tests exercise the actual application API client and login form in Chromium.

Covered authentication behavior: rejected login retains the form and error without refreshing, protected requests still refresh and retry, and explicit refresh failures do not trigger another refresh.

Chat tests use saved-message fixtures and a controlled incremental `ReadableStream` in the browser. They exercise UTF-8 chunks, streaming completion, saved answers after reload, conversation switching, stopping/restarting, truncated streams, provider errors, and selection after reload. They do not validate a real provider, network-level SSE delivery, or backend persistence.

Failure screenshots and traces are written under `test-results`; an HTML report is written under `playwright-report`. These files are ignored by Git. The GitHub Actions workflow runs the strict production build and browser suite on pull requests and pushes to main, and retains the report and failure evidence as downloadable artifacts for seven days. No provider secrets are needed.
