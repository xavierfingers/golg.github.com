import asyncio
from playwright.async_api import sync_playwright

async def run():
    async with sync_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            print('Navigating to Google...')
            await page.goto('https://www.google.com')
            print('Page loaded. Taking screenshot...')
            await page.screenshot(path='google_screenshot.png')
            print('Screenshot saved as google_screenshot.png')
        except Exception as e:
            print(f'An error occurred: {e}')
        finally:
            await browser.close()
            print('Browser closed.')

if __name__ == '__main__':
    asyncio.run(run())
