from src.webrtc_sim.signaling.app import create_signaling_app


def test_health_route():
    app = create_signaling_app()
    client = app.test_client()
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_offer_creates_session():
    app = create_signaling_app()
    client = app.test_client()
    payload = {"peer_id": "peer-1", "sdp": "v=0", "type": "offer"}
    resp = client.post('/signal/offer', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "session_id" in data
    assert data["answer"]["type"] == "answer"
