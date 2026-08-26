import asyncio
from playwright.async_api import async_playwright
import os

HTML_PATH = os.path.abspath("sites/instituto-ferreira-odontologia-rio-claro/instituto-ferreira-odontologia-rio-claro.html")
FILE_URL = f"file:///{HTML_PATH.replace(os.sep, '/')}"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # 1. Desktop Test (1440x900)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        
        console_errors = []
        page.on("pageerror", lambda err: console_errors.append(str(err)))
        
        await page.goto(FILE_URL)
        await page.wait_for_timeout(1000) # Allow hero reveal animation to resolve
        
        await page.screenshot(path="desktop_hero_motion.png")
        print("Captured desktop_hero_motion.png")
        
        # Scroll to middle (Treatments & Facilities)
        await page.evaluate("window.scrollTo(0, 1100)")
        await page.wait_for_timeout(600)
        await page.screenshot(path="desktop_mid_facilities.png")
        print("Captured desktop_mid_facilities.png")
        
        # Scroll to Doctor & Location
        await page.evaluate("window.scrollTo(0, 2200)")
        await page.wait_for_timeout(600)
        await page.screenshot(path="desktop_mid_doctor.png")
        print("Captured desktop_mid_doctor.png")
        
        # Full page screenshot
        await page.screenshot(path="desktop_full_motion.png", full_page=True)
        print("Captured desktop_full_motion.png")
        
        # Verify floating WhatsApp visible on scroll
        floating_classes = await page.eval_on_selector("#floatingWhatsapp", "el => el.className")
        print(f"Floating WhatsApp classes on scroll: {floating_classes}")
        
        await context.close()
        
        # 2. Mobile Test (390x844)
        mobile_context = await browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        )
        mobile_page = await mobile_context.new_page()
        mobile_page.on("pageerror", lambda err: console_errors.append(f"Mobile error: {err}"))
        
        await mobile_page.goto(FILE_URL)
        await mobile_page.wait_for_timeout(800)
        await mobile_page.screenshot(path="mobile_hero_motion.png")
        print("Captured mobile_hero_motion.png")
        
        await mobile_page.screenshot(path="mobile_full_motion.png", full_page=True)
        print("Captured mobile_full_motion.png")
        
        await mobile_context.close()
        
        # 3. Reduced Motion Test
        rm_context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            reduced_motion="reduce"
        )
        rm_page = await rm_context.new_page()
        rm_page.on("pageerror", lambda err: console_errors.append(f"Reduced-motion error: {err}"))
        await rm_page.goto(FILE_URL)
        await rm_page.wait_for_timeout(300)
        
        # Check all headers and cards are 100% visible immediately
        hero_opacity = await rm_page.eval_on_selector(".hero-headline", "el => window.getComputedStyle(el).opacity")
        treatments_opacity = await rm_page.eval_on_selector(".treatment-card", "el => window.getComputedStyle(el).opacity")
        print(f"Reduced motion test - hero headline opacity: {hero_opacity}, treatment card opacity: {treatments_opacity}")
        
        await rm_context.close()
        await browser.close()
        
        print("Console errors:", console_errors if console_errors else "ZERO errors (Clean!)")

asyncio.run(main())
