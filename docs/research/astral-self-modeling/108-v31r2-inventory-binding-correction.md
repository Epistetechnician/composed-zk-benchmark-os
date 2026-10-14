# V31R2 Inventory Binding Correction

State slice: `astral-rgs-v31r2-inventory-binding-correction`.

Status: `Implemented / HermeticValidationComplete / ModelExecutionUnauthorized`.

V31R2 changes one construction seam: instead of requesting nonexistent
`inventory_sha256`, it canonically hashes the complete established inventory
object containing checkpoint hash, tokenizer hash, and file census. The
regression test freezes that schema. Every scientific variable and gate from
V31 remains unchanged.

Maximum claim: `LocalCorrectedTinyAcquisitionInstrumentV31R2`.
