import re

DECORATOR_RE = re.compile(r'@routes\.(route|get|post|ws)\(\s*["\']([^"\']+)["\']')


def _find_decorator_matches(lines: list[str]) -> list[tuple[int, re.Match]]:
    matches = []
    for index, line in enumerate(lines):
        match = DECORATOR_RE.search(line)
        if match:
            matches.append((index, match))
    return matches


def _get_function_block(lines: list[str], start_index: int, end_index: int) -> str:
    """Return the text between the decorator and the next decorator (or EOF)."""
    return "\n".join(lines[start_index:end_index])
