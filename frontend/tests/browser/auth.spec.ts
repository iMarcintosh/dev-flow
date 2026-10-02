import { expect, test } from '@playwright/test'

test('rejected login preserves the error and form without refreshing the session', async ({ page }) => {
  let refreshRequests = 0
  await page.route('**/api/auth/refresh', async (route) => {
    refreshRequests++
    await route.fulfill({ status: 401, json: { detail: 'No refresh token' } })
  })
  await page.route('**/api/auth/login', async (route) => {
    await route.fulfill({ status: 401, json: { detail: 'Invalid credentials' } })
  })
  await page.goto('/login')
  await page.getByLabel('Email', { exact: true }).fill('login-test@example.com')
  await page.getByLabel('Password', { exact: true }).fill('invalid-test-password')
  await page.getByRole('button', { name: 'Sign In', exact: true }).click()
  await expect(page.getByText('Invalid credentials', { exact: true })).toBeVisible()
  await expect(page.getByLabel('Email', { exact: true })).toHaveValue('login-test@example.com')
  await expect(page.getByLabel('Password', { exact: true })).toHaveValue('invalid-test-password')
  await expect(page.getByRole('button', { name: 'Sign In', exact: true })).toBeEnabled()
  expect(refreshRequests).toBe(0)
})

test('a protected request still refreshes an expired session and retries', async ({ page }) => {
  let protectedRequests = 0
  let refreshRequests = 0
  await page.route('**/api/auth/refresh', async (route) => {
    refreshRequests++
    await route.fulfill({ json: { access_token: 'refreshed-test-token' } })
  })
  await page.route('**/api/projects/', async (route) => {
    protectedRequests++
    if (route.request().headers().authorization !== 'Bearer refreshed-test-token') {
      await route.fulfill({ status: 401, json: { detail: 'Expired token' } })
    } else {
      await route.fulfill({ json: [] })
    }
  })
  await page.goto('/login')
  const result = await page.evaluate(async () => {
    localStorage.setItem('access_token', 'expired-test-token')
    // Import the same API client that the application uses, via Vite.
    // @ts-expect-error Vite serves this source module in the browser.
    const { api } = await import('/src/services/api.ts')
    const response = await api.get('/api/projects/')
    return { status: response.status, data: response.data }
  })
  expect(result).toEqual({ status: 200, data: [] })
  expect(refreshRequests).toBe(1)
  expect(protectedRequests).toBe(2)
})

test('a rejected explicit refresh does not recursively refresh', async ({ page }) => {
  let refreshRequests = 0
  await page.route('**/api/auth/refresh', async (route) => {
    refreshRequests++
    await route.fulfill({ status: 401, json: { detail: 'No refresh token' } })
  })
  await page.goto('/login')
  const status = await page.evaluate(async () => {
    // @ts-expect-error Vite serves this source module in the browser.
    const { api } = await import('/src/services/api.ts')
    try {
      await api.post('/api/auth/refresh')
      return 200
    } catch (error: any) {
      return error.response.status
    }
  })
  expect(status).toBe(401)
  expect(refreshRequests).toBe(1)
})
