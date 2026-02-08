# Runtime Execution Flow

## Startup
1. CLI entry starts the process in `headless` or `interactive` mode.
2. Configuration loader merges file-based config with environment overrides.
3. Logging and metrics subsystems initialize before network services.
4. Runtime supervisor starts asyncio task groups and shutdown hooks.
5. Flask app starts signaling endpoints and control-plane endpoints.
6. Peer manager starts with an empty registry and scenario scheduler.

## Mode-specific initialization
### Headless mode
- Scenario file is loaded at startup.
- Scenario engine schedules peer creation and churn.
- Control plane remains available for runtime adjustments.

### Interactive mode
- Web UI is served.
- Operator creates peers/scenarios using REST or UI actions.

## Streaming phase
1. Peer manager allocates peer runtime objects from specs.
2. Lifecycle manager initiates signaling.
3. Once negotiated and connected, synthetic tracks begin streaming.
4. Metrics collector polls peer and transport stats at fixed intervals.
5. Logs and status endpoints expose peer progress and anomalies.

## Shutdown
1. Stop request or process signal triggers coordinated teardown.
2. Active peers transition to stopping and close media/transport resources.
3. Registry cleanup finalizes peer lifecycle entries.
4. Runtime supervisor waits for task completion within grace timeout.
5. Process exits only after clean service stop.
