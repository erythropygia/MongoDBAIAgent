import time
import sys
import threading

class LoadingAnimation:
    def __init__(self, message="Processing"):
        self.message = message
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.animate)
        self.thread.start()

    def animate(self):
        chars = ["|", "/", "-", "\\"]
        i = 0
        while self.running:
            sys.stdout.write(f"\r{self.message} {chars[i % len(chars)]} ")
            sys.stdout.flush()
            i += 1
            time.sleep(0.2)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write("\r" + " " * 50 + "\r")  # Temizle
        sys.stdout.flush()
