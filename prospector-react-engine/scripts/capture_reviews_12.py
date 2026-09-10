import asyncio
from playwright.async_api import async_playwright
import shutil

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        # Desktop View
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        await page.goto("http://localhost:4040/", wait_until="networkidle")
        await page.evaluate('window.scrollTo(0, document.getElementById("reviews").offsetTop - 40)')
        await page.wait_for_timeout(1000)
        
        # Element screenshot desktop
        reviews_el = page.locator('#reviews')
        await reviews_el.screenshot(path="e:/Antigravity/prospector/prospector-react-engine/reviews_element_desktop.png")
        await page.screenshot(path="e:/Antigravity/prospector/prospector-react-engine/reviews_section_12_desktop.png")
        
        # Click on review 04 (Tyler) to verify interactivity
        await page.click('button[aria-label="View review 4 by Tyler"]')
        await page.wait_for_timeout(500)
        await page.screenshot(path="e:/Antigravity/prospector/prospector-react-engine/reviews_section_12_desktop_active4.png")
        await context.close()

        # Mobile View
        context_m = await browser.new_context(viewport={"width": 390, "height": 844})
        page_m = await context_m.new_page()
        await page_m.goto("http://localhost:4040/", wait_until="networkidle")
        await page_m.evaluate('window.scrollTo(0, document.getElementById("reviews").offsetTop - 40)')
        await page_m.wait_for_timeout(1000)
        
        # Element screenshot mobile
        reviews_m = page_m.locator('#reviews')
        await reviews_m.screenshot(path="e:/Antigravity/prospector/prospector-react-engine/reviews_element_mobile.png")
        await page_m.screenshot(path="e:/Antigravity/prospector/prospector-react-engine/reviews_section_12_mobile.png")
        await context_m.close()

        await browser.close()
        print("Captured reviews screenshots successfully")

asyncio.run(run())

shutil.copyfile("e:/Antigravity/prospector/prospector-react-engine/reviews_element_desktop.png", "C:/Users/leo_b/.gemini/antigravity-ide/brain/e9e77699-be15-4e73-a267-218d256e1de1/reviews_element_desktop.png")
shutil.copyfile("e:/Antigravity/prospector/prospector-react-engine/reviews_element_mobile.png", "C:/Users/leo_b/.gemini/antigravity-ide/brain/e9e77699-be15-4e73-a267-218d256e1de1/reviews_element_mobile.png")
shutil.copyfile("e:/Antigravity/prospector/prospector-react-engine/reviews_section_12_desktop.png", "C:/Users/leo_b/.gemini/antigravity-ide/brain/e9e77699-be15-4e73-a267-218d256e1de1/reviews_section_12_desktop.png")
shutil.copyfile("e:/Antigravity/prospector/prospector-react-engine/reviews_section_12_desktop_active4.png", "C:/Users/leo_b/.gemini/antigravity-ide/brain/e9e77699-be15-4e73-a267-218d256e1de1/reviews_section_12_desktop_active4.png")
shutil.copyfile("e:/Antigravity/prospector/prospector-react-engine/reviews_section_12_mobile.png", "C:/Users/leo_b/.gemini/antigravity-ide/brain/e9e77699-be15-4e73-a267-218d256e1de1/reviews_section_12_mobile.png")
print("All screenshots copied to artifacts")
