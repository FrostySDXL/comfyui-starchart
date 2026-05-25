import re


def _get_helper_body(source_text: str, func_name: str) -> str:
    """Extract the body of a helper function defined in source_text."""
    pattern = rf"^\s*def\s+{re.escape(func_name)}\s*\([^)]*\):"
    lines = source_text.splitlines()
    for i, line in enumerate(lines):
        if re.match(pattern, line):
            indent = len(line) - len(line.lstrip())
            body_lines = []
            for j in range(i + 1, len(lines)):
                next_line = lines[j]
                if next_line.strip() == "":
                    body_lines.append(next_line)
                    continue
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent <= indent:
                    break
                body_lines.append(next_line)
            return "\n".join(body_lines)
    return ""


def _extract_main_body(block: str) -> str:
    """Return the main function body, excluding nested function definitions."""
    lines = block.splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("def ") or stripped.startswith("async def "):
            start_idx = i
            break
    if start_idx is None:
        return block

    handler_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    body_indent = handler_indent + 4

    result = []
    skip_depth = 0

    for line in lines[start_idx + 1 :]:
        if not line.strip():
            if skip_depth == 0:
                result.append(line)
            continue

        line_indent = len(line) - len(line.lstrip())
        stripped = line.lstrip()

        if (
            stripped.startswith("def ") or stripped.startswith("async def ")
        ) and line_indent <= handler_indent:
            break

        if stripped.startswith("def ") or stripped.startswith("async def "):
            if line_indent >= body_indent:
                skip_depth += 1
                continue

        if skip_depth > 0:
            if line_indent <= body_indent:
                skip_depth = 0
                result.append(line)
            else:
                continue
        else:
            result.append(line)

    return "\n".join(result)


def _extract_helper_body_from_main_body(main_body: str, full_source: str) -> str:
    helper_match = re.search(r"return\s+(\w+)\s*\(", main_body)
    if not helper_match or not full_source:
        return ""
    helper_name = helper_match.group(1)
    return _get_helper_body(full_source, helper_name)
