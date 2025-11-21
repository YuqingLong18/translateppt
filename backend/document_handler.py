"""Shared handlers for extracting and replacing text in supported documents."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from docx import Document
from docx.table import _Cell as DocxCell
from docx.text.paragraph import Paragraph
from openpyxl import load_workbook
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.shapes.base import BaseShape
from pptx.table import _Cell as PptxCell
from pptx.text.text import _Paragraph
from pptx.util import Pt


@dataclass
class TextElement:
    element_id: str
    text: str


def _get_run_font_attributes(runs) -> tuple[Optional[str], Optional[Any]]:
    """Return the first available font name and size from a collection of runs."""
    for run in runs:
        font = getattr(run, "font", None)
        if not font:
            continue
        name = getattr(font, "name", None)
        size = getattr(font, "size", None)
        if name or size:
            return name, size
    return None, None


class DocumentHandler:
    """Base protocol for document handlers."""

    def extract_text(self) -> List[TextElement]:  # pragma: no cover - protocol
        raise NotImplementedError

    def apply_translations(
        self,
        translations: Dict[str, str],
        output_path: Path,
        font_name: Optional[str] = None,
    ) -> Path:  # pragma: no cover - protocol
        raise NotImplementedError


class PowerPointHandler(DocumentHandler):
    """Extracts and applies translations for PowerPoint presentations."""

    BODY_FONT_NAME = "Arial"
    BODY_FONT_SIZE_PT = 24

    def __init__(self, presentation_path: Path):
        self.presentation_path = Path(presentation_path)

    def extract_text(self) -> List[TextElement]:
        presentation = Presentation(self.presentation_path)
        elements: List[TextElement] = []

        for slide_index, slide in enumerate(presentation.slides):
            for shape_index, shape in enumerate(slide.shapes):
                elements.extend(self._extract_from_shape(slide_index, shape_index, shape))

        return elements

    def apply_translations(
        self,
        translations: Dict[str, str],
        output_path: Path,
        font_name: Optional[str] = None,
    ) -> Path:
        presentation = Presentation(self.presentation_path)

        for slide_index, slide in enumerate(presentation.slides):
            for shape_index, shape in enumerate(slide.shapes):
                self._apply_to_shape(slide_index, shape_index, shape, translations)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        presentation.save(output_path)
        return output_path

    # PowerPoint helpers --------------------------------------------------
    def _extract_from_shape(
        self, slide_index: int, shape_index: int, shape: BaseShape
    ) -> List[TextElement]:
        elements: List[TextElement] = []

        if getattr(shape, "has_text_frame", False):
            text_frame = shape.text_frame
            for paragraph_index, paragraph in enumerate(text_frame.paragraphs):
                text = paragraph.text.strip()
                if text:
                    element_id = self._paragraph_id(slide_index, shape_index, paragraph_index)
                    elements.append(TextElement(element_id=element_id, text=text))

        if getattr(shape, "has_table", False):
            table = shape.table
            for row_idx, row in enumerate(table.rows):
                for col_idx, cell in enumerate(row.cells):
                    text = cell.text.strip()
                    if text:
                        element_id = self._cell_id(slide_index, shape_index, row_idx, col_idx)
                        elements.append(TextElement(element_id=element_id, text=text))

        return elements

    def _apply_to_shape(
        self,
        slide_index: int,
        shape_index: int,
        shape: BaseShape,
        translations: Dict[str, str],
    ) -> None:
        if getattr(shape, "has_text_frame", False):
            text_frame = shape.text_frame
            for paragraph_index, paragraph in enumerate(text_frame.paragraphs):
                element_id = self._paragraph_id(slide_index, shape_index, paragraph_index)
                translated = translations.get(element_id)
                if translated is not None:
                    self._replace_ppt_paragraph(paragraph, translated)

        if getattr(shape, "has_table", False):
            table = shape.table
            for row_idx, row in enumerate(table.rows):
                for col_idx, cell in enumerate(row.cells):
                    element_id = self._cell_id(slide_index, shape_index, row_idx, col_idx)
                    translated = translations.get(element_id)
                    if translated is not None:
                        self._replace_ppt_cell(cell, translated)

    @classmethod
    def _replace_ppt_paragraph(cls, paragraph: _Paragraph, new_text: str) -> None:
        paragraph.clear()
        run = paragraph.add_run()
        run.text = new_text
        cls._apply_body_text_format(paragraph, run)

    @classmethod
    def _replace_ppt_cell(cls, cell: PptxCell, new_text: str) -> None:
        text_frame = cell.text_frame
        text_frame.clear()
        paragraph = text_frame.paragraphs[0]
        paragraph.clear()
        run = paragraph.add_run()
        run.text = new_text
        cls._apply_body_text_format(paragraph, run)

    @staticmethod
    def _paragraph_id(slide_index: int, shape_index: int, paragraph_index: int) -> str:
        return f"ppt_s{slide_index}_sh{shape_index}_p{paragraph_index}"

    @staticmethod
    def _cell_id(slide_index: int, shape_index: int, row_index: int, col_index: int) -> str:
        return f"ppt_s{slide_index}_sh{shape_index}_c{row_index}_{col_index}"

    @classmethod
    def _apply_body_text_format(cls, paragraph: _Paragraph, run) -> None:
        paragraph.alignment = PP_ALIGN.LEFT
        paragraph.line_spacing = 1
        run.font.name = cls.BODY_FONT_NAME
        run.font.size = Pt(cls.BODY_FONT_SIZE_PT)


class WordHandler(DocumentHandler):
    """Handles extraction and replacement for Word documents."""

    def __init__(self, document_path: Path):
        self.document_path = Path(document_path)

    def extract_text(self) -> List[TextElement]:
        document = Document(self.document_path)
        elements: List[TextElement] = []

        for paragraph_index, paragraph in enumerate(document.paragraphs):
            text = paragraph.text.strip()
            if text:
                elements.append(TextElement(self._paragraph_id(paragraph_index), text))

        for table_index, table in enumerate(document.tables):
            for row_index, row in enumerate(table.rows):
                for col_index, cell in enumerate(row.cells):
                    text = cell.text.strip()
                    if text:
                        elements.append(
                            TextElement(self._cell_id(table_index, row_index, col_index), text)
                        )

        return elements

    def apply_translations(
        self,
        translations: Dict[str, str],
        output_path: Path,
        font_name: Optional[str] = None,
    ) -> Path:
        document = Document(self.document_path)

        for paragraph_index, paragraph in enumerate(document.paragraphs):
            element_id = self._paragraph_id(paragraph_index)
            translated = translations.get(element_id)
            if translated is not None:
                self._replace_paragraph(paragraph, translated, font_name)

        for table_index, table in enumerate(document.tables):
            for row_index, row in enumerate(table.rows):
                for col_index, cell in enumerate(row.cells):
                    element_id = self._cell_id(table_index, row_index, col_index)
                    translated = translations.get(element_id)
                    if translated is not None:
                        self._replace_cell(cell, translated, font_name)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        document.save(output_path)
        return output_path

    @staticmethod
    def _replace_paragraph(paragraph: Paragraph, new_text: str, font_name: Optional[str]) -> None:
        original_name, original_size = _get_run_font_attributes(paragraph.runs)
        if not original_size and getattr(paragraph, "style", None) and getattr(paragraph.style.font, "size", None):
            original_size = paragraph.style.font.size
        if not original_name and getattr(paragraph, "style", None) and getattr(paragraph.style.font, "name", None):
            original_name = paragraph.style.font.name
        for run in list(paragraph.runs):
            paragraph._p.remove(run._r)
        run = paragraph.add_run(new_text)
        if font_name:
            run.font.name = font_name
        elif original_name:
            run.font.name = original_name
        if original_size:
            run.font.size = original_size

    @staticmethod
    def _replace_cell(cell: DocxCell, new_text: str, font_name: Optional[str]) -> None:
        original_name: Optional[str] = None
        original_size: Optional[Any] = None
        for paragraph in cell.paragraphs:
            name, size = _get_run_font_attributes(paragraph.runs)
            if not original_name and name:
                original_name = name
            if not original_size and size:
                original_size = size
            if original_name and original_size:
                break
        if not original_size and cell.paragraphs:
            style_font = getattr(cell.paragraphs[0].style, "font", None)
            if style_font and getattr(style_font, "size", None):
                original_size = style_font.size
            if not original_name and style_font and getattr(style_font, "name", None):
                original_name = style_font.name
        cell.text = ""
        paragraph = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph("")
        for run in list(paragraph.runs):
            paragraph._p.remove(run._r)
        run = paragraph.add_run(new_text)
        if font_name:
            run.font.name = font_name
        elif original_name:
            run.font.name = original_name
        if original_size:
            run.font.size = original_size

    @staticmethod
    def _paragraph_id(paragraph_index: int) -> str:
        return f"doc_p{paragraph_index}"

    @staticmethod
    def _cell_id(table_index: int, row_index: int, col_index: int) -> str:
        return f"doc_t{table_index}_r{row_index}_c{col_index}"


class ExcelHandler(DocumentHandler):
    """Handles extraction and replacement for Excel workbooks."""

    def __init__(self, workbook_path: Path):
        self.workbook_path = Path(workbook_path)

    def extract_text(self) -> List[TextElement]:
        workbook = load_workbook(self.workbook_path, data_only=True)
        elements: List[TextElement] = []

        for sheet_index, sheet in enumerate(workbook.worksheets):
            for row in sheet.iter_rows():
                for cell in row:
                    value = cell.value
                    if isinstance(value, str):
                        text = value.strip()
                        if text:
                            elements.append(
                                TextElement(self._cell_id(sheet_index, cell.row, cell.column), text)
                            )
        return elements

    def apply_translations(
        self,
        translations: Dict[str, str],
        output_path: Path,
        font_name: Optional[str] = None,
    ) -> Path:
        workbook = load_workbook(self.workbook_path)

        for sheet_index, sheet in enumerate(workbook.worksheets):
            for row in sheet.iter_rows():
                for cell in row:
                    element_id = self._cell_id(sheet_index, cell.row, cell.column)
                    translated = translations.get(element_id)
                    if translated is not None:
                        cell.value = translated
                        if font_name:
                            cell.font = cell.font.copy(name=font_name)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(output_path)
        return output_path

    @staticmethod
    def _cell_id(sheet_index: int, row_index: int, column_index: int) -> str:
        return f"xls_s{sheet_index}_r{row_index}_c{column_index}"


def get_document_handler(path: Path) -> DocumentHandler:
    suffix = Path(path).suffix.lower()
    if suffix == ".pptx":
        return PowerPointHandler(path)
    if suffix == ".docx":
        return WordHandler(path)
    if suffix == ".xlsx":
        return ExcelHandler(path)
    raise ValueError(f"Unsupported file type: {suffix}")
