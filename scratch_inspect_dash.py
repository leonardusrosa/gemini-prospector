import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path('.').resolve()

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1440, 'height': 900})
        dash_path = (ROOT / 'dashboard.html').as_posix()
        await page.goto(f'file:///{dash_path}', wait_until='load')
        await page.wait_for_timeout(1000)
        
        # Check text in body
        text = await page.inner_text('body')
        print('Contains IOST:', 'IOST' in text)
        print('Contains Aline:', 'Aline' in text)
        
        # Check kanban columns
        cols = await page.query_selector_all('.col')
        print('Col count:', len(cols))
        for col in cols:
            title_el = await col.query_selector('.col-h b, .col-h')
            t = await title_el.inner_text() if title_el else ''
            cards = await col.query_selector_all('.card')
            print(f'  Col: {t.strip()} -> {len(cards)} cards')
            for c in cards:
                c_text = await c.inner_text()
                first_line = c_text.splitlines()[0] if c_text else ''
                print(f'    - {first_line}')

        # Click Sites tab
        tab_sites = await page.query_selector('a[href="#sites"], button:has-text("Sites"), nav a:has-text("Sites")')
        if tab_sites:
            await tab_sites.click()
            await page.wait_for_timeout(500)
            site_cards = await page.query_selector_all('.s-card')
            print('Site cards in Sites tab:', len(site_cards))
            for sc in site_cards:
                sc_text = await sc.inner_text()
                first_line = sc_text.splitlines()[0] if sc_text else ''
                print(f'    - Site: {first_line}')

        await page.screenshot(path='qa_dashboard_playwright_verified.png', full_page=True)
        print('Captured qa_dashboard_playwright_verified.png')
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
