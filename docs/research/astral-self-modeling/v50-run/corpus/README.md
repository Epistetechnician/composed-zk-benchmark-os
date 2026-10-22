# V50 corpus (public metadata only)

36 Project Gutenberg books (English, declared published 1900 or later; years are operator-declared, titles verified against the Gutenberg header), parsed with spaCy 3.8.16 / en_core_web_sm 3.8.0. Fetched text is not stored in the repository; `corpus-public.json` lists IDs, sizes and SHA-256 of the raw bytes, the document-disjoint splits, gates, and the manifest digest.

Construction rules fixed before any model effect: exact class balance per split; at most 400 items per class per split; subsampling prefers attractor items, then id hash; per-document cap 400. Result: 800 items per split, attractor fraction 72.6% (the protocol minimum is 30%; natural frequency is about 12%, so this corpus over-represents attractors and is a harder test than running text), non-"The" fraction 74.2%.

Label audit: 200 sampled items judged by Claude (AI-assisted, not an independent human); 2 errors (1.0%), both compound subjects with a singular verb. The sample list and per-item booleans are in `label-audit.json`; the owner should spot-check. Dropped candidates: id 242 (title mismatch), 219, 3600, 1342 (declared year before 1900).
