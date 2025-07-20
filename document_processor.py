"""
Document processing module for OncoStaging application.
Handles file validation, text extraction, and document processing.
"""

import fitz  # PyMuPDF
import docx
import hashlib
import logging
from typing import Optional, BinaryIO
from pathlib import Path

from config import config_manager
from exceptions import DocumentProcessingError, FileValidationError


class DocumentProcessor:
    """Handles document processing operations with validation and error handling."""
    
    def __init__(self):
        self.config = config_manager.config
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
    
    def validate_file(self, file) -> bool:
        """
        Validate uploaded file for security and format compliance.
        
        Args:
            file: Uploaded file object
            
        Returns:
            bool: True if file is valid
            
        Raises:
            FileValidationError: If file validation fails
        """
        try:
            # Check file extension
            if not hasattr(file, 'name') or not file.name:
                raise FileValidationError("File must have a valid name")
            
            file_extension = Path(file.name).suffix.lower().lstrip('.')
            if file_extension not in self.config.ALLOWED_EXTENSIONS:
                raise FileValidationError(
                    f"File type '{file_extension}' not allowed. "
                    f"Allowed types: {', '.join(self.config.ALLOWED_EXTENSIONS)}"
                )
            
            # Check file size
            if hasattr(file, 'size'):
                max_size_bytes = self.config.MAX_FILE_SIZE_MB * 1024 * 1024
                if file.size > max_size_bytes:
                    raise FileValidationError(
                        f"File size ({file.size / 1024 / 1024:.1f}MB) exceeds "
                        f"maximum allowed size ({self.config.MAX_FILE_SIZE_MB}MB)"
                    )
            
            # Basic content validation
            if hasattr(file, 'read'):
                # Read a small portion to check if file is readable
                current_pos = file.tell() if hasattr(file, 'tell') else 0
                try:
                    content_sample = file.read(1024)
                    if not content_sample:
                        raise FileValidationError("File appears to be empty")
                finally:
                    # Reset file position
                    if hasattr(file, 'seek'):
                        file.seek(current_pos)
            
            self.logger.info(f"File validation successful: {file.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"File validation failed: {str(e)}")
            if isinstance(e, FileValidationError):
                raise
            raise FileValidationError(f"File validation error: {str(e)}")
    
    def extract_text(self, file) -> str:
        """
        Extract text from uploaded file with comprehensive error handling.
        
        Args:
            file: Uploaded file object (PDF or DOCX)
            
        Returns:
            str: Extracted text content
            
        Raises:
            DocumentProcessingError: If text extraction fails
        """
        try:
            # Validate file first
            self.validate_file(file)
            
            file_extension = Path(file.name).suffix.lower()
            extracted_text = ""
            
            if file_extension == ".pdf":
                extracted_text = self._extract_from_pdf(file)
            elif file_extension == ".docx":
                extracted_text = self._extract_from_docx(file)
            else:
                raise DocumentProcessingError(f"Unsupported file type: {file_extension}")
            
            # Validate extracted text
            if not extracted_text or not extracted_text.strip():
                raise DocumentProcessingError("No text could be extracted from the document")
            
            if len(extracted_text) > self.config.MAX_TEXT_LENGTH:
                self.logger.warning(f"Text length ({len(extracted_text)}) exceeds maximum, truncating")
                extracted_text = extracted_text[:self.config.MAX_TEXT_LENGTH]
            
            self.logger.info(f"Text extraction successful: {len(extracted_text)} characters")
            return extracted_text
            
        except Exception as e:
            self.logger.error(f"Text extraction failed for {file.name}: {str(e)}")
            if isinstance(e, (DocumentProcessingError, FileValidationError)):
                raise
            raise DocumentProcessingError(f"Failed to extract text: {str(e)}")
    
    def _extract_from_pdf(self, file) -> str:
        """Extract text from PDF file."""
        try:
            pdf_document = fitz.open(stream=file.read(), filetype="pdf")
            text_content = []
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                page_text = page.get_text()
                if page_text.strip():
                    text_content.append(page_text)
            
            pdf_document.close()
            return "\n".join(text_content)
            
        except Exception as e:
            raise DocumentProcessingError(f"PDF processing error: {str(e)}")
    
    def _extract_from_docx(self, file) -> str:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(file)
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            return "\n".join(text_content)
            
        except Exception as e:
            raise DocumentProcessingError(f"DOCX processing error: {str(e)}")
    
    def get_file_hash(self, file) -> str:
        """
        Generate hash for file content (useful for caching).
        
        Args:
            file: File object
            
        Returns:
            str: SHA256 hash of file content
        """
        try:
            current_pos = file.tell() if hasattr(file, 'tell') else 0
            file_content = file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Reset file position
            if hasattr(file, 'seek'):
                file.seek(current_pos)
            
            return file_hash
            
        except Exception as e:
            self.logger.error(f"Failed to generate file hash: {str(e)}")
            return ""