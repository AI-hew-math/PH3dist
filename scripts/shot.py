import sys, threading, functools, http.server, socketserver
from playwright.sync_api import sync_playwright

web_dir = sys.argv[1]                                   # directory to serve
out = sys.argv[2]                                       # screenshot path
width = int(sys.argv[3]) if len(sys.argv) > 3 else 1280
port = 8137

Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=web_dir)
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", port), Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

msgs = []
with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
    pg = b.new_page(viewport={"width": width, "height": 900})
    pg.on("console", lambda m: msgs.append(f"{m.type}: {m.text}"))
    pg.on("pageerror", lambda e: msgs.append(f"PAGEERROR: {e}"))
    try:
        pg.goto(f"http://127.0.0.1:{port}/", wait_until="load", timeout=15000)
    except Exception as e:
        msgs.append(f"GOTO: {e}")
    pg.wait_for_timeout(1600)
    pg.screenshot(path=out, full_page=True)
    b.close()
httpd.shutdown()
for m in msgs:
    print(m)
print("shot ->", out)
