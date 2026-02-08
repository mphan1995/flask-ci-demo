# File Responsibilities

## Root
- README.md: Project scope and entry documentation.
- pyproject.toml: Packaging and dependency declaration contract.
- .env.example: Environment variable schema.
- Makefile: Planned task interface for developer and CI workflows.

## docker/
- docker/Dockerfile: Container build intent for headless execution.
- docker/docker-compose.ci.yml: Planned CI test topology.

## configs/
- configs/app.yaml: Runtime, mode, signaling, and control defaults.
- configs/logging.yaml: Structured logging policy and sink definitions.
- configs/scenarios/single-peer.yaml: One-peer smoke test profile.
- configs/scenarios/multi-peer-load.yaml: Large-scale peer load profile.
- configs/media/default-video.yaml: Synthetic video behavior defaults.
- configs/media/default-audio.yaml: Synthetic audio behavior defaults.

## docs/
- docs/architecture.md: Component map and boundaries.
- docs/execution-flow.md: Startup to shutdown runtime sequence.
- docs/signaling-flow.md: Offer/answer/ICE message choreography.
- docs/state-model.md: Peer state machine contract.
- docs/operations-wsl2.md: WSL2 deployment and networking constraints.

## scripts/
- scripts/run-headless.sh: Planned headless launcher.
- scripts/run-interactive.sh: Planned interactive launcher.
- scripts/run-scenario.sh: Planned scenario launcher.

## src/webrtc_sim/
- src/webrtc_sim/main.py: Entry point and mode selection.
- src/webrtc_sim/bootstrap.py: Dependency wiring and subsystem startup order.
- src/webrtc_sim/config.py: Config loading and validation pipeline.

## src/webrtc_sim/signaling/
- src/webrtc_sim/signaling/app.py: Flask app factory and signaling middleware setup.
- src/webrtc_sim/signaling/http_routes.py: HTTP signaling endpoints.
- src/webrtc_sim/signaling/ws_routes.py: WebSocket signaling channel.
- src/webrtc_sim/signaling/schemas.py: Signaling payload validation contracts.
- src/webrtc_sim/signaling/session_store.py: Signaling session correlation store.

## src/webrtc_sim/control/
- src/webrtc_sim/control/api.py: Control API route registration.
- src/webrtc_sim/control/service.py: Control command orchestration logic.
- src/webrtc_sim/control/schemas.py: Control request/response schemas.
- src/webrtc_sim/control/ui_routes.py: Web UI routing.

## src/webrtc_sim/peers/
- src/webrtc_sim/peers/manager.py: Orchestration entrypoint for all peers.
- src/webrtc_sim/peers/factory.py: Peer construction from config and templates.
- src/webrtc_sim/peers/lifecycle.py: Lifecycle operation handlers.
- src/webrtc_sim/peers/state_machine.py: Allowed peer state transitions.
- src/webrtc_sim/peers/registry.py: Active peer instance index.
- src/webrtc_sim/peers/models.py: Peer and session domain models.

## src/webrtc_sim/media/
- src/webrtc_sim/media/profiles.py: Configurable media behavior profiles.
- src/webrtc_sim/media/video_track.py: Synthetic video track integration boundary.
- src/webrtc_sim/media/audio_track.py: Synthetic audio track integration boundary.
- src/webrtc_sim/media/frame_generator.py: Frame/timing production abstraction.
- src/webrtc_sim/media/overlays.py: Dynamic overlay composition definitions.
- src/webrtc_sim/media/patterns.py: Pattern catalog contract.

## src/webrtc_sim/runtime/
- src/webrtc_sim/runtime/event_bus.py: Internal async event distribution.
- src/webrtc_sim/runtime/task_supervisor.py: Task lifecycle, cancellation, fault isolation.
- src/webrtc_sim/runtime/health.py: Health and readiness probes.

## src/webrtc_sim/metrics/
- src/webrtc_sim/metrics/collector.py: Metrics collection coordinator.
- src/webrtc_sim/metrics/models.py: Metric schema definitions.
- src/webrtc_sim/metrics/exporters.py: Metrics sink adapters.
- src/webrtc_sim/metrics/stats_adapter.py: Mapping from WebRTC stats to metric models.

## src/webrtc_sim/logging/
- src/webrtc_sim/logging/config.py: Logging bootstrap and formatter policy.
- src/webrtc_sim/logging/events.py: Structured event taxonomy.

## src/webrtc_sim/integrations/
- src/webrtc_sim/integrations/sfu_adapter.py: SFU-specific interoperability abstraction.
- src/webrtc_sim/integrations/turn_config.py: TURN/STUN configuration resolution.

## src/webrtc_sim/web/
- src/webrtc_sim/web/templates/index.html: Interactive UI shell.
- src/webrtc_sim/web/static/app.js: Browser-side signaling and control actions.
- src/webrtc_sim/web/static/styles.css: UI styling.

## tests/
- tests/unit/test_state_machine.py: State-machine behavior tests.
- tests/unit/test_media_profiles.py: Media profile validation tests.
- tests/integration/test_signaling_offer_answer.py: Signaling negotiation integration test.
- tests/integration/test_multi_peer_lifecycle.py: Multi-peer orchestration integration test.
- tests/e2e/test_headless_smoke.py: Headless scenario end-to-end smoke test.
