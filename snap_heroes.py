import asyncio
import pathlib
from playwright.async_api import async_playwright

async def snap_heroes():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        u = pathlib.Path("e:/Antigravity/prospector-sites/clientes/iost-ortodontia-aline-iost-rio-claro/index.html").resolve().as_uri()
        
        # 1440
        p1 = await b.new_page(viewport={"width": 1440, "height": 900})
        await p1.goto(u, wait_until="networkidle")
        await p1.screenshot(path="e:/Antigravity/prospector/hero_snap_1440.png")
        
        # 1920
        p2 = await b.new_page(viewport={"width": 1920, "height": 1080})
        await p2.goto(u, wait_until="networkidle")
        await p2.screenshot(path="e:/Antigravity/prospector/hero_snap_1920.png")

        # 390
        p3 = await b.new_page(viewport={"width": 390, "height": 844})
        await p3.goto(u, wait_until="networkidle")
        await p3.screenshot(path="e:/Antigravity/prospector/hero_snap_mobile.png")
        
        await b.close()

if __name__ == "__main__":
    asyncio.run(snap_heroes())
