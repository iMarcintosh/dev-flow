import { expect, test, type Page } from '@playwright/test'

const agentId = 'browser-test-agent'
const firstId = 'conversation-a'
const secondId = 'conversation-b'
const inputPlaceholder = 'Type your message... (Enter to send, Shift+Enter for new line)'

function message(conversationId: string, content: string, role = 'assistant') {
  return { id: `${conversationId}-${content}`, conversation_id: conversationId, role, content, message_metadata: {}, created_at: '2026-01-01T12:00:00Z' }
}

async function setupChat(page: Page) {
  const saved = {
    [firstId]: [message(firstId, 'Saved first conversation')],
    [secondId]: [message(secondId, 'Saved second conversation')],
  }
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'browser-test-token')
    localStorage.setItem('auth-storage', JSON.stringify({ state: {
      user: { id: 'browser-test-user', email: 'browser@example.com', full_name: 'Browser Test' },
      token: 'browser-test-token', isAuthenticated: true,
    }, version: 0 }))

    // Controlled streaming transport: exercise the application's real fetch
    // reader with incremental bytes, without paid provider calls or secrets.
    const streams: Record<string, { controller: ReadableStreamDefaultController<Uint8Array>; aborted: boolean }> = {}
    ;(window as any).__chatStreams = streams
    const nativeFetch = window.fetch.bind(window)
    window.fetch = async (input, init) => {
      const url = new URL(input instanceof Request ? input.url : String(input), location.href)
      const match = url.pathname.match(/\/conversations\/([^/]+)\/messages\/stream$/)
      if (!match) return nativeFetch(input, init)
      const id = match[1]
      const stream = new ReadableStream<Uint8Array>({
        start(controller) {
          streams[id] = { controller, aborted: false }
          init?.signal?.addEventListener('abort', () => {
            streams[id].aborted = true
            controller.error(new DOMException('Aborted', 'AbortError'))
          }, { once: true })
        },
      })
      return new Response(stream, { headers: { 'Content-Type': 'text/event-stream' } })
    }
  })
  await page.route('**/api/**', async (route) => {
    const path = new URL(route.request().url()).pathname
    if (path === '/api/projects/') {
      await route.fulfill({ json: [] })
    } else if (path === `/api/custom-agents/${agentId}`) {
      await route.fulfill({ json: { id: agentId, name: 'Browser Test Agent', description: 'Controlled browser regression fixture', icon: '🤖' } })
    } else if (path === '/api/agent-chat/conversations') {
      await route.fulfill({ json: [firstId, secondId].map((id, index) => ({
        id, agent_id: agentId, title: index === 0 ? 'First conversation' : 'Second conversation',
        message_count: saved[id].length, created_at: '2026-01-01T12:00:00Z', updated_at: '2026-01-01T12:00:00Z',
      })) })
    } else if (path.endsWith('/messages')) {
      const id = path.split('/')[4]
      await route.fulfill({ json: saved[id] ?? [] })
    } else {
      await route.fulfill({ status: 404, json: { detail: 'Unexpected test endpoint' } })
    }
  })
  await page.goto(`/chat?agent_id=${agentId}&conversation_id=${firstId}`)
  await expect(page.getByText('Saved first conversation', { exact: true })).toBeVisible()
  return saved
}

async function send(page: Page, text: string) {
  await page.getByPlaceholder(inputPlaceholder).fill(text)
  await page.getByPlaceholder(inputPlaceholder).press('Enter')
  await expect.poll(() => page.evaluate(() => Boolean((window as any).__chatStreams['conversation-a']))).toBe(true)
}

async function bytes(page: Page, value: string | number[], close = false) {
  const data = typeof value === 'string' ? Array.from(Buffer.from(value)) : value
  await page.evaluate(({ data, close }) => {
    const stream = (window as any).__chatStreams['conversation-a']
    stream.controller.enqueue(new Uint8Array(data))
    if (close) stream.controller.close()
  }, { data, close })
}

function event(type: string, values: Record<string, unknown> = {}) {
  return `data: ${JSON.stringify({ type, ...values })}\n\n`
}

