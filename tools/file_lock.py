import os
import time
import contextlib


@contextlib.contextmanager
def file_lock(lock_path: str, timeout: float = 10.0, poll_interval: float = 0.05):
    """Verrou exclusif cross-platform via creation atomique d'un fichier .lock."""
    os.makedirs(os.path.dirname(lock_path) or ".", exist_ok=True)
    deadline = time.time() + timeout
    acquired = False

    while time.time() < deadline:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            acquired = True
            break
        except FileExistsError:
            time.sleep(poll_interval)

    if not acquired:
        raise TimeoutError(f"Impossible d'acquerir le verrou: {lock_path}")

    try:
        yield
    finally:
        try:
            os.remove(lock_path)
        except OSError:
            pass
