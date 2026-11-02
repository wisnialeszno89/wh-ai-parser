# NaviMind V2 client CI validation

This small draft branch triggers the V1/V2 bridge contract workflow against
the current `architecture/navimind-world-model-v2` branch. The test set
includes the V2 HTTP client path that accepts an `AgentTaskV2Contract`
instance as well as serialized mapping input.

No production deployment or change to the V1 runtime is involved.
