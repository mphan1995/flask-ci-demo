# Signaling Flow

## Offer/Answer sequence
1. Local peer builds an SDP offer and sets local description.
2. Offer payload is sent via HTTP or WebSocket signaling endpoint.
3. Remote endpoint consumes offer, builds SDP answer, sets local description.
4. Answer payload returns through signaling and is applied as remote description.

## ICE exchange
1. Both peers gather ICE candidates.
2. Trickle candidates are sent incrementally through signaling transport.
3. Candidate messages are correlated by session and peer identifiers.
4. Transport reaches connected state after successful ICE and DTLS completion.

## Session management
- Each negotiation is mapped to a signaling session record.
- Out-of-order candidates are queued until descriptions are ready.
- Session close events clear message queues and correlation state.

## Failure paths
- Negotiation timeout results in failed peer state.
- Invalid SDP or candidate payloads are rejected and logged.
- Connectivity failures trigger lifecycle error handling and cleanup.
