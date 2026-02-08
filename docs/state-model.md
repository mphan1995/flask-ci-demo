# Peer State Model

## States
- `created`: Peer specification accepted.
- `preparing`: WebRTC runtime and synthetic tracks are being initialized.
- `signaling`: Offer/answer exchange has started.
- `negotiating`: ICE candidate exchange and transport setup in progress.
- `connected`: Peer connectivity established.
- `streaming`: Synthetic media actively flowing.
- `degraded`: Stream active but quality thresholds exceeded.
- `stopping`: Controlled teardown in progress.
- `stopped`: Peer fully terminated and registry entry closed.
- `failed`: Unrecoverable error occurred.

## Transition contract
- `created -> preparing -> signaling -> negotiating -> connected -> streaming`
- `streaming -> degraded` when thresholds breach.
- `degraded -> streaming` when quality recovers.
- Any active state can transition to `stopping` on control request.
- `stopping -> stopped` on successful cleanup.
- Any non-terminal state may transition to `failed` on fatal errors.

## Guard conditions
- Signaling cannot start before media and peer connection are provisioned.
- Streaming cannot begin before remote description and connectivity complete.
- Stop is idempotent and safe from any active lifecycle state.
