"""Pagination logic for splitting Excel data into pages.

Each page contains:
- Header rows (fixed, repeated on every page)
- Data rows (chunked by page_size)
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.services.excel_parser import Cell, SheetModel, MergedCell


@dataclass
class Page:
    """A single page containing header + data rows."""
    page_number: int
    header_rows: List[List[Cell]] = field(default_factory=list)
    data_rows: List[List[Cell]] = field(default_factory=list)
    merged_cells: List[MergedCell] = field(default_factory=list)


def paginate(
    sheet: SheetModel,
    header_rows: int = 1,
    page_size: int = 10,
) -> List[Page]:
    """Split sheet data into pages.

    Args:
        sheet: Parsed sheet data
        header_rows: Number of header rows to repeat on each page (from top)
        page_size: Number of data rows per page (excluding header)

    Returns:
        List of Page objects, each with header + data chunk
    """
    if not sheet.rows:
        return []

    all_rows = sheet.rows
    total_rows = len(all_rows)

    # Validate header_rows
    if header_rows < 0:
        header_rows = 0
    if header_rows >= total_rows:
        header_rows = max(0, total_rows - 1)

    # Extract header rows (always from the beginning)
    header = all_rows[:header_rows] if header_rows > 0 else []

    # Data rows start after header
    data_rows = all_rows[header_rows:]

    if not data_rows:
        # No data rows, return single page with just header
        if header:
            return [Page(
                page_number=1,
                header_rows=header,
                data_rows=[],
                merged_cells=sheet.merged_cells,
            )]
        return []

    # Split data into chunks
    pages = []
    page_num = 1

    for i in range(0, len(data_rows), page_size):
        chunk = data_rows[i:i + page_size]

        # Filter merged cells relevant to this page
        page_start_row = header_rows + i + 1  # 1-indexed
        page_end_row = header_rows + i + len(chunk)

        relevant_merges = _get_relevant_merges(
            sheet.merged_cells, header_rows, page_start_row, page_end_row
        )

        pages.append(Page(
            page_number=page_num,
            header_rows=header,
            data_rows=chunk,
            merged_cells=relevant_merges,
        ))
        page_num += 1

    return pages


def _get_relevant_merges(
    merged_cells: List[MergedCell],
    header_rows: int,
    page_start_row: int,
    page_end_row: int,
) -> List[MergedCell]:
    """Filter merged cells that are relevant to a specific page.

    Includes:
    - Merges entirely within header rows
    - Merges entirely within the page's data rows
    - Partial overlaps are excluded for simplicity
    """
    relevant = []

    for merge in merged_cells:
        # Header merges (rows 1 to header_rows)
        if merge.max_row <= header_rows:
            relevant.append(merge)
        # Data merges within this page
        elif merge.min_row >= page_start_row and merge.max_row <= page_end_row:
            # Adjust row numbers to be relative to page
            adjusted = MergedCell(
                min_row=merge.min_row - page_start_row + header_rows + 1,
                max_row=merge.max_row - page_start_row + header_rows + 1,
                min_col=merge.min_col,
                max_col=merge.max_col,
            )
            relevant.append(adjusted)

    return relevant


def get_total_pages(total_data_rows: int, page_size: int) -> int:
    """Calculate total number of pages."""
    if page_size <= 0:
        return 1
    return (total_data_rows + page_size - 1) // page_size
