# V41R22 Single-Case Substrate Calibration Execution Record

State slice: `V41R22SingleCaseUpdateSubstrateCalibration`.

Status: `SingleCaseSubstrateCalibrationComplete / MultiCaseInterferenceSupported / IndependentlyValidated / Consumed`.

The exact case-zero prompt was incorrect before update. The frozen calibration
then produced:

| Arm | Gate | Margin (nats) | Loss ratio | Protected accuracy | Reload |
|---|---|---:|---:|---:|---|
| 64 steps, `2e-4` | pass | 64.0526 | 0.000365 | 0.2500 | exact |
| 512 steps, `2e-4` | pass | 70.7669 | 0.000000847 | 0.3750 | exact |
| 64 steps, `2e-3` | loss-ratio fail | 53.9600 | 0.156472 | 0.2500 | exact |
| 512 steps, `2e-3` | loss-ratio fail | 53.8108 | 1.470316 | 0.3125 | exact |

Protected accuracy began at 1.0000 for every checkpoint-reset arm. The original
64-step, `2e-4` substrate is therefore the frozen minimal passing arm. This
supports `MultiCaseInterferenceSupported`: V41R21 was not caused by an absolute
inability of the adapter to acquire one exact association. It does not prove
multi-case acquisition, composition, retention, continual learning,
self-improvement, or any Astral internal-access claim. Every arm caused severe
protected interference.

Result SHA-256 is
`sha256:9aa4855ff03ba1d29bc7fc1feda4bc5864b7b72dfff6ecfa1183d4c47ac63157`.
Provider artifact `art-9idff` has SHA-256
`ef81732e15119856317243c267f5c10db7b7a053df4120e3c3307f451e3f5146`.
The first validation report was retained as a fail-closed validator defect
(`82f5b2c272bc918d4e9b134e322acff9c47f0df247c44e1ef8a6ab00feda4341`):
scored rows intentionally omit the separately bound prompt. Corrected validator
commit `19eb865ffc9254136def754a68e59d7fe167e396` changed no metric, gate,
interpretation, or artifact byte. Its zero-error report SHA-256 is
`d44b0f12a3a6fd42772d7d715cdd93d7a5a5d40f0e7a31606f07cc9463ebfb67`.
Mission cost was USD 0.697. The node is stopped and the identity is consumed.
