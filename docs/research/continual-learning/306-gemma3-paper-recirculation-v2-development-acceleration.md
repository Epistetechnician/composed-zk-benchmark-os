# Gemma 3 paper-shaped recirculation V2 development acceleration

State slice: `gemma3-paper-recirculation-schema-resolution-v2-development`

Status: `DevelopmentOnly / ScientificExecutionClosed`

## Purpose

This lane accelerates work that can be completed without making an unreviewed
scientific claim. It exposes implementation bugs, improves search and
abstraction policies, and hardens the semantic oracle before the exact corpus
and scientific execution packet are independently accepted.

## Allowed work

- synthetic corpus fixtures and deterministic fixture generators;
- contract, custody, schema, and tokenizer round-trip tests;
- semantic-oracle implementation and adversarial tests;
- search-policy and abstraction-policy experiments on synthetic tasks;
- Weco dry-runs whose inputs and outputs are explicitly marked synthetic;
- runtime profiling that does not execute the V2 scientific panel or produce
  scientific result artifacts.

## Closed work

- external corpus acquisition or licensing substitution;
- relabeling or consuming the existing V1/FineWeb roots as V2 data;
- model execution against the V2 scientific 16-fit/16-assessment panel;
- provider calls, spending, assessment effects, or publication;
- accepted Evidence Ledger mutation;
- claims above
  `LocalDevelopmentGemma3PaperRecirculationEngineeringV2`.

## Exit condition

The development lane exits when the synthetic oracle and search harness pass
their focused gates and produce a deterministic, reviewable packet. The
scientific lane still requires the exact packet-bound independent review,
external source custody, semantic-oracle pass, and separate execution
authorization defined by protocol V2.
