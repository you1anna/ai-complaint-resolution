"""
Document Parser Module

Handles extraction of text and structured data from various document formats
including PDF and DOCX files. Used for importing complaints and policy documents.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

# Document parsing libraries
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logging.warning("python-docx not available. DOCX parsing disabled.")

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("pypdf not available. PDF parsing disabled.")

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logging.warning("python-magic not available. File type detection may be less accurate.")

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DocumentMetadata(BaseModel):
    """Metadata extracted from document"""
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    page_count: Optional[int] = None
    author: Optional[str] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    title: Optional[str] = None
    subject: Optional[str] = None


class ParsedDocument(BaseModel):
    """Parsed document with extracted content and metadata"""
    metadata: DocumentMetadata
    text: str
    paragraphs: List[str] = Field(default_factory=list)
    tables: List[List[List[str]]] = Field(default_factory=list)
    structure: Dict[str, Any] = Field(default_factory=dict)

    @property
    def word_count(self) -> int:
        """Count words in extracted text"""
        return len(self.text.split())

    @property
    def char_count(self) -> int:
        """Count characters in extracted text"""
        return len(self.text)


class DocumentParser:
    """
    Parse documents in various formats (PDF, DOCX) to extract text and metadata.

    Supports:
    - PDF documents (via pypdf)
    - Microsoft Word DOCX (via python-docx)
    - Text extraction with structure preservation
    - Metadata extraction
    - Table extraction (DOCX)
    """

    SUPPORTED_FORMATS = {'.pdf', '.docx', '.doc'}

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def detect_file_type(self, file_path: Path) -> str:
        """
        Detect file type based on extension and magic bytes.

        Args:
            file_path: Path to file

        Returns:
            File type (pdf, docx, txt, unknown)
        """
        extension = file_path.suffix.lower()

        # Use python-magic if available for more accurate detection
        if MAGIC_AVAILABLE:
            try:
                mime = magic.from_file(str(file_path), mime=True)
                if 'pdf' in mime:
                    return 'pdf'
                elif 'word' in mime or 'officedocument' in mime:
                    return 'docx'
                elif 'text' in mime:
                    return 'txt'
            except Exception as e:
                self.logger.warning(f"Magic detection failed: {e}, falling back to extension")

        # Fallback to extension-based detection
        if extension in {'.pdf'}:
            return 'pdf'
        elif extension in {'.docx', '.doc'}:
            return 'docx'
        elif extension in {'.txt'}:
            return 'txt'
        else:
            return 'unknown'

    def parse_file(self, file_path: str | Path) -> ParsedDocument:
        """
        Parse a document file and extract text and metadata.

        Args:
            file_path: Path to document file

        Returns:
            ParsedDocument with extracted content

        Raises:
            ValueError: If file format is unsupported or parsing fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        file_type = self.detect_file_type(file_path)
        self.logger.info(f"Parsing {file_type} file: {file_path.name}")

        if file_type == 'pdf':
            return self._parse_pdf(file_path)
        elif file_type == 'docx':
            return self._parse_docx(file_path)
        elif file_type == 'txt':
            return self._parse_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_type} ({file_path.suffix})")

    def _parse_pdf(self, file_path: Path) -> ParsedDocument:
        """
        Parse PDF document.

        Args:
            file_path: Path to PDF file

        Returns:
            ParsedDocument with extracted content
        """
        if not PDF_AVAILABLE:
            raise ValueError("PDF parsing not available. Install pypdf: pip install pypdf")

        try:
            reader = PdfReader(str(file_path))

            # Extract metadata
            metadata = DocumentMetadata(
                file_path=str(file_path),
                file_name=file_path.name,
                file_type='pdf',
                file_size=file_path.stat().st_size,
                page_count=len(reader.pages)
            )

            # Extract PDF metadata if available
            if reader.metadata:
                if reader.metadata.author:
                    metadata.author = reader.metadata.author
                if reader.metadata.title:
                    metadata.title = reader.metadata.title
                if reader.metadata.subject:
                    metadata.subject = reader.metadata.subject
                if reader.metadata.creation_date:
                    metadata.created_date = reader.metadata.creation_date
                if reader.metadata.modification_date:
                    metadata.modified_date = reader.metadata.modification_date

            # Extract text from all pages
            paragraphs = []
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text.strip():
                        paragraphs.append(text)
                except Exception as e:
                    self.logger.warning(f"Failed to extract text from page {page_num}: {e}")

            full_text = "\n\n".join(paragraphs)

            # Create structure information
            structure = {
                'format': 'pdf',
                'pages': len(reader.pages),
                'encrypted': reader.is_encrypted,
            }

            return ParsedDocument(
                metadata=metadata,
                text=full_text,
                paragraphs=paragraphs,
                structure=structure
            )

        except Exception as e:
            self.logger.error(f"Failed to parse PDF {file_path}: {e}")
            raise ValueError(f"PDF parsing failed: {e}")

    def _parse_docx(self, file_path: Path) -> ParsedDocument:
        """
        Parse DOCX document.

        Args:
            file_path: Path to DOCX file

        Returns:
            ParsedDocument with extracted content
        """
        if not DOCX_AVAILABLE:
            raise ValueError("DOCX parsing not available. Install python-docx: pip install python-docx")

        try:
            doc = Document(str(file_path))

            # Extract metadata
            metadata = DocumentMetadata(
                file_path=str(file_path),
                file_name=file_path.name,
                file_type='docx',
                file_size=file_path.stat().st_size
            )

            # Extract core properties if available
            if hasattr(doc, 'core_properties'):
                props = doc.core_properties
                if props.author:
                    metadata.author = props.author
                if props.title:
                    metadata.title = props.title
                if props.subject:
                    metadata.subject = props.subject
                if props.created:
                    metadata.created_date = props.created
                if props.modified:
                    metadata.modified_date = props.modified

            # Extract paragraphs
            paragraphs = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)

            full_text = "\n\n".join(paragraphs)

            # Extract tables
            tables = []
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    table_data.append(row_data)
                tables.append(table_data)

            # Create structure information
            structure = {
                'format': 'docx',
                'paragraph_count': len(paragraphs),
                'table_count': len(tables),
                'has_tables': len(tables) > 0
            }

            return ParsedDocument(
                metadata=metadata,
                text=full_text,
                paragraphs=paragraphs,
                tables=tables,
                structure=structure
            )

        except Exception as e:
            self.logger.error(f"Failed to parse DOCX {file_path}: {e}")
            raise ValueError(f"DOCX parsing failed: {e}")

    def _parse_text(self, file_path: Path) -> ParsedDocument:
        """
        Parse plain text file.

        Args:
            file_path: Path to text file

        Returns:
            ParsedDocument with extracted content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Split into paragraphs (by blank lines)
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

            metadata = DocumentMetadata(
                file_path=str(file_path),
                file_name=file_path.name,
                file_type='txt',
                file_size=file_path.stat().st_size
            )

            structure = {
                'format': 'txt',
                'paragraph_count': len(paragraphs)
            }

            return ParsedDocument(
                metadata=metadata,
                text=text,
                paragraphs=paragraphs,
                structure=structure
            )

        except Exception as e:
            self.logger.error(f"Failed to parse text file {file_path}: {e}")
            raise ValueError(f"Text file parsing failed: {e}")

    def extract_complaint_data(self, parsed_doc: ParsedDocument) -> Dict[str, Any]:
        """
        Extract structured complaint data from parsed document.

        This attempts to identify common complaint fields like:
        - Complaint ID
        - Customer name
        - Date received
        - Policy number
        - Complaint text

        Args:
            parsed_doc: Parsed document

        Returns:
            Dictionary with extracted complaint fields
        """
        text = parsed_doc.text

        # Extract potential complaint ID (various patterns)
        complaint_id = None
        patterns = [
            r'complaint\s*(?:id|number|#|ref|reference)?\s*:?\s*([A-Z0-9\-]+)',
            r'reference\s*(?:number|#)?\s*:?\s*([A-Z0-9\-]+)',
            r'case\s*(?:id|number|#)?\s*:?\s*([A-Z0-9\-]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                complaint_id = match.group(1)
                break

        # Extract customer name
        customer_name = None
        name_patterns = [
            r'(?:customer|client|name)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'from\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                customer_name = match.group(1)
                break

        # Extract policy number
        policy_number = None
        policy_patterns = [
            r'policy\s*(?:number|#)?\s*:?\s*([A-Z0-9\-]+)',
            r'policy\s*:?\s*([A-Z0-9]{6,})',
        ]
        for pattern in policy_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                policy_number = match.group(1)
                break

        # Extract dates
        date_received = None
        date_patterns = [
            r'(?:date|received|submitted)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}-\d{2}-\d{2})',  # ISO format
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_received = match.group(1)
                break

        # Determine language (simple heuristic)
        language = self._detect_language(text)

        return {
            'complaint_id': complaint_id,
            'customer_name': customer_name,
            'policy_number': policy_number,
            'date_received': date_received,
            'complaint_text': text,
            'customer_language': language,
            'metadata': {
                'source_file': parsed_doc.metadata.file_name,
                'file_type': parsed_doc.metadata.file_type,
                'page_count': parsed_doc.metadata.page_count,
                'word_count': parsed_doc.word_count,
            }
        }

    def _detect_language(self, text: str) -> str:
        """
        Simple language detection based on common words.

        Args:
            text: Text to analyze

        Returns:
            Language code (en, it, de, fr, es)
        """
        text_lower = text.lower()

        # Italian indicators
        italian_words = ['sono', 'della', 'questa', 'alla', 'degli', 'negli', 'anche', 'essere']
        italian_score = sum(1 for word in italian_words if word in text_lower)

        # German indicators
        german_words = ['der', 'die', 'das', 'und', 'ist', 'nicht', 'sie', 'ich']
        german_score = sum(1 for word in german_words if word in text_lower)

        # French indicators
        french_words = ['le', 'la', 'les', 'est', 'pas', 'pour', 'dans', 'nous']
        french_score = sum(1 for word in french_words if word in text_lower)

        # Spanish indicators
        spanish_words = ['el', 'la', 'los', 'las', 'es', 'por', 'para', 'con']
        spanish_score = sum(1 for word in spanish_words if word in text_lower)

        # English indicators
        english_words = ['the', 'is', 'and', 'or', 'not', 'for', 'with', 'this']
        english_score = sum(1 for word in english_words if word in text_lower)

        scores = {
            'en': english_score,
            'it': italian_score,
            'de': german_score,
            'fr': french_score,
            'es': spanish_score,
        }

        detected = max(scores, key=scores.get)
        return detected if scores[detected] > 0 else 'en'


def parse_document(file_path: str | Path) -> ParsedDocument:
    """
    Convenience function to parse a document.

    Args:
        file_path: Path to document file

    Returns:
        ParsedDocument with extracted content
    """
    parser = DocumentParser()
    return parser.parse_file(file_path)


def extract_complaint_from_file(file_path: str | Path) -> Dict[str, Any]:
    """
    Convenience function to extract complaint data from a document file.

    Args:
        file_path: Path to document file

    Returns:
        Dictionary with extracted complaint fields
    """
    parser = DocumentParser()
    parsed_doc = parser.parse_file(file_path)
    return parser.extract_complaint_data(parsed_doc)
