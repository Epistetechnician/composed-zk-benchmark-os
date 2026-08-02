# V41R15 Equal-Example Development Execution Record

State slice: `V41R15EqualExampleDevelopmentExecution`.

Status: `EqualExampleDevelopmentNoSignal / IndependentlyValidated / Consumed`.

Job `job-kgyid` ran one clock-locked H100 attempt with zero restarts. Every
four-microbatch receipt independently verified exact equal-example weights of
`[0.25, 0.25, 0.25, 0.25]`, all 64 steps completed, and fresh-base adapter
reload was exact.

No-update accuracy was 24/96 (`0.25`) overall and 8/32 in each class.
Persistent accuracy was 25/96 (`0.2604166667`): direct 9/32 (`0.28125`),
paraphrase 6/32 (`0.1875`), and composition 10/32 (`0.3125`). Protected
accuracy fell from 16/16 (`1.0`) to 13/16 (`0.8125`). The acquisition-overall,
per-class, advantage, and protection gates all failed.

Equal-example weighting improved protection relative to V41R14's `0.75`, but
acquisition declined from `0.3229166667` to `0.2604166667`. Loss still declined
while every pre-clip gradient norm exceeded `1.0`. The objective-weighting
diagnosis was mechanistically relevant but insufficient.

The independent validator returned `valid=true` with no errors. Bindings:

- semantic result:
  `sha256:893451b417e6654096e87e7494e638f37daf0efe5cb73c2eacf28a6b415966b3`;
- provider artifact `art-5pn2u`, SHA-256
  `dc6ccd753ef9c5a2ffdb916ff5b33095fe2f29275ac736815839352339642138`;
- independent report SHA-256
  `0bda3d48f89e8cbd73cfd894d813975cb07dfbd0606b78293b4d542c88c40536`;
- durable archive
  `/Users/shaanp/Documents/research-artifacts/astral-v41r15-equal-example-no-signal-job-kgyid`;
- mission cost USD 0.163.

V41R15 is consumed. This valid development negative blocks confirmation and
qualification. The next method must address clipping and representation
interference without tuning additional ratios on this reused instrument.