test('streaming renders incremental UTF-8 tokens and completed answers survive reload', async ({ page }) => {
  const saved = await setupChat(page)
  await send(page, 'Explain streaming')
  await expect(page.getByText('Explain streaming', { exact: true })).toBeVisible()
  const chunk = Buffer.from(event('stream', { content: 'Hello 🌍' }))
  const emoji = chunk.indexOf(Buffer.from('🌍'))
  await bytes(page, Array.from(chunk.subarray(0, emoji + 2)))
  await bytes(page, Array.from(chunk.subarray(emoji + 2)))
  await expect(page.getByText('Hello 🌍', { exact: true })).toBeVisible()
  await expect(page.getByPlaceholder(inputPlaceholder)).toBeDisabled()
  await bytes(page, event('stream', { content: ' from the agent' }))
  saved[firstId].push(message(firstId, 'Explain streaming', 'user'), message(firstId, 'Hello 🌍 from the agent'))
  await bytes(page, event('end'), true)
  await expect(page.getByPlaceholder(inputPlaceholder)).toBeEnabled()
  await expect(page.getByText('Hello 🌍 from the agent', { exact: true })).toHaveCount(1)
  await page.reload()
  await expect(page.getByText('Hello 🌍 from the agent', { exact: true })).toHaveCount(1)
})

test('switching conversations cancels the old stream without leaking its content', async ({ page }, testInfo) => {
  await setupChat(page)
  await send(page, 'Question for first conversation')
  await bytes(page, event('stream', { content: 'Partial answer only for first' }))
  await expect(page.getByText('Partial answer only for first', { exact: true })).toBeVisible()
  await page.getByRole('heading', { name: 'Second conversation', exact: true }).click()
  await expect(page.getByText('Saved second conversation', { exact: true })).toBeVisible()
  await expect(page.getByText('Partial answer only for first', { exact: true })).toHaveCount(0)
  await expect(page.getByPlaceholder(inputPlaceholder)).toBeEnabled()
  await expect.poll(() => page.evaluate(() => (window as any).__chatStreams['conversation-a'].aborted)).toBe(true)
  await page.screenshot({ path: testInfo.outputPath('conversation-switch-fixed.png'), fullPage: true })
})

test('stopping a stream restores input and a later send can complete', async ({ page }) => {
  await setupChat(page)
  await send(page, 'First request')
  await bytes(page, event('stream', { content: 'Interrupted answer' }))
  await page.getByRole('button', { name: 'Stop response', exact: true }).click()
  await expect(page.getByPlaceholder(inputPlaceholder)).toBeEnabled()
  await expect(page.getByText('Interrupted answer', { exact: true })).toHaveCount(0)
  await send(page, 'Second request')
  await bytes(page, event('stream', { content: 'Completed second answer' }) + event('end'), true)
  await expect(page.getByText('Completed second answer', { exact: true })).toBeVisible()
  await expect(page.getByPlaceholder(inputPlaceholder)).toBeEnabled()
})

test('a stream that closes without completion reports an error and restores input', async ({ page }, testInfo) => {
  await setupChat(page)
  await send(page, 'Truncated request')
  await bytes(page, event('stream', { content: 'Truncated answer' }), true)
  await expect(page.getByText('An error occurred. Please try again.', { exact: true })).toBeVisible()
  await expect(page.getByPlaceholder(inputPlaceholder)).toBeEnabled()
  await page.screenshot({ path: testInfo.outputPath('truncated-stream-fixed.png'), fullPage: true })
})

test('conversation selection survives reload', async ({ page }) => {
  await setupChat(page)
  await page.getByRole('heading', { name: 'Second conversation', exact: true }).click()
  await expect(page.getByText('Saved second conversation', { exact: true })).toBeVisible()
  await page.reload()
  await expect(page.getByText('Saved second conversation', { exact: true })).toBeVisible()
})

test('provider error restores input and displays an error', async ({ page }) => {
  await setupChat(page)
  await send(page, 'Failing request')
  await bytes(page, event('error', { error: 'Fixture provider failure' }), true)
  await expect(page.getByText('An error occurred. Please try again.', { exact: true })).toBeVisible()
  await expect(page.getByPlaceholder(inputPlaceholder)).toBeEnabled()
})

test('reselecting the current conversation keeps its stream alive', async ({ page }) => {
  await setupChat(page)
  await send(page, 'Keep this stream')
  await bytes(page, event('stream', { content: 'Still streaming' }))
  await page.getByRole('heading', { name: 'First conversation', exact: true }).click()
  await expect(page.getByPlaceholder(inputPlaceholder)).toBeDisabled()
  expect(await page.evaluate(() => (window as any).__chatStreams['conversation-a'].aborted)).toBe(false)
  await bytes(page, event('stream', { content: ' after selection' }) + event('end'), true)
  await expect(page.getByText('Still streaming after selection', { exact: true })).toBeVisible()
})

test('browser back restores the previously selected conversation', async ({ page }) => {
  await setupChat(page)
  await page.getByRole('heading', { name: 'Second conversation', exact: true }).click()
  await expect(page.getByText('Saved second conversation', { exact: true })).toBeVisible()
  await page.goBack()
  await expect(page.getByText('Saved first conversation', { exact: true })).toBeVisible()
})
