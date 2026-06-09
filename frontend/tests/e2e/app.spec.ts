import { test, expect } from '@playwright/test';

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173';
const API_URL = process.env.E2E_API_URL || 'http://localhost:8080';

test.describe('Login Page', () => {
  test('should display login form', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await expect(page.getByLabel('Usuario')).toBeVisible();
    await expect(page.getByLabel('Contraseña')).toBeVisible();
    // The form submit button is the second "Acceder" on the page
    // (the first is the header nav link). Scope to the main content.
    await expect(page.locator('#main-content').getByRole('button', { name: 'Acceder' })).toBeVisible();
  });
});

test.describe('Dashboard', () => {
  test('should show stats after login', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    await page.getByLabel('Usuario').fill('admin');
    await page.getByLabel('Contraseña').fill('admin123');
    await page.locator('#main-content').getByRole('button', { name: 'Acceder' }).click();

    // Login redirects to the timeline (root). Navigate to the
    // dashboard explicitly to verify the stats render.
    await page.waitForURL(`${BASE_URL}/`);
    await page.goto(`${BASE_URL}/dashboards`);

    await expect(page.getByRole('heading', { name: 'Dashboards analíticos' })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Total canciones')).toBeVisible();
    await expect(page.getByText('Álbumes').first()).toBeVisible();
  });
});

test.describe('Songs Page', () => {
  test('should display songs list', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    await page.getByLabel('Usuario').fill('admin');
    await page.getByLabel('Contraseña').fill('admin123');
    await page.locator('#main-content').getByRole('button', { name: 'Acceder' }).click();

    await page.waitForURL(`${BASE_URL}/`);

    await page.goto(`${BASE_URL}/canciones`);

    await expect(page.getByRole('heading', { name: 'Canciones' })).toBeVisible({ timeout: 10000 });
  });
});

test.describe('API Health', () => {
  test('backend health endpoint should respond', async ({ request }) => {
    const response = await request.get(`${API_URL}/health`);
    expect(response.ok()).toBeTruthy();
  });
});