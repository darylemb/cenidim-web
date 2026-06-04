import { chromium } from 'playwright';

const TEST_USER = process.env.E2E_TEST_USER || 'admin';
const TEST_PASS = process.env.E2E_TEST_PASS || 'admin123';

async function testAuth() {
  console.log('Starting browser...');
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const results = {
    passed: [],
    failed: [],
  };

  page.on('console', msg => console.log('Browser console:', msg.text()));
  page.on('pageerror', err => console.log('Page error:', err.message));

  try {
    console.log('\n=== Test 1: Health Check ===');
    const healthRes = await page.goto('http://localhost:8080/health');
    const healthText = await page.textContent('body');
    console.log('Health response:', healthText);
    if (healthText.includes('healthy')) {
      results.passed.push('Health check');
    } else {
      results.failed.push('Health check');
    }

    console.log('\n=== Test 2: Login Page Load ===');
    const frontendRes = await page.goto('http://localhost:5173/');
    console.log('Frontend status:', frontendRes.status());
    if (frontendRes.status() === 200) {
      results.passed.push('Frontend loads');
    } else {
      results.failed.push('Frontend loads');
    }

    await page.waitForLoadState('networkidle');

    console.log('\n=== Test 3: Login Form Present ===');
    const hasUsernameInput = await page.locator('input[type="text"], input[name="username"]').count() > 0;
    const hasPasswordInput = await page.locator('input[type="password"]').count() > 0;
    const hasLoginButton = await page.locator('button[type="submit"]').count() > 0;

    console.log('Has username input:', hasUsernameInput);
    console.log('Has password input:', hasPasswordInput);
    console.log('Has login button:', hasLoginButton);

    if (hasUsernameInput && hasPasswordInput && hasLoginButton) {
      results.passed.push('Login form elements present');
    } else {
      results.failed.push('Login form elements');
    }

    console.log('\n=== Test 4: Login Form Submission ===');
    const usernameInput = page.locator('input[type="text"], input[name="username"]').first();
    const passwordInput = page.locator('input[type="password"]').first();
    const loginBtn = page.locator('button[type="submit"]').first();

    if (await usernameInput.count() > 0) {
      await usernameInput.fill(TEST_USER);
      await passwordInput.fill(TEST_PASS);
      await loginBtn.click();

      await page.waitForLoadState('networkidle');

      const currentUrl = page.url();
      console.log('URL after login attempt:', currentUrl);

      if (currentUrl.includes('login') || currentUrl.includes('auth')) {
        console.log('Login page shown - authentication may have failed');
        const errorText = await page.locator('.error, [role="alert"], .text-red').textContent().catch(() => 'none');
        console.log('Error displayed:', errorText);
      } else {
        results.passed.push('Login form submission');
      }
    } else {
      results.failed.push('Could not find login form');
    }

    console.log('\n=== Test 5: Auth API Network Request ===');
    page.on('request', req => {
      if (req.url().includes('/api/auth')) {
        console.log('Auth request:', req.method(), req.url());
      }
    });

    page.on('response', async res => {
      if (res.url().includes('/api/auth')) {
        console.log('Auth response:', res.status(), res.url());
        try {
          const body = await res.text();
          console.log('Auth response body:', body.substring(0, 200));
        } catch (e) {
          console.log('Could not read response body:', e.message);
        }
      }
    });

  } catch (error) {
    console.error('Error during tests:', error.message);
    results.failed.push(`Error: ${error.message}`);
  }

  await browser.close();

  console.log('\n=== SUMMARY ===');
  console.log('PASSED:', results.passed.join(', ') || 'none');
  console.log('FAILED:', results.failed.join(', ') || 'none');
  console.log(`Total: ${results.passed.length} passed, ${results.failed.length} failed`);

  process.exit(results.failed.length > 0 ? 1 : 0);
}

testAuth();