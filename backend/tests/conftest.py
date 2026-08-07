import os

# Keep TestClient lifespan fast and avoid hung watchdog/zeroconf teardown on Windows.
os.environ.setdefault("SHAREBOX_DISABLE_WATCHER", "1")
os.environ.setdefault("SHAREBOX_DISABLE_MDNS", "1")
