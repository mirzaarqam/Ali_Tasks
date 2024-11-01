import time
import sys
import itertools
import threading
from typing import Optional
class ProgressIndicator:
    def __init__(self, description: str = "Processing"):
        self.description = description
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

    def _animate(self):
        for c in itertools.cycle(['⢿', '⣻', '⣽', '⣾', '⣷', '⣯', '⣟', '⡿']):
            if not self.is_running:
                break
            sys.stdout.write(f'\r{self.description} {c}')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\r')

    def start(self):
        self.is_running = True
        self._thread = threading.Thread(target=self._animate)
        self._thread.start()

    def stop(self):
        self.is_running = False
        if self._thread is not None:
            self._thread.join()

