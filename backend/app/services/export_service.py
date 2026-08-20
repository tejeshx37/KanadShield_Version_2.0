from datetime import datetime


def render_markdown_notes(*, title: str, sections: list[tuple[str, str]]) -> str:
    """Generates a real Markdown export on request — never a stale
    pre-baked file. Used for AI summaries, comparison results, and
    research-workspace notes."""
    lines = [f"# {title}", "", f"_Generated {datetime.utcnow().isoformat()}Z_", ""]
    for heading, body in sections:
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(body)
        lines.append("")
    return "\n".join(lines)
