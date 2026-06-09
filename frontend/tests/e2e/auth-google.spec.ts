import { test, expect } from '@playwright/test'

test.describe('Google sign-in (US3)', () => {
  test('login page exposes the Google sign-in button', async ({ page }) => {
    await page.goto('/login')
    const link = page.getByRole('link', { name: /Continuar con Google/ })
    await expect(link).toBeVisible()
    // The link must point at the backend's start endpoint.
    await expect(link).toHaveAttribute('href', /\/api\/auth\/google\/start$/)
  })

  test('login page renders the password form below the Google divider', async ({ page }) => {
    await page.goto('/login')
    // The form submit button is the second "Acceder" on the page
    // (the first is the header nav link). Scope to the main content.
    await expect(page.locator('#main-content').getByRole('button', { name: 'Acceder' })).toBeVisible()
    await expect(page.getByText('o', { exact: true })).toBeVisible()
  })

  test('cancelling Google sign-in returns a human-readable error', async ({ page }) => {
    // The /api/auth/google/callback handler is responsible for translating
    // the upstream `error` query into ?google=err=user_cancelled and
    // redirecting back to the SPA. We simulate that navigation here.
    await page.goto('/login?google=err=user_cancelled')
    await expect(page.getByText(/Cancelaste el inicio de sesión con Google/)).toBeVisible()
  })
})
