# Phase 2 RAG Plan

RAG runtime protection is excluded from the MVP. Phase 2 should add:

- Local `.txt` upload, then PDF extraction.
- Retrieved content scanning before prompt assembly.
- Instruction neutralization for retrieved documents.
- Source zone tagging such as `RETRIEVED`.
- Runtime metrics for `indirect_rag_injection`.

The current dataset already includes `indirect_rag_injection` samples so the classifier can learn the class before runtime RAG support exists.
