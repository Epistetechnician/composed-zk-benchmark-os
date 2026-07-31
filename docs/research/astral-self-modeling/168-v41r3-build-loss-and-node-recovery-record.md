# V41R3 Build Loss and Persistent-Node Recovery Record

State slice: `V41R3BuildLossDiagnosis`.

## Terminal batch result

GiveMeNode job `job-q7phu`, label
`astral-v41r3-h100-profile-r2`, ended `build_failed` at
2026-07-31 03:47 UTC:

```text
image build failed: build lost: the worker stopped reporting before it finished
```

The operator confirmed three free pre-container build attempts. Each attempted
to fetch the finalized 3,822,107,009-byte context at approximately
200–400 KB/s and was reaped after 35 minutes. Attempt 1 began at 02:02:37,
attempt 2 at 02:37:38, and attempt 3 at 03:12:38 UTC. No container,
dependency preflight, model access, scientific command, result, artifact, or
billed attempt occurred.

## Persistent-node diagnosis

Node `astral-v41r3-profile-node-r1` was created with the catalog image
`cuda-12.4` and clock lock enabled. Direct preflight established:

- NVIDIA H100 80 GB HBM3;
- compute capability 9.0;
- driver 580.159.03;
- Python 3.10.12;
- 233 GB available persistent disk;
- no preinstalled Torch.

Source context `ctx-84ed3b2d` eventually passed SHA-256
`210f514c38f4702f0b29500c6a7dd27e54c018f2b613a10cb881fc711e3cafcb`.
The complete Git bundle verified, and detached checkout
`0403e731a91ead32f895b3822db8bcd044424f13` remained clean.

Observed node-side object-storage throughput was approximately 60 KB/s, not
the operator's expected 30–70 MB/s. PyPI installation reached the 915.5 MB
Torch 2.10.0 wheel after building only about 13 MB of cache in 4.5 minutes,
projecting hours before the CUDA dependencies. Command `cmd-54uja` was killed
and the node was stopped. Its encrypted disk remains intact; billing is
stopped.

## Exact unblock

Do not submit another batch build and do not resume the paid node against the
same slow package path. Resume only after one of these is available:

1. the exact GiveMeNode catalog image name containing PyTorch 2.10.0+cu128;
2. a reusable provider snapshot/image reference from the already successful
   V41 image build; or
3. verified restoration of normal node-side package/object throughput.

Ticket `tkt-qrurr` requests the catalog image or reusable snapshot reference.
After that input arrives, wake the same node, re-run exact dependency and H100
preflight, execute the unchanged V41 runner once, export the artifact, validate
it independently, and stop the node immediately.

This record is infrastructure evidence only. The maximum potential artifact
claim remains `RemoteH100RuntimeProfileOnlyV41`; no scientific result or higher
claim exists.
