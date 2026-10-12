"""A small FastAPI service demonstrating model-service integration.

Replace ``analyze_sequence`` with model inference when moving to a real model.
Keep the HTTP request/response boundary used by the MCP Tool.
"""

from collections import Counter
from hashlib import sha256

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ALLOWED = set("ACDEFGHIKLMNPQRSTVWYBXZUO")
app = FastAPI(title="DSH Starter Sequence Demo", version="1.0")


class AnalyzeRequest(BaseModel):
    sequence: str = Field(min_length=1, max_length=12_000)


def analyze_sequence(raw: str) -> dict:
    lines = raw.strip().splitlines()
    if lines and lines[0].startswith(">"):
        lines = lines[1:]
    if any(line.startswith(">") for line in lines):
        raise ValueError("Provide exactly one FASTA record")
    sequence = "".join("".join(lines).split()).upper()
    if not sequence or len(sequence) > 10_000 or not set(sequence) <= ALLOWED:
        raise ValueError("Provide 1–10000 valid protein residues")
    counts = Counter(sequence)
    return {
        "kind": "deterministic_sequence_statistics",
        "length": len(sequence),
        "amino_acid_counts": dict(sorted(counts.items())),
        "top_residues": [
            {"residue": residue, "count": count}
            for residue, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:5]
        ],
        "sequence_sha256": sha256(sequence.encode("ascii")).hexdigest(),
    }


@app.get("/readyz")
def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    try:
        return analyze_sequence(request.sequence)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
