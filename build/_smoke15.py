# -*- coding: utf-8 -*-
import asyncio, json
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8137/lettura.html?id=15"
EXPECT = 120
MODES = ["pair", "it", "zh", "col"]


async def run():
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", args=["--no-sandbox"])
        for mode in MODES:
            ctx = await browser.new_context()
            await ctx.add_init_script(
                "localStorage.setItem('grimm_prefs_v1', JSON.stringify(%s));"
                % json.dumps({"mode": mode, "fs": False, "cont": False,
                               "follow": False, "loop": False, "rate": 1, "lang": "it"})
            )
            page = await ctx.new_page()
            cerr = []
            page.on("console", lambda m: cerr.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: cerr.append(str(e)))
            await page.goto(BASE, wait_until="networkidle")
            try:
                await page.wait_for_selector(".para", timeout=15000)
            except Exception as ex:
                errors.append("%s: no .para (%s)" % (mode, ex))
                await ctx.close()
                continue
            paras = await page.eval_on_selector_all(".para", "els=>els.length")
            its = await page.eval_on_selector_all(".it-line", "els=>els.length")
            zhs = await page.eval_on_selector_all(".zh-line", "els=>els.length")
            cls = await page.eval_on_selector("body", "b=>b.className")
            title = await page.title()
            ok = (paras == EXPECT and its == EXPECT and zhs == EXPECT
                  and cls == "mode-" + mode and not cerr)
            if not ok:
                errors.append("%s: paras=%s it=%s zh=%s cls=%s console=%s title=%s"
                              % (mode, paras, its, zhs, cls, cerr[:3], title))
            print("%-5s paras=%d it=%d zh=%d cls=%s console=%d %s"
                  % (mode, paras, its, zhs, cls, len(cerr), "OK" if ok else "FAIL"))
            await ctx.close()
        await browser.close()
    if errors:
        print("SMOKE FAIL:", errors)
        raise SystemExit(1)
    print("SMOKE ALL OK — 4 modes, %d paras each" % EXPECT)


asyncio.run(run())
