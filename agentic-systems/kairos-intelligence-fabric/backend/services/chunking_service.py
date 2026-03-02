from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    document_title: str
    chunk_index: int
    text: str
    section_title: str = ""
    entity_ids: list[str] = field(default_factory=list)
    source_format: str = "text"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def chunk_document(
    doc_id: str,
    doc_title: str,
    content: str,
    max_chunk_size: int = 800,
    filename: str = "",
) -> list[DocumentChunk]:
    """Split document into chunks using format-aware strategy.

    Detects format from filename extension and delegates to the appropriate
    chunker.  Falls back to text chunking for unknown formats.
    """
    fmt = _detect_format(filename)
    if fmt == "csv":
        return _chunk_csv(doc_id, doc_title, content, max_chunk_size)
    if fmt == "json":
        return _chunk_json(doc_id, doc_title, content, max_chunk_size)
    if fmt == "sql":
        return _chunk_sql(doc_id, doc_title, content, max_chunk_size)
    return _chunk_text(doc_id, doc_title, content, max_chunk_size)


def _detect_format(filename: str) -> str:
    if not filename:
        return "text"
    ext = Path(filename).suffix.lower()
    return {
        ".csv": "csv",
        ".json": "json",
        ".sql": "sql",
        ".md": "text",
        ".txt": "text",
    }.get(ext, "text")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_chunk(
    doc_id: str,
    doc_title: str,
    text: str,
    section: str,
    fmt: str,
    index: int,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=f"{doc_id}::chunk-{index}",
        document_id=doc_id,
        document_title=doc_title,
        chunk_index=index,
        text=text,
        section_title=section,
        entity_ids=_extract_entity_references(text),
        source_format=fmt,
    )


def _extract_section_title(text: str) -> str:
    """Extract numbered section headers like '1. CNC MILL A-7' or '## Section'."""
    for line in text.splitlines()[:3]:
        line = line.strip()
        m = re.match(r"^(\d+\.\s+.+)$", line)
        if m:
            return m.group(1)
        m = re.match(r"^#{1,3}\s+(.+)$", line)
        if m:
            return m.group(1)
    return ""


def _extract_entity_references(text: str) -> list[str]:
    """Extract entity IDs like (equip-cnc-a7) from text."""
    return list(set(re.findall(r"\(([a-z]+-[a-z0-9-]+)\)", text)))


# ---------------------------------------------------------------------------
# Text chunker (original paragraph-boundary strategy)
# ---------------------------------------------------------------------------

def _chunk_text(
    doc_id: str,
    doc_title: str,
    content: str,
    max_chunk_size: int,
) -> list[DocumentChunk]:
    """Split on double-newlines, merge small paragraphs, split oversized at sentences."""
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", content) if p.strip()]

    merged: list[str] = []
    current = ""
    for para in paragraphs:
        if current and len(current) + len(para) + 2 > max_chunk_size:
            merged.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        merged.append(current)

    final_texts: list[str] = []
    for block in merged:
        if len(block) <= max_chunk_size:
            final_texts.append(block)
        else:
            final_texts.extend(_split_at_sentences(block, max_chunk_size))

    return [
        _make_chunk(doc_id, doc_title, text, _extract_section_title(text), "text", i)
        for i, text in enumerate(final_texts)
    ]


