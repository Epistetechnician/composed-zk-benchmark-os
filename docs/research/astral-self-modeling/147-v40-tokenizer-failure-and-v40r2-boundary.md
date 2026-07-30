# V40 Tokenizer Failure and V40R2 Boundary

Status: `V40RetiredTokenizerFailure / V40R2ConstructionAuthorized`.

V40 qualified only 9 of 32 targets as canonical single tokens; 23 were
multi-token. No forward pass occurred. The corpus is retired. The original
qualification was console-only, so no immutable-artifact claim is made.

V40R2 must freeze an ordered ordinary-word allowlist before tokenizer access,
select the first 32 canonical single-token entries, fail if fewer qualify, and
only then construct new families and partition seals. Model execution and all
scientific gates remain unauthorized.
