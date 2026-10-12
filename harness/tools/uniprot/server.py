"""A public HTTP API wrapped as a Python MCP Tool."""

import re
import urllib.error
import urllib.parse
import urllib.request

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("uniprot")
ACCESSION = re.compile(r"^[A-Z0-9]{6,10}$", re.IGNORECASE)
AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWYBXZUO")


def normalize_entry(entry: str) -> str:
    """Accept an accession or UniProtKB Entry URL."""
    value = entry.strip()
    if "://" in value:
        parsed = urllib.parse.urlparse(value)
        if parsed.hostname not in {"uniprot.org", "www.uniprot.org"}:
            raise ValueError("Expected a UniProt Entry URL")
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2 or parts[0].lower() != "uniprotkb":
            raise ValueError("URL must contain /uniprotkb/<accession>")
        value = parts[1]
    value = value.upper()
    if not ACCESSION.fullmatch(value):
        raise ValueError("Invalid UniProt accession")
    return value


@mcp.tool()
def uniprot_get_fasta(entry: str) -> dict[str, str | int]:
    """Fetch one canonical UniProtKB FASTA record by accession or Entry URL."""
    accession = normalize_entry(entry)
    url = f"https://rest.uniprot.org/uniprotkb/{accession}.fasta"
    request = urllib.request.Request(url, headers={"Accept": "text/plain"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            fasta = response.read(100_000).decode("utf-8").strip()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise ValueError(f"UniProt entry not found: {accession}") from exc
        raise RuntimeError(f"UniProt returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"UniProt is unavailable: {exc}") from exc
    lines = fasta.splitlines()
    if len(lines) < 2 or not lines[0].startswith(">") or any(
        line.startswith(">") for line in lines[1:]
    ):
        raise RuntimeError("UniProt returned an invalid FASTA record")
    sequence = "".join(lines[1:]).upper()
    if not sequence or not set(sequence) <= AMINO_ACIDS:
        raise RuntimeError("UniProt returned an invalid protein sequence")
    return {
        "accession": accession,
        "header": lines[0][1:],
        "sequence": sequence,
        "length": len(sequence),
        "source_url": url,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
