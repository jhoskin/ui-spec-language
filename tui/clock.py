"""Controlled clock (HAR-3, HAR-6, FIX-6).

The clock holds the time in ms from the start of a session and a list of
timers. A timer that is due at a clock time has run when the clock shows that
time. Timers that are due at the same time run in the order in which they were
set (FIX-13).
"""
import datetime
import heapq

CLOCK_START = datetime.datetime(2026, 11, 20, 9, 0, 0, tzinfo=datetime.timezone.utc)


class Timer:
    __slots__ = ("due", "seq", "fn", "cancelled")

    def __init__(self, due, seq, fn):
        self.due = due
        self.seq = seq
        self.fn = fn
        self.cancelled = False

    def cancel(self):
        self.cancelled = True


class Clock:
    def __init__(self, start=CLOCK_START):
        self.start = start
        self.now = 0
        self._heap = []
        self._seq = 0

    def schedule(self, delay, fn):
        self._seq += 1
        t = Timer(self.now + max(0, int(delay)), self._seq, fn)
        heapq.heappush(self._heap, (t.due, t.seq, t))
        return t

    def next_due(self):
        while self._heap and self._heap[0][2].cancelled:
            heapq.heappop(self._heap)
        return self._heap[0][0] if self._heap else None

    def advance(self, ms):
        target = self.now + max(0, int(ms))
        while True:
            due = self.next_due()
            if due is None or due > target:
                break
            _, _, t = heapq.heappop(self._heap)
            self.now = due
            t.fn()
        self.now = target

    def iso(self, ms=None):
        """Time as UTC with whole seconds (FIX-10)."""
        ms = self.now if ms is None else ms
        t = self.start + datetime.timedelta(milliseconds=ms)
        t = t.replace(microsecond=0)
        return t.strftime("%Y-%m-%dT%H:%M:%SZ")
