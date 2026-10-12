---
name: protein-sequence-summary
description: Summarize a protein sequence supplied directly or fetched from a UniProtKB Entry, using a local FastAPI service.
---

# Protein sequence summary

Use this workflow when the user asks for a protein sequence summary, sequence length or amino-acid composition.

1. If the user gives a UniProtKB accession or Entry URL, call `mcp__uniprot__uniprot_get_fasta` and use its `sequence`. Preserve the accession and source URL in the answer.
2. If the user gives a raw sequence or a single FASTA record, use that sequence directly. Do not call UniProt.
3. Call `mcp__sequence__sequence_analyze` exactly once with the complete sequence.
4. State the length and the most common amino acids, and distinguish calculated statistics from biological interpretation. If a Tool fails, explain the failure rather than inventing results.

This example does not predict drug activity, binding, safety or clinical outcomes.
