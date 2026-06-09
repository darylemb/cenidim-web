import { test, expect } from '@playwright/test'

const VIEWPORTS = [
  { name: 'mobile-360', width: 360, height: 720 },
  { name: 'tablet-768', width: 768, height: 1024 },
  { name: 'desktop-1440', width: 1440, height: 900 },
]

const PAGES: { name: string; path: string; heading: RegExp }[] = [
  { name: 'login', path: '/login', heading: /CENIDIM/ },
  { name: 'dashboard', path: '/dashboards', heading: /Dashboards analíticos/ },
  { name: 'songs', path: '/canciones', heading: /Canciones/ },
  { name: 'timeline', path: '/', heading: /Cronología Musical/ },
]

for (const v of VIEWPORTS) {
  test.describe(`Responsive layout @ ${v.name} (${v.width}x${v.height})`, () => {
    for (const p of PAGES) {
      test(`${p.name} page has no horizontal scroll at ${v.width}px`, async ({ page }) => {
        await page.setViewportSize({ width: v.width, height: v.height })
        await page.goto(p.path)
        // Scope to <main> so the nav tab buttons (e.g. "Canciones"
        // in the header) don't satisfy the heading assertion.
        await expect(page.locator('main').getByText(p.heading).first()).toBeVisible()
        // No horizontal scroll: documentElement.scrollWidth should not exceed viewport width.
        const { scrollWidth, clientWidth } = await page.evaluate(() => ({
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        }))
        expect(scrollWidth, `${p.name} should not scroll horizontally at ${v.width}px`).toBeLessThanOrEqual(
          v.width + 1,
        )
        expect(clientWidth).toBeGreaterThan(0)
      })
    }
  })
}
