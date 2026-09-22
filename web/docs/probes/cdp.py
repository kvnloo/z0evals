"""Minimal CDP driver: launch headless chromium, evaluate JS, return JSON."""
import asyncio, json, subprocess, time, urllib.request, os, signal, sys
import websockets

CHROME = "/usr/sbin/chromium"
PORT = int(os.environ.get("CDP_PORT", "9333"))
WIDTH = int(os.environ.get("VW", "1440"))
HEIGHT = int(os.environ.get("VH", "1200"))


def launch(profile="/tmp/cdp-profile"):
    subprocess.run(["rm", "-rf", profile], check=False)
    p = subprocess.Popen(
        [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
         "--disable-dev-shm-usage", "--hide-scrollbars", "--force-device-scale-factor=1",
         f"--remote-debugging-port={PORT}", f"--user-data-dir={profile}",
         f"--window-size={WIDTH},{HEIGHT}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(120):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
            return p
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("chromium did not expose CDP")


class Page:
    def __init__(self, ws):
        self.ws = ws
        self.i = 0

    async def send(self, method, **params):
        self.i += 1
        mid = self.i
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            msg = json.loads(await self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    async def eval(self, expr, awaitp=True):
        r = await self.send("Runtime.evaluate", expression=expr,
                            returnByValue=True, awaitPromise=awaitp)
        if r.get("exceptionDetails"):
            raise RuntimeError(json.dumps(r["exceptionDetails"])[:900])
        return r["result"].get("value")

    async def goto(self, url):
        await self.send("Page.enable")
        await self.send("Page.navigate", url=url)
        for _ in range(200):
            st = await self.eval("document.readyState", awaitp=False)
            if st == "complete":
                await asyncio.sleep(0.6)
                return
            await asyncio.sleep(0.1)
        raise RuntimeError("page never completed loading")

    async def set_viewport(self, w, h, mobile=False):
        await self.send("Emulation.setDeviceMetricsOverride", width=w, height=h,
                        deviceScaleFactor=1, mobile=mobile)

    async def shot(self, path, full=False):
        p = {"format": "png"}
        if full:
            m = await self.send("Page.getLayoutMetrics")
            cs = m["cssContentSize"]
            p["clip"] = {"x": 0, "y": 0, "width": cs["width"],
                         "height": min(cs["height"], 30000), "scale": 1}
            p["captureBeyondViewport"] = True
        r = await self.send("Page.captureScreenshot", **p)
        open(path, "wb").write(__import__("base64").b64decode(r["data"]))
        return path


async def _open(ensure=True):
    if ensure:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list", timeout=1).read()
        except Exception:
            launch()
    t = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list").read())
    page = [x for x in t if x["type"] == "page"][0]
    ws = await websockets.connect(page["webSocketDebuggerUrl"], max_size=200 * 1024 * 1024)
    pg = Page(ws)
    await pg.send("Runtime.enable")
    await pg.set_viewport(WIDTH, HEIGHT)
    return pg


def run(fn, *a, **kw):
    return asyncio.run(fn(*a, **kw))
