# src/agents/nodes/prompts.py

WRITER_USER_TEMPLATE = (
    "Topic: {query}\n\n"
    "Reviewed Research Findings:\n{findings_text}\n\n"
    "Please format your response exactly as follows:\n"
    "## Topic: {query}\n"
    "### Key Findings\n"
    "[List of findings ordered by source quality]\n\n"
    "### Confidence Summary\n"
    "[Explain the overall confidence level and any uncertainties]\n\n"
    "### TL;DR Summary\n"
    "[3-5 high-level bullet points summary]"
)
