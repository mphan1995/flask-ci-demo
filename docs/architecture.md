# Architecture

## System intent
A modular simulator that creates synthetic WebRTC peers for SFU/MCU load tests, CI smoke checks, and browser interoperability validation.

## Components

### Control Plane
- Exposes REST and optional web UI endpoints.
- Accepts lifecycle commands for peers and scenarios.
- Returns per-peer and scenario status snapshots.

### Signaling Layer
- Transports SDP and ICE payloads over HTTP and/or WebSocket.
- Correlates messages by peer and session identifiers.
- Does not own peer creation or peer business logic.

### Peer Lifecycle Management
- Owns peer registry and state transitions.
- Coordinates create, negotiate, connect, stream, and stop phases.
- Handles retries, timeouts, and failure classification.

### Media Generation
- Produces synthetic video and audio tracks in software only.
- Supports pattern configuration (color bars, overlays, timestamps).
- Supports per-peer profile variance for realistic load shaping.

### WebRTC Runtime
- Manages aiortc peer connections, transceivers, and stats collection hooks.
- Applies media tracks and connectivity policy.
- Emits transport events and lifecycle updates.

### Observability
- Emits structured logs for lifecycle and signaling events.
- Collects metrics placeholders: fps, RTT, packet loss, bitrate, negotiation latency.
- Provides health/readiness signals for CI orchestration.

### Scenario Engine
- Reads scenario definitions and schedules peer churn behavior.
- Supports single-peer smoke and multi-peer load patterns.

## Boundary rules
- Control plane invokes peer manager only; no direct signaling mutations.
- Signaling layer transports messages only; no lifecycle decisions.
- Media modules are independent from signaling transport.
- Metrics read runtime state but do not control state.
- Runtime supervision isolates failures and supports graceful shutdown.
