from __future__ import annotations

from typing import Dict, Any


class RemoteSource:
    """Base class for API adapters (podcast feeds, radio dirs, internal services)."""
    name = "base"

    def search(self, query: str) -> list[Dict[str, Any]]:
        raise NotImplementedError

    def fetch_metadata(self, url: str) -> Dict[str, Any]:
        raise NotImplementedError


class SourceManager:
    def __init__(self):
        self.sources: dict[str, RemoteSource] = {}

    def register(self, source: RemoteSource):
        self.sources[source.name] = source

    def get(self, name: str) -> RemoteSource:
        return self.sources[name]

