from __future__ import annotations

import os
import signal
import threading
import time
from typing import Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config import load_config
from .settings import CONFIG_PATH, log

_reload_lock = threading.Lock()
_last_reload = 0.0
_DEBOUNCE_SEC = 0.5
_observer: Optional[Observer] = None


def safe_reload() -> None:
    global _last_reload
    with _reload_lock:
        now = time.monotonic()
        if now - _last_reload < _DEBOUNCE_SEC:
            return
        try:
            load_config()
            _last_reload = now
            log.info("config hot-reloaded")
        except Exception as exc:
            log.error("hot-reload failed: %s", exc)


class _CfgHandler(FileSystemEventHandler):
    def __init__(self, target_path: str):
        super().__init__()
        self._target_path = os.path.realpath(target_path)

    def _maybe(self, path: str) -> None:
        if os.path.realpath(path) == self._target_path:
            safe_reload()

    def on_modified(self, event):
        self._maybe(event.src_path)

    def on_moved(self, event):
        self._maybe(getattr(event, "dest_path", ""))


def start_config_watcher() -> None:
    global _observer
    if _observer:
        return
    path = os.path.realpath(CONFIG_PATH)
    directory = os.path.dirname(path)
    handler = _CfgHandler(path)
    observer = Observer()
    observer.schedule(handler, directory, recursive=False)
    observer.daemon = True
    observer.start()
    _observer = observer
    log.info("watching %s", path)


def _on_sighup(signum, frame):
    log.info("SIGHUP received, reloading config")
    safe_reload()


def install_signal_handler() -> None:
    if not hasattr(signal, "SIGHUP"):
        return
    try:
        signal.signal(signal.SIGHUP, _on_sighup)
    except ValueError:
        # Happens when not in main thread; nothing we can do.
        log.warning("failed to install SIGHUP handler (not in main thread)")
