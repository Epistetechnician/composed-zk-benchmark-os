# V29 Authorization Record

State slice: `astral-calibrated-opaque-causal-channel-v29-authorization`.

The V29 execution is authorized as one offline local run after V28's failed
utility gate. It may load only the frozen local actor and public llama.cpp ABI.
It may not access the network, provider APIs, V25/V26/V27/V28 result data, raw
reasoning traces, credentials, PII, production state, or the Evidence Ledger.

The runner must emit only derived trial summaries to stdout. The aggregator
must write only one aggregate JSON result to `/tmp/astral-v29-calibrated-20260813`
and must set `raw_intermediate_retained` to `false`. A positive result would be
local development evidence only. A negative result closes the slice without
raising any Astral claim ceiling.
