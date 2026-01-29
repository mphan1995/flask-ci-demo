import json
import queue
from typing import Dict, Any


class EventBus:
    def __init__(self):
        self.subscribers: list[queue.Queue] = []

    def publish(self, event: str, data: Dict[str, Any]):
        payload = {"event": event, "data": data}
        for q in list(self.subscribers):
            try:
                q.put_nowait(payload)
            except queue.Full:
                pass

    def stream(self):
        q: queue.Queue = queue.Queue(maxsize=100)
        self.subscribers.append(q)
        try:
            while True:
                payload = q.get()
                event = payload["event"]
                data = json.dumps(payload["data"], ensure_ascii=True)
                yield f"event: {event}\n"
                yield f"data: {data}\n\n"
        finally:
            if q in self.subscribers:
                self.subscribers.remove(q)

