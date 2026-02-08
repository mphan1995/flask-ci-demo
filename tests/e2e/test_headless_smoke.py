from pathlib import Path

from src.webrtc_sim.config import load_config, load_scenario


def test_config_and_scenario_load():
    cfg = load_config(Path('configs/app.yaml'), env={})
    assert cfg.name == 'webrtc-peer-simulator'
    scenario = load_scenario(Path('configs/scenarios/single-peer.yaml'))
    assert scenario.count >= 1
