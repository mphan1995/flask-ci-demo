"""In-memory signaling session store."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict


@dataclass
class Session:
    session_id: str
    peer_id: str
    created_at: float
    expires_in: int

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.expires_in


class SessionStore:
    def __init__(self, ttl_seconds: int = 180) -> None:
        self.ttl = ttl_seconds
        self.sessions: Dict[str, Session] = {}

    def create(self, session_id: str, peer_id: str) -> Session:
        session = Session(session_id=session_id, peer_id=peer_id, created_at=time.time(), expires_in=self.ttl)
        self.sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        session = self.sessions.get(session_id)
        if session and session.is_expired():
            self.sessions.pop(session_id, None)
            return None
        return session

    def delete(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def cleanup(self) -> None:
        for sid, session in list(self.sessions.items()):
            if session.is_expired():
                self.sessions.pop(sid, None)
