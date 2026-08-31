import asyncio
import os
import pathlib
import base64
from playwright.async_api import async_playwright

def get_auth_header():
    user = os.environ.get("PROSPECTOR_DASHBOARD_TEST_USER")
    password = os.environ.get("PROSPECTOR_DASHBOARD_TEST_PASSWORD")
    if not user or not password:
        env_file = pathlib.Path(__file__).parent / ".env.test.local"
        if env_file.is_file():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    if k.strip() == "PROSPECTOR_DASHBOARD_TEST_USER":
                        user = v.strip()
                    elif k.strip() == "PROSPECTOR_DASHBOARD_TEST_PASSWORD":
                        password = v.strip()
    if not user or not password:
        raise SystemExit("Missing PROSPECTOR_DASHBOARD_TEST_USER / PROSPECTOR_DASHBOARD_TEST_PASSWORD environment variables.")
    return "Basic " + base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")

async def verify_live_dashboard():
    url = "https://prospector.autocora.com.br/"
    auth_header = get_auth_header()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            extra_http_headers={"Authorization": auth_header},
            viewport={"width": 1440, "height": 900}
        )
        page = await context.new_page()
        res = await page.goto(url, wait_until="networkidle")
        print(f"Dashboard HTTP Status: {res.status}")
        assert res.status == 200, f"Expected 200, got {res.status}"

        await page.wait_for_timeout(1000)

        # 1. Switch to Sites view
        sites_btn = page.locator('nav button:has-text("Sites")')
        await sites_btn.click()
        await page.wait_for_timeout(1000)

        # 2. Find IOST Ortodontia card
        iost_card = page.locator('.site-card:has-text("IOST Ortodontia")')
        count = await iost_card.count()
        print(f"IOST Ortodontia site card count: {count}")
        assert count >= 1, "IOST Ortodontia site card not found!"

        # Check main actions
        main_actions = iost_card.locator(".s-main")
        admin_btn = main_actions.locator("a.admin-btn")
        assert await admin_btn.count() >= 1, "Admin button missing from IOST card!"

        admin_text = (await admin_btn.first.text_content()).strip()
        admin_href = await admin_btn.first.get_attribute("href")
        print(f"Admin button text: '{admin_text}', href: '{admin_href}'")
        assert admin_text == "Admin"
        assert admin_href == "https://prospector.autocora.com.br/clientes/iost-ortodontia-aline-iost-rio-claro/admin/"

        # Check primary action (Ver no ar)
        prim_btn = main_actions.locator("a.prim")
        assert await prim_btn.count() >= 1, "Primary action button missing!"
        prim_text = (await prim_btn.first.text_content()).strip()
        prim_href = await prim_btn.first.get_attribute("href")
        prim_text_safe = prim_text.encode('ascii', 'ignore').decode('ascii')
        print(f"Primary action text: '{prim_text_safe}', href: '{prim_href}'")
        assert "Ver no ar" in prim_text or "no ar" in prim_text or "Ver" in prim_text
        assert prim_href == "https://prospector-sites-beta.vercel.app/clientes/iost-ortodontia-aline-iost-rio-claro/"

        # Check proposal link
        proposal_link = iost_card.locator('a[data-proposal-slug="iost-ortodontia-aline-iost-rio-claro"]')
        if await proposal_link.count() >= 1:
            prop_href = await proposal_link.first.get_attribute("href")
            print(f"Proposal link href: '{prop_href}'")
            assert "proposta.html" in prop_href

        # Screenshot Dashboard Sites view
        await page.screenshot(path="qa_dashboard_iost_live_verified.png")
        print("Captured qa_dashboard_iost_live_verified.png")

        # 3. Test Admin URL reachable and returns 200
        admin_page = await context.new_page()
        admin_res = await admin_page.goto(admin_href, wait_until="networkidle")
        print(f"Admin URL status: {admin_res.status}")
        assert admin_res.status == 200

        await browser.close()
        print("\n[ALL DASHBOARD UI CHECKS PASSED 100%]")

if __name__ == "__main__":
    asyncio.run(verify_live_dashboard())
