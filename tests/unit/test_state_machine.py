import pytest

from src.webrtc_sim.peers.state_machine import can_transition


def test_valid_transitions():
    assert can_transition("created", "preparing")
    assert can_transition("connected", "streaming")


def test_invalid_transition():
    assert not can_transition("streaming", "created")
    assert not can_transition("stopped", "streaming")
