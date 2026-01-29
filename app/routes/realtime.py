from flask import Blueprint, current_app, Response

realtime_bp = Blueprint("realtime", __name__, url_prefix="/api")


@realtime_bp.get("/events")
def events():
    event_bus = current_app.extensions["events"]
    return Response(event_bus.stream(), mimetype="text/event-stream")

