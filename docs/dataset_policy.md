# Dataset Policy

The dataset builder creates 500 attack prompts and 500 benign prompts. `attack_class` is the authoritative label for classifier training, evaluation grouping, and reporting.

Attack classes:

- `direct_injection`
- `indirect_rag_injection`
- `multi_turn_accumulation`
- `agent_hijacking`
- `prompt_leaking`
- `payload_obfuscation`
- `jailbreak`

`indirect_rag_injection` and `multi_turn_accumulation` are classifier-only in MVP runtime. No dataset prompt contains real credentials, real targets, real organizations, or operational instructions for real systems.
