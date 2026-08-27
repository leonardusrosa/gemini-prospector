import sys, os, time, sqlite3, traceback
from playwright.sync_api import sync_playwright

def run():
    try:
        print("1. Query initial DB state...", flush=True)
        c = sqlite3.connect('prospector.db')
        cur = c.cursor()
        cur.execute("SELECT status, urlNova, dataProposta FROM leads WHERE slug = 'instituto-ferreira-odontologia-rio-claro'")
        lead_row = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM outreach_history WHERE slug = 'instituto-ferreira-odontologia-rio-claro'")
        hist_count = cur.fetchone()[0]
        c.close()
        print(f"Lead status: {lead_row[0]}, history count: {hist_count}", flush=True)

        print("2. Starting Playwright browser...", flush=True)
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()

            console_errors = []
            page.on("console", lambda m: console_errors.append(f"{m.text} @ {m.location}") if m.type == "error" else None)

            print("3. Navigating to http://127.0.0.1:8765...", flush=True)
            page.goto("http://127.0.0.1:8765", wait_until="load")
            page.wait_for_timeout(1000)
            print("Page title:", page.title(), flush=True)

            print("4. Switching to pipeline view...", flush=True)
            page.evaluate("setView('pipeline')")
            page.wait_for_timeout(1000)

            print("Waiting for proposal link to appear...", flush=True)
            prop_selector = 'a[data-proposal-slug="instituto-ferreira-odontologia-rio-claro"]'
            page.wait_for_selector(prop_selector, timeout=10000)
            prop_link = page.locator(prop_selector).first
            
            href = prop_link.get_attribute("href")
            text = prop_link.text_content().strip()
            print(f"A. 'ver proposta' is visible: TRUE (text: '{text}')", flush=True)
            print(f"B. 'ver proposta' target: {href}", flush=True)
            assert "proposta.html" in href, f"Expected proposta.html in href, got {href}"

            # Check outreach action
            outreach_link = page.locator('a[onclick*="instituto-ferreira-odontologia-rio-claro"]').first
            outreach_text = outreach_link.text_content().strip()
            print(f"C. 'outreach' is a separate action: '{outreach_text}'", flush=True)
            assert outreach_text == "outreach", f"Expected outreach text, got {outreach_text}"

            # Open outreach modal
            print("D. Opening outreach modal...", flush=True)
            outreach_link.click()
            
            modal_selector = '#out-modal-body'
            page.wait_for_selector(modal_selector, timeout=5000)
            page.wait_for_timeout(1500)

            modal_text = page.locator(modal_selector).text_content()
            print(f"Modal body text length: {len(modal_text)}", flush=True)
            clean_snippet = modal_text[:250].encode('ascii', 'replace').decode('ascii')
            print(f"Modal snippet: {clean_snippet}...", flush=True)
            assert "Não foi possível carregar o outreach" not in modal_text, "Outreach loading error in modal"

            # Check WhatsApp evaluation
            print("E. Verifying Evolution / WhatsApp status in modal...", flush=True)
            # Switch tabs
            email_btn = page.locator('button:has-text("E-mail"), .out-tab:has-text("E-mail")').first
            wpp_btn = page.locator('button:has-text("WhatsApp"), .out-tab:has-text("WhatsApp")').first

            if email_btn.is_visible():
                print("Clicking E-mail tab...", flush=True)
                email_btn.click()
                page.wait_for_timeout(500)
                email_msg = page.locator('#out-message-text').input_value()
                print(f"E-mail message preview length: {len(email_msg)}", flush=True)

            if wpp_btn.is_visible():
                print("Clicking WhatsApp tab...", flush=True)
                wpp_btn.click()
                page.wait_for_timeout(500)
                wpp_msg = page.locator('#out-message-text').input_value()
                print(f"WhatsApp message preview length: {len(wpp_msg)}", flush=True)

            # Close modal
            print("Closing outreach modal...", flush=True)
            page.evaluate("fecharOutreach()")
            page.wait_for_timeout(300)
            page.screenshot(path="qa_dashboard_playwright.png")
            print("Captured screenshot: qa_dashboard_playwright.png", flush=True)

            b.close()

        print("5. Checking DB state after QA...", flush=True)
        c = sqlite3.connect('prospector.db')
        cur = c.cursor()
        cur.execute("SELECT status, urlNova, dataProposta FROM leads WHERE slug = 'instituto-ferreira-odontologia-rio-claro'")
        lead_row_after = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM outreach_history WHERE slug = 'instituto-ferreira-odontologia-rio-claro'")
        hist_count_after = cur.fetchone()[0]
        c.close()

        print(f"Lead status after: {lead_row_after[0]} (unchanged: {lead_row == lead_row_after})", flush=True)
        print(f"History count after: {hist_count_after} (unchanged: {hist_count == hist_count_after})", flush=True)
        assert lead_row == lead_row_after, "Lead table was mutated unexpectedly!"
        assert hist_count == hist_count_after, "Outreach history was mutated unexpectedly!"

        filtered_errors = [e for e in console_errors if "favicon" not in e and "discovery/runs" not in e]
        print(f"Filtered console errors ({len(filtered_errors)}): {filtered_errors}", flush=True)
        assert len(filtered_errors) == 0, f"Unexpected console errors: {filtered_errors}"

        print("=== ALL QA TESTS PASSED SUCCESSFULLY ===", flush=True)
    except Exception as e:
        print(f"QA FAILED WITH EXCEPTION: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run()
