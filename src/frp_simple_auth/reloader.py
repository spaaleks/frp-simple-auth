from __future__ import annotations

import os
import signal
import threading
import time
from typing import Optional, Tuple

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config import load_config
from .settings import CONFIG_PATH, CONFIG_POLL_SEC, log

_reload_lock = threading.Lock()
_last_reload = 0.0
_DEBOUNCE_SEC = 0.5
_observer: Optional[Observer] = None
_poller: Optional[threading.Thread] = None
_stop = threading.Event()
_loaded_sig: Optional[Tuple[int, int, int]] = None


def _stat_signature(path: str) -> Optional[Tuple[int, int, int]]:
    try:
        st = os.stat(path)
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size, st.st_ino)


def safe_reload() -> None:
    global _last_reload, _loaded_sig
    with _reload_lock:
        now = time.monotonic()
        if now - _last_reload < _DEBOUNCE_SEC:
            return
        sig = _stat_signature(CONFIG_PATH)
        try:
            load_config()
            _last_reload = now
            _loaded_sig = sig
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


def _poll_loop(path: str, interval: float) -> None:
    while not _stop.wait(interval):
        sig = _stat_signature(path)
        if sig is not None and sig != _loaded_sig:
            safe_reload()


def start_config_watcher() -> None:
    global _observer, _poller, _loaded_sig
    path = os.path.realpath(CONFIG_PATH)
    _loaded_sig = _stat_signature(path)

    if not _observer:
        handler = _CfgHandler(path)
        observer = Observer()
        try:
            observer.schedule(handler, os.path.dirname(path), recursive=False)
            observer.daemon = True
            observer.start()
            _observer = observer
            log.info("watching %s", path)
        except Exception as exc:
            log.warning("inotify watch unavailable (%s), relying on polling", exc)

    if not _poller and CONFIG_POLL_SEC > 0:
        _stop.clear()
        poller = threading.Thread(
            target=_poll_loop,
            args=(path, CONFIG_POLL_SEC),
            name="config-poller",
            daemon=True,
        )
        poller.start()
        _poller = poller
        log.info("polling %s every %.1fs", path, CONFIG_POLL_SEC)


def stop_config_watcher() -> None:
    global _observer, _poller
    _stop.set()
    if _observer:
        _observer.stop()
        _observer = None
    _poller = None


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
