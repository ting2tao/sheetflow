"""HTML template renderer for generating table pages.

Converts Page objects into HTML using Jinja2 templates.
Preserves Excel styles (fonts, colors, borders, alignment, merges).
"""

import os
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

from app.services.excel_parser import Cell, CellStyle, MergedCell
from app.services.paginator import Page


def _cell_style_to_css(style: CellStyle) -> str:
    """Convert CellStyle to inline CSS string."""
    css_parts = []

    # Font
    if style.font_name:
        css_parts.append(f"font-family: '{style.font_name}', sans-serif")
    if style.font_size:
        # Convert points to pixels (1pt ≈ 1.333px)
        px = round(style.font_size * 1.333)
        css_parts.append(f"font-size: {px}px")
    if style.font_bold:
        css_parts.append("font-weight: bold")
    if style.font_italic:
        css_parts.append("font-style: italic")
    if style.font_color:
        css_parts.append(f"color: {style.font_color}")

    # Background
    if style.bg_color:
        css_parts.append(f"background-color: {style.bg_color}")

    # Borders - use individual sides if available
    borders = []
    if style.border_top:
        borders.append(f"border-top: {style.border_top}")
    if style.border_bottom:
        borders.append(f"border-bottom: {style.border_bottom}")
    if style.border_left:
        borders.append(f"border-left: {style.border_left}")
    if style.border_right:
        borders.append(f"border-right: {style.border_right}")
    css_parts.extend(borders)

    # Alignment
    if style.align_horizontal:
        css_parts.append(f"text-align: {style.align_horizontal}")
    if style.align_vertical:
        # Map Excel vertical alignment to CSS
        val_map = {
            'top': 'top',
            'center': 'middle',
            'bottom': 'bottom',
        }
        css_parts.append(f"vertical-align: {val_map.get(style.align_vertical, 'middle')}")
    if style.wrap_text:
        css_parts.append("white-space: pre-wrap")
        css_parts.append("word-wrap: break-word")

    return "; ".join(css_parts)


def _build_merge_map(merged_cells: List[MergedCell]) -> Dict[tuple, MergedCell]:
    """Build a lookup map for merged cells.

    Returns dict mapping (row, col) -> MergedCell for cells that are
    the top-left corner of a merge.
    """
    merge_map = {}
    for merge in merged_cells:
        key = (merge.min_row, merge.min_col)
        merge_map[key] = merge
    return merge_map


def _is_cell_in_merge(row: int, col: int, merge_map: Dict[tuple, MergedCell]) -> Optional[MergedCell]:
    """Check if a cell is part of a merge (but not the top-left corner)."""
    for merge in merge_map.values():
        if (merge.min_row <= row <= merge.max_row and
            merge.min_col <= col <= merge.max_col):
            if (row, col) != (merge.min_row, merge.min_col):
                return merge
    return None


def render_page_html(
    page: Page,
    column_widths: Optional[Dict[int, float]] = None,
    template_dir: Optional[str] = None,
) -> str:
    """Render a single page to HTML.

    Args:
        page: Page object with header and data rows
        column_widths: Optional column widths from Excel
        template_dir: Directory containing Jinja2 templates

    Returns:
        Rendered HTML string
    """
    if template_dir is None:
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('table.html')

    # Build merge map
    merge_map = _build_merge_map(page.merged_cells)

    # Track cells to skip (part of a merge but not top-left)
    skip_cells = set()
    for merge in page.merged_cells:
        for r in range(merge.min_row, merge.max_row + 1):
            for c in range(merge.min_col, merge.max_col + 1):
                if (r, c) != (merge.min_row, merge.min_col):
                    skip_cells.add((r, c))

    # Combine header and data rows
    all_rows = page.header_rows + page.data_rows

    # Build table data with styles
    table_rows = []
    for row_idx, row_cells in enumerate(all_rows):
        row_data = []
        for col_idx, cell in enumerate(row_cells):
            row_num = row_idx + 1  # 1-indexed
            col_num = col_idx + 1  # 1-indexed

            # Skip cells that are part of a merge (not top-left)
            if (row_num, col_num) in skip_cells:
                continue

            # Check if this cell is a merge origin
            merge = merge_map.get((row_num, col_num))
            colspan = (merge.max_col - merge.min_col + 1) if merge else 1
            rowspan = (merge.max_row - merge.min_row + 1) if merge else 1

            cell_value = cell.value if cell.value is not None else ""
            # Convert to string, handling numbers
            if isinstance(cell_value, float) and cell_value == int(cell_value):
                cell_value = str(int(cell_value))
            else:
                cell_value = str(cell_value)

            row_data.append({
                "value": cell_value,
                "style": _cell_style_to_css(cell.style),
                "colspan": colspan,
                "rowspan": rowspan,
                "is_header": row_idx < len(page.header_rows),
            })
        table_rows.append(row_data)

    # Calculate column widths for CSS
    col_widths = []
    if column_widths and table_rows:
        max_cols = max(len(row) for row in table_rows) if table_rows else 0
        for i in range(1, max_cols + 1):
            width = column_widths.get(i)
            if width:
                # Excel width to pixels (approximate)
                col_widths.append(f"{int(width * 7)}px")
            else:
                col_widths.append("auto")

    return template.render(
        rows=table_rows,
        col_widths=col_widths,
        page_number=page.page_number,
    )