def _split_at_sentences(text: str, max_size: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    parts: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > max_size:
            parts.append(current.strip())
            current = sentence
        else:
            current = f"{current} {sentence}" if current else sentence
    if current:
        parts.append(current.strip())
    return parts


# ---------------------------------------------------------------------------
# CSV chunker
# ---------------------------------------------------------------------------

def _chunk_csv(
    doc_id: str,
    doc_title: str,
    content: str,
    max_chunk_size: int,
) -> list[DocumentChunk]:
    """Chunk CSV by rows, repeating the header in every chunk."""
    try:
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
    except csv.Error:
        return _chunk_text(doc_id, doc_title, content, max_chunk_size)

    if len(rows) < 2:
        return [_make_chunk(doc_id, doc_title, content, "", "csv", 0)]

    header = rows[0]
    data_rows = rows[1:]
    header_line = ",".join(header)
    header_prefix = f"CSV Data (columns: {header_line})\n{header_line}\n"

    # Decide rows per chunk — start at 20, reduce if header is wide
    rows_per_chunk = 20
    while rows_per_chunk > 5:
        sample_row = ",".join(data_rows[0]) if data_rows else ""
        estimated = len(header_prefix) + (len(sample_row) + 1) * rows_per_chunk
        if estimated <= max_chunk_size:
            break
        rows_per_chunk -= 5

    chunks: list[DocumentChunk] = []
    for batch_start in range(0, len(data_rows), rows_per_chunk):
        batch = data_rows[batch_start: batch_start + rows_per_chunk]
        body_lines = [",".join(row) for row in batch]
        text = header_prefix + "\n".join(body_lines)

        # Trim rows if still over limit
        while len(text) > max_chunk_size and len(body_lines) > 1:
            body_lines.pop()
            text = header_prefix + "\n".join(body_lines)

        section = _csv_section_title(header, batch, batch_start)
        chunks.append(_make_chunk(doc_id, doc_title, text, section, "csv", len(chunks)))

    return chunks


def _csv_section_title(header: list[str], batch: list[list[str]], start_row: int) -> str:
    """Derive a section title from CSV batch content."""
    # If there's a 'table_name' column, use the unique values from this batch
    for i, col in enumerate(header):
        if col.strip().lower() in ("table_name", "table", "category", "domain"):
            values = sorted({row[i].strip() for row in batch if i < len(row) and row[i].strip()})
            if values:
                return ", ".join(values[:3])
    end_row = start_row + len(batch)
    return f"Rows {start_row + 1}-{end_row}"


# ---------------------------------------------------------------------------
# JSON chunker
# ---------------------------------------------------------------------------

def _chunk_json(
    doc_id: str,
    doc_title: str,
    content: str,
    max_chunk_size: int,
) -> list[DocumentChunk]:
    """Chunk JSON by structure: schema-dict by table, arrays by batch, flat by keys."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return _chunk_text(doc_id, doc_title, content, max_chunk_size)

    if isinstance(data, list):
        return _chunk_json_array(doc_id, doc_title, data, max_chunk_size)
    if isinstance(data, dict):
        if "domains" in data:
            return _chunk_json_schema(doc_id, doc_title, data, max_chunk_size)
        return _chunk_json_flat(doc_id, doc_title, data, max_chunk_size)
    return [_make_chunk(doc_id, doc_title, content, "", "json", 0)]


def _chunk_json_schema(
    doc_id: str,
    doc_title: str,
    data: dict,
    max_chunk_size: int,
) -> list[DocumentChunk]:
    """Chunk a schema dictionary JSON (has 'domains' with nested tables)."""
    chunks: list[DocumentChunk] = []

    # Chunk 0: overview (top-level metadata + domain names)
    overview = {k: v for k, v in data.items() if k != "domains" and k != "cross_domain_relationships"}
    domain_names = [d.get("domain_name", "") for d in data.get("domains", [])]
    overview["domain_names"] = domain_names
    overview_text = f"Schema Overview\n{json.dumps(overview, indent=2)}"
    chunks.append(_make_chunk(doc_id, doc_title, overview_text, "Schema Overview", "json", len(chunks)))

    # One chunk per table in each domain
    for domain in data.get("domains", []):
        domain_name = domain.get("domain_name", "Unknown")
        for table in domain.get("tables", []):
            table_name = table.get("table_name", "unknown")
            section = f"{domain_name} > {table_name}"
            table_text = f"Domain: {domain_name}\nTable: {table_name}\n{json.dumps(table, indent=2)}"

            if len(table_text) <= max_chunk_size:
                chunks.append(_make_chunk(doc_id, doc_title, table_text, section, "json", len(chunks)))
            else:
                # Split large table: columns in one chunk, relationships in another
                base = {k: v for k, v in table.items() if k != "columns" and k != "relationships"}
                cols = table.get("columns", [])
                rels = table.get("relationships", [])

                cols_text = f"Domain: {domain_name}\nTable: {table_name} (columns)\n{json.dumps({**base, 'columns': cols}, indent=2)}"
                chunks.append(_make_chunk(doc_id, doc_title, cols_text, f"{section} (columns)", "json", len(chunks)))

                if rels:
                    rels_text = f"Domain: {domain_name}\nTable: {table_name} (relationships)\n{json.dumps({**base, 'relationships': rels}, indent=2)}"
                    chunks.append(_make_chunk(doc_id, doc_title, rels_text, f"{section} (relationships)", "json", len(chunks)))

    # Cross-domain relationships chunk
    cross = data.get("cross_domain_relationships", [])
    if cross:
        cross_text = f"Cross-Domain Relationships\n{json.dumps(cross, indent=2)}"
        chunks.append(_make_chunk(doc_id, doc_title, cross_text, "Cross-Domain Relationships", "json", len(chunks)))

    return chunks


def _chunk_json_array(
    doc_id: str,
    doc_title: str,
    data: list,
    max_chunk_size: int,
) -> list[DocumentChunk]:
    """Chunk a JSON array by batches, with schema summary in each chunk."""
    if not data:
        return [_make_chunk(doc_id, doc_title, "[]", "", "json", 0)]

    # Build schema summary from first element
    schema_keys = list(data[0].keys()) if isinstance(data[0], dict) else []
    schema_line = f"JSON Array ({len(data)} items, keys: {', '.join(schema_keys)})\n" if schema_keys else ""

    # Estimate items per chunk
    sample = json.dumps(data[0], indent=2)
    items_per_chunk = max(1, (max_chunk_size - len(schema_line)) // (len(sample) + 5))
    items_per_chunk = min(items_per_chunk, 15)

    chunks: list[DocumentChunk] = []
    for batch_start in range(0, len(data), items_per_chunk):
        batch = data[batch_start: batch_start + items_per_chunk]
        batch_text = schema_line + json.dumps(batch, indent=2)

        # Trim if over limit
        while len(batch_text) > max_chunk_size and len(batch) > 1:
            batch.pop()
            batch_text = schema_line + json.dumps(batch, indent=2)

        end = batch_start + len(batch)
        section = f"Items {batch_start + 1}-{end}"
        chunks.append(_make_chunk(doc_id, doc_title, batch_text, section, "json", len(chunks)))

    return chunks


def _chunk_json_flat(
    doc_id: str,
    doc_title: str,
    data: dict,
    max_chunk_size: int,
) -> list[DocumentChunk]:
    """Chunk a flat JSON object — single chunk if small, split by keys if large."""
    full = json.dumps(data, indent=2)
    if len(full) <= max_chunk_size:
        return [_make_chunk(doc_id, doc_title, full, "", "json", 0)]

    # Split by top-level keys, grouping small ones together
    chunks: list[DocumentChunk] = []
    current_keys: list[str] = []
    current_obj: dict = {}

    for key, value in data.items():
        current_keys.append(key)
        current_obj[key] = value
        text = json.dumps(current_obj, indent=2)
        if len(text) > max_chunk_size and len(current_obj) > 1:
            # Emit everything except the last key
            del current_obj[key]
            emit_text = json.dumps(current_obj, indent=2)
            section = ", ".join(current_keys[:-1])
            chunks.append(_make_chunk(doc_id, doc_title, emit_text, section, "json", len(chunks)))
            current_keys = [key]
            current_obj = {key: value}

    if current_obj:
        emit_text = json.dumps(current_obj, indent=2)
        section = ", ".join(current_keys)
        chunks.append(_make_chunk(doc_id, doc_title, emit_text, section, "json", len(chunks)))

    return chunks


# ---------------------------------------------------------------------------
# SQL chunker
# ---------------------------------------------------------------------------

def _chunk_sql(
    doc_id: str,
    doc_title: str,
    content: str,
    max_chunk_size: int,
) -> list[DocumentChunk]:
    """Chunk SQL DDL by CREATE TABLE/VIEW blocks."""
    blocks = _split_sql_blocks(content)
    if not blocks:
        return [_make_chunk(doc_id, doc_title, content, "", "sql", 0)]

    chunks: list[DocumentChunk] = []
    current_text = ""
    current_section = ""

    for block in blocks:
        block_section = _sql_block_title(block)
        if not block_section:
            block_section = current_section

        if current_text and len(current_text) + len(block) + 2 > max_chunk_size:
            chunks.append(_make_chunk(doc_id, doc_title, current_text, current_section, "sql", len(chunks)))
            current_text = block
            current_section = block_section
        else:
            current_text = f"{current_text}\n\n{block}".strip() if current_text else block
            current_section = block_section or current_section

    if current_text:
        chunks.append(_make_chunk(doc_id, doc_title, current_text, current_section, "sql", len(chunks)))

    return chunks


def _split_sql_blocks(content: str) -> list[str]:
    """Split SQL content on CREATE TABLE/VIEW boundaries and section comments.

    Keeps COMMENT ON statements attached to the preceding CREATE block.
    """
    # Split on lines that start a new CREATE or a section divider (-- ===)
    pattern = r"(?=(?:^CREATE\s+(?:TABLE|VIEW)\b|^--\s*={3,}))"
    raw_blocks = re.split(pattern, content, flags=re.MULTILINE | re.IGNORECASE)
    return [b.strip() for b in raw_blocks if b.strip()]


def _sql_block_title(block: str) -> str:
    """Extract table/view name from a SQL block."""
    m = re.search(r"CREATE\s+(?:TABLE|VIEW)\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", block, re.IGNORECASE)
    if m:
        return m.group(1)
    # Check for section comment like "-- CUSTOMER & SALES DOMAIN"
    m = re.match(r"^--\s*=+\s*\n--\s*(.+?)\s*\n", block)
    if m:
        return m.group(1).strip()
    return ""
