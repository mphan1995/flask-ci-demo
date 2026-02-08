# WSL2 Operations Notes

## Environment assumptions
- Linux userspace only.
- No kernel module requirements.
- No webcam, microphone, or hardware capture dependencies.

## Networking
- Bind simulator services to `0.0.0.0` for host-to-WSL2 browser access.
- Keep signaling and control ports explicit and configurable.
- Document host/guest port forwarding expectations for CI runners.

## Runtime mode guidance
- Prefer headless mode for CI and load execution.
- Use interactive mode for manual validation from a host browser.

## Media constraints
- Use synthetic video/audio generation only.
- Avoid references to `/dev/video*` and audio capture devices.

## CI considerations
- Include deterministic scenario files for smoke and load tiers.
- Track key readiness signals: process liveness, signaling availability, peer convergence.
- Collect structured logs and metrics as CI artifacts.
