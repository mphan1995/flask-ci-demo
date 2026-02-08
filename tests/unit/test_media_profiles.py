from src.webrtc_sim.media.profiles import from_dict


def test_media_profile_defaults():
    profile = from_dict({"width": 800, "height": 600, "fps": 15, "pattern": "color_bars"}, {"sample_rate": 48000, "channels": 1, "profile": "tone", "tone_hz": 440})
    assert profile.video.width == 800
    assert profile.video.fps == 15
    assert profile.audio.sample_rate == 48000
