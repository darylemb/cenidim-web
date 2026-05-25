import { test, expect } from '@playwright/test';

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173';
const API_URL = process.env.E2E_API_URL || 'http://localhost:8080';

test.describe('Login Page', () => {
  test('should display login form', async ({ page }) => {
    await page.goto(BASE_URL);
    await expect(page.getByPlaceholder('Usuario')).toBeVisible();
    await expect(page.getByPlaceholder('Contraseña')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Iniciar Sesión' })).toBeVisible();
  });
});

test.describe('Dashboard', () => {
  test('should show stats after login', async ({ page }) => {
    await page.goto(BASE_URL);

    await page.getByPlaceholder('Usuario').fill('admin');
    await page.getByPlaceholder('Contraseña').fill('admin123');
    await page.getByRole('button', { name: 'Iniciar Sesión' }).click();

    await page.waitForURL('**/dashboard');

    await expect(page.getByText('Dashboards Analíticos')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Total de Álbumes')).toBeVisible();
    await expect(page.getByText('Total de Canciones')).toBeVisible();
  });
});

test.describe('Songs Page', () => {
  test('should display songs list', async ({ page }) => {
    await page.goto(BASE_URL);

    await page.getByPlaceholder('Usuario').fill('admin');
    await page.getByPlaceholder('Contraseña').fill('admin123');
    await page.getByRole('button', { name: 'Iniciar Sesión' }).click();

    await page.waitForURL('**/dashboard');

    await page.goto(`${BASE_URL}/songs`);

    await expect(page.getByRole('heading', { name: 'Canciones' })).toBeVisible({ timeout: 10000 });
  });
});

test.describe('API Health', () => {
  test('backend health endpoint should respond', async ({ request }) => {
    const response = await request.get(`${API_URL}/health`);
    expect(response.ok()).toBeTruthy();
  });
});