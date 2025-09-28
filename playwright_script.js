const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    console.log('Navigating to Google...');
    await page.goto('https://www.google.com');
    console.log('Page loaded. Taking screenshot...');
    await page.screenshot({ path: 'google_screenshot.png' });
    console.log('Screenshot saved as google_screenshot.png');
  } catch (error) {
    console.error('An error occurred:', error);
  } finally {
    await browser.close();
    console.log('Browser closed.');
  }
})();
