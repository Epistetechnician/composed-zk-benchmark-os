# Aligned RSI BillSum chat-template adaptation V3 preparation closure

State slice: `aligned-rsi-billsum-chat-template-adaptation-v3`.

Governance slice: `global-experiment-assurance-lifecycle-v1`.

Disposition: `PreparationFailedAssistantTurnTrailer`. V3 is terminal.

## Result

A read-only preparation pass failed while tokenizing the first selected fit
row. The pinned Qwen3 tokenizer renders the assistant turn terminator as token
ID `151645` (`<|im_end|>`) and appends one template-separator newline token ID
`198`. The V3 runner incorrectly required the target sequence's final token
to equal the generic EOS ID, which is also `151645`; the actual returned
sequence ended in `[151645, 198]`. This is a template-boundary mismatch, not a
model or curriculum result.

The failure occurred before the formal `prepare` command wrote a
prepared-input receipt, before model loading, and before any forward pass,
fit scoring, adapter update, assessment, activation capture, release, or local
acceptance. The V3 owner output root is absent. No V3 scientific result exists.
The V3 focused suite passed 9 checks, but those tests did not model the
trailing template newline and do not override the real-tokenizer failure.

## Frozen V3 evidence

- Repository revision: `62bf2bfb5b6775327eb635d722bd2a715a2c6a42`; the worktree
  was already dirty.
- Runner SHA-256:
  `20474591c0e6198955ed1180b1a39fdc90be31d2015785ac66faa303ba3eb41b`.
- Protocol manifest SHA-256:
  `d10458ba17e542088bc7d056e07e6988d30ca5e0e7580965e25bddfd18e447c8`.
- Requirements lock SHA-256:
  `6d603511e60da82c21f458a9b9ee0e78be945ae68224ffda2685b5cc35035402`.
- Focused-test SHA-256:
  `a6fa0520152eb0373a11b060345ca5c7ca90d41555c85ed1bcbf3817384ac413`.
- Protocol SHA-256:
  `9c699cd0d1312d437fb34300c536a1c0104e25d0d020541104be4f27dc6c31a8`.
- The pinned local tokenizer identifies `<|im_end|>` as its EOS marker with
  token ID `151645`; the template's final separator is newline token ID `198`.
- No model forward, training, or assessment occurred. Independent acceptance
  was not requested or performed.

## Closure

Do not edit, rerun, or locally accept V3. Its failure is retained as a
preparation-contract outcome. The continuing local end-to-end request is
carried into fresh V4 state slice
`aligned-rsi-billsum-chat-template-adaptation-v4`, which freezes the exact
assistant end marker and excludes the trailing template separator from the
assistant loss. V4 may reuse only pinned raw model/data inputs; V3 outputs are
not inputs.
