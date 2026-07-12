import { test, expect } from '@playwright/test'

test.describe('Dashboard filters (US2)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboards')
    await expect(page.getByRole('heading', { name: 'Dashboards analíticos' })).toBeVisible()
  })

  test('filter URL round-trips: apply a theme, share URL, view restored', async ({ page }) => {
    // Click the AMOR theme chip
    await page.getByRole('button', { name: 'AMOR' }).click()

    // The URL should now carry the theme filter
    await expect(page).toHaveURL(/theme=AMOR/)

    // A chip should be visible
    await expect(page.getByText(/Tema: AMOR/)).toBeVisible()

    // Navigate to a fresh page and verify the filter is reapplied
    const sharedUrl = page.url()
    const fresh = await page.context().newPage()
    await fresh.goto(sharedUrl)
    await expect(fresh.getByText(/Tema: AMOR/)).toBeVisible()
    await fresh.close()
  })

  test('empty-state renders when filter combination yields zero results', async ({ page }) => {
    // Pick a theme AND a year range that cannot match anything
    await page.getByRole('button', { name: 'AMOR' }).click()
    // Year inputs are labelled "Desde" / "Hasta" and share placeholder "—".
    const yearFrom = page.getByLabel('Desde')
    const yearTo = page.getByLabel('Hasta')
    await yearFrom.fill('1900')
    await yearTo.fill('1901')
    await yearTo.blur()

    // The dashboard shows a custom empty-state label when the filter
    // combination yields zero results.
    await expect(page.getByText('El archivo no devuelve coincidencias para estos filtros.')).toBeVisible()
  })

  test('removing a filter chip restores the broader view', async ({ page }) => {
    await page.getByRole('button', { name: 'AMOR' }).click()
    await expect(page.getByText(/Tema: AMOR/)).toBeVisible()
    // The chip is a <button> with aria-label="Quitar filtro: Tema: AMOR".
    await page.getByRole('button', { name: /Quitar filtro: Tema: AMOR/ }).click()
    await expect(page).not.toHaveURL(/theme=AMOR/)
  })
})
