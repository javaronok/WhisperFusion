import multiprocessing as mp

class QueueSize:
    def __init__(self, queue: mp.Queue):
        self.queue = queue
        self._counter = mp.Value('i', 0)
        self._lock = mp.Lock()

    def put(self, item):
        self.queue.put(item)
        with self._lock:
            self._counter.value += 1

    def get(self):
        item = self.queue.get()
        with self._lock:
            self._counter.value -= 1
        return item

    def qsize(self):
        with self._lock:
            return self._counter.value

# использование
#transcription_queue = mp.Queue()
#qs = QueueSize(transcription_queue)

# вместо transcription_queue.put(...)  -> qs.put(...)
# вместо transcription_queue.get(...)  -> qs.get(...)
# вместо transcription_queue.qsize()   -> qs.qsize()