"""Controlled clock (HAR-3, HAR-6).

The application reads time and sets timers only through a Clock. In harness
mode the clock moves only by advance(); in real mode RealClock.sync() moves it
to the elapsed wall time.
"""
import heapq
import itertools
import time


class Clock:
    def __init__(self):
        self.now = 0
        self._heap = []
        self._seq = itertools.count()
        self._cancelled = set()

    def schedule(self, delay, fn):
        """Run fn when the clock shows now + delay. Returns a timer id."""
        tid = next(self._seq)
        heapq.heappush(self._heap, (self.now + max(0, int(delay)), tid, fn))
        return tid

    def cancel(self, tid):
        if tid is not None:
            self._cancelled.add(tid)

    def next_due(self):
        while self._heap and self._heap[0][1] in self._cancelled:
            _, tid, _ = heapq.heappop(self._heap)
            self._cancelled.discard(tid)
        return self._heap[0][0] if self._heap else None

    def advance(self, ms):
        self.advance_to(self.now + max(0, int(ms)))

    def advance_to(self, target):
        """Run each timer that is due at or before target, in order of due time
        (and of scheduling for equal times), then show target."""
        while True:
            due = self.next_due()
            if due is None or due > target:
                break
            due, tid, fn = heapq.heappop(self._heap)
            if due > self.now:
                self.now = due
            fn()
        if target > self.now:
            self.now = target


class RealClock(Clock):
    def __init__(self):
        super().__init__()
        self._t0 = time.monotonic()

    def elapsed(self):
        return int((time.monotonic() - self._t0) * 1000)

    def sync(self):
        self.advance_to(self.elapsed())
