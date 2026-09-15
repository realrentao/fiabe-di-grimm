# -*- coding: utf-8 -*-
import asyncio, sys
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:8792"

async def run():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(channel="msedge", headless=True)
        except Exception:
            browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.on("console", lambda m: errs.append("CONSOLE " + m.type + ": " + m.text) if m.type == "error" else None)

        print("=== INDEX (catalog) ===")
        await page.goto(BASE + "/index.html", wait_until="load")
        await page.wait_for_timeout(500)
        cards = await page.eval_on_selector_all(".card", "els=>els.length")
        print("card count:", cards)
        first_it = await page.eval_on_selector(".card .card-it", "e=>e.textContent")
        print("first card IT title:", first_it.strip())
        # search filter
        await page.fill("#search", "ranocchio")
        await page.wait_for_timeout(300)
        fc = await page.eval_on_selector_all(".card", "els=>els.length")
        print("after search 'ranocchio' cards:", fc)
        await page.fill("#search", "")
        await page.wait_for_timeout(200)

        print("\n=== READER id=01 ===")
        await page.goto(BASE + "/lettura.html?id=01", wait_until="load")
        await page.wait_for_timeout(500)
        ch_it = await page.eval_on_selector(".ch-it", "e=>e.textContent")
        ch_zh = await page.eval_on_selector(".ch-zh", "e=>e.textContent")
        print("chapter IT:", ch_it.strip(), "| ZH:", ch_zh.strip())
        np = await page.eval_on_selector_all(".para", "els=>els.length")
        print("para count:", np)
        # default mode pair -> both lines visible
        zh_visible_pair = await page.eval_on_selector(".zh-line", "e=>getComputedStyle(e).display!=='none'")
        print("zh-line visible in pair mode:", zh_visible_pair)
        # switch to 仅意语
        await page.click('#modeSeg button[data-mode="it"]')
        await page.wait_for_timeout(150)
        bodycls = await page.eval_on_selector("body", "e=>e.className")
        zh_hidden = await page.eval_on_selector(".zh-line", "e=>getComputedStyle(e).display==='none'")
        print("after 仅意语 -> body.class:", bodycls, "| zh hidden:", zh_hidden)
        # switch to 双栏
        await page.click('#modeSeg button[data-mode="col"]')
        await page.wait_for_timeout(150)
        colcls = await page.eval_on_selector("body", "e=>e.className")
        print("after 双栏 -> body.class:", colcls)
        # switch to 仅中文
        await page.click('#modeSeg button[data-mode="zh"]')
        await page.wait_for_timeout(150)
        it_hidden = await page.eval_on_selector(".it-line", "e=>getComputedStyle(e).display==='none'")
        print("after 仅中文 -> it-line hidden:", it_hidden)
        # back to pair
        await page.click('#modeSeg button[data-mode="pair"]')
        await page.wait_for_timeout(100)

        print("\n=== READER id=75 (1-para story) ===")
        await page.goto(BASE + "/lettura.html?id=75", wait_until="load")
        await page.wait_for_timeout(400)
        ch75 = await page.eval_on_selector(".ch-it", "e=>e.textContent")
        np75 = await page.eval_on_selector_all(".para", "els=>els.length")
        print("chapter IT:", ch75.strip(), "| para count:", np75)

        print("\n=== JS ERRORS ===")
        if errs:
            for e in errs[:20]: print("  ", e)
        else:
            print("  none")

        await browser.close()
        print("\nVERIFY DONE")

asyncio.run(run())
