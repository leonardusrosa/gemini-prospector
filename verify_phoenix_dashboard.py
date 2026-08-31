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

async def verify_phoenix_dashboard():
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

        # Wait for data load
        await page.wait_for_timeout(500)

        # 1. Switch to Sites view
        sites_btn = page.locator('nav button:has-text("Sites")')
        await sites_btn.click()
        await page.wait_for_timeout(500)

        # Find Instituto Ferreira card
        instituto_card = page.locator('.site-card:has-text("Instituto Ferreira")')
        assert await instituto_card.count() >= 1, "Instituto Ferreira site card not found!"
        print("Instituto Ferreira site card: FOUND")

        # Check main actions
        main_actions = instituto_card.locator(".s-main")
        admin_btn = main_actions.locator("a.admin-btn")
        assert await admin_btn.count() == 1, "Admin button missing from Instituto card .s-main!"

        admin_text = (await admin_btn.text_content()).strip()
        admin_href = await admin_btn.get_attribute("href")
        admin_target = await admin_btn.get_attribute("target")
        admin_rel = await admin_btn.get_attribute("rel")

        print(f"Admin button text: '{admin_text}'")
        print(f"Admin button href: '{admin_href}'")
        print(f"Admin button target: '{admin_target}'")
        print(f"Admin button rel: '{admin_rel}'")

        assert admin_text == "Admin"
        assert admin_href == "https://prospector.autocora.com.br/clientes/instituto-ferreira-odontologia-rio-claro/admin/"
        assert admin_target == "_blank"
        assert "noopener" in admin_rel and "noreferrer" in admin_rel

        # Check existing primary action
        prim_btn = main_actions.locator("a.prim")
        prim_text = (await prim_btn.text_content()).strip()
        prim_href = await prim_btn.get_attribute("href")
        print(f"Primary action text: '{prim_text.encode('ascii', 'ignore').decode('ascii')}', href: '{prim_href}'")
        assert "Ver no ar" in prim_text or "Ver página" in prim_text

        # 2. Check Admin Page destination HTTP & CMS Auth form
        admin_page = await context.new_page()
        admin_res = await admin_page.goto(admin_href, wait_until="networkidle")
        print(f"Admin Destination HTTP Status: {admin_res.status}")
        assert admin_res.status == 200

        login_form = admin_page.locator("#client-login-form, form, #login-screen")
        print(f"Admin login form present: {await login_form.count() > 0}")
        assert await login_form.count() > 0

        await browser.close()
        print("\n[PASS] All Phoenix Dashboard production verifications passed 100%!")

if __name__ == "__main__":
    asyncio.run(verify_phoenix_dashboard())
