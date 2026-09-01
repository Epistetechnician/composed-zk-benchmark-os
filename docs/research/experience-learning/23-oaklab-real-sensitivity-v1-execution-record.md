# Oak Lab fresh real-panel sensitivity V1 execution

State slice: `oaklab-experience-learning-real-sensitivity-v1`.

## Receipts

External artifact root:
`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-sensitivity-v1`.

Protocol digest:
`30140519e2c275de8e8e3384d5f6ae55918b90edd4dbe4c97b9624b8566c41e0`
Independent review digest:
`ac681a2d66f4ee0d23e0e12661a29d905facc719fc08f31b7f366a10065d40c1`
Result: `real_sensitivity_v1.json`
Result digest:
`b5600c238c60e08c2aea716f8e8c97ff549cd619ecf899013a97b3a22740f7d7`
Independent validation: `VALID`.

The run completed on all four fresh panels. TIDBD is semantically not
applicable because these panels contain no declared nonzero TD reward. All
other arms completed tune selection and locked assessment where finite; IDBD
had no valid candidate on the long-horizon panel under the declared grid.

The local real-sensitivity gate identified `adam_b32` on `event_camera` and
`noisy_mnist`. Publication status remains `no_candidate`: the gate still lacks
the privileged digest-bound joule receipt, and this result is not a substitute
for the global publication gate. No plasticity-guard retuning occurred.

The original failed attempt is superseded. Its default-parameter binding defect
was detected before interpretation; only this corrected result is evidence.
