# Chumba Labs — product notes

Autonomous agents for HPLC and GC-MS method development.

- **HPLC** is the primary product path: goals → propose → simulate → score → refine.
- **GC-MS** is a thin plugin (oven/flow sketch + rule score), not spectral ID.
- Chromatographic metrics come from deterministic tools, not the LLM.
- Simulation ranks methods for search. Confirm every method on the instrument.
- Out of scope for now: instrument control, LIMS/ELN replace, GxP / 21 CFR Part 11 claims.
