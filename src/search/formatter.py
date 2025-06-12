from typing import Any, Dict, List


def pretty_print(search_data: Dict[Any, Any]) -> str:
    if not search_data or "items" not in search_data:
        return "No Results Found."

    lines: List[str] = []
    lines.append("=" * 80)
    lines.append("SEARCH RESULTS")
    lines.append("=" * 80)

    info = search_data.get("searchInformation", {})
    lines.append(f"Total Results: {info.get('totalResults', 'Unknown')}")
    lines.append(f"Search Time : {info.get('searchTime', 'Unknown')} s")
    lines.append("-" * 80)

    for i, item in enumerate(search_data["items"], 1):
        title = item.get("title", "No Title")
        link = item.get("link", "No Link")
        snippet = item.get("snippet", "No description available")

        lines.extend(
            [
                f"\n{i}. {title}",
                f"   URL : {link}",
                f"   Desc: {snippet}",
                "-" * 80,
            ]
        )
    return "\n".join(lines)
