"""
Module 1: Document Upload & OCR Module
Robust OCR processing with multiple backends (Tesseract, Google Vision API)
"""

import os
import io
import logging
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import base64
import json

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import pytesseract
import fitz  # PyMuPDF

from config import ERROR_MESSAGES, MAX_FILE_SIZE_BYTES
from exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Structure for OCR processing results."""
    text: str
    confidence: float
    method: str
    processing_time: float
    page_count: int
    file_info: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "method": self.method,
            "processing_time": self.processing_time,
            "page_count": self.page_count,
            "file_info": self.file_info
        }


class ImagePreprocessor:
    """Advanced image preprocessing for better OCR accuracy."""
    
    @staticmethod
    def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
        """
        Apply advanced preprocessing techniques for medical documents.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 1. Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # 2. Contrast enhancement using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # 3. Adaptive thresholding for text extraction
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # 4. Morphological operations to clean up text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # 5. Deskewing (if needed)
        cleaned = ImagePreprocessor._deskew_image(cleaned)
        
        return cleaned
    
    @staticmethod
    def _deskew_image(image: np.ndarray) -> np.ndarray:
        """Correct skew in scanned documents."""
        try:
            # Find lines using Hough transform
            edges = cv2.Canny(image, 100, 200, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
            
            if lines is not None and len(lines) > 0:
                # Calculate average angle
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                    angles.append(angle)
                
                # Filter out extreme angles
                angles = [a for a in angles if -45 < a < 45]
                if angles:
                    median_angle = np.median(angles)
                    
                    # Only rotate if angle is significant
                    if abs(median_angle) > 0.5:
                        center = (image.shape[1] // 2, image.shape[0] // 2)
                        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                        image = cv2.warpAffine(image, rotation_matrix, (image.shape[1], image.shape[0]))
            
            return image
        except Exception as e:
            logger.warning(f"Deskewing failed: {e}")
            return image


class TesseractOCR:
    """Tesseract OCR implementation with medical document optimization."""
    
    def __init__(self):
        self.config_options = {
            'medical_default': '--psm 6 -l eng',
            'medical_sparse': '--psm 4 -l eng',
            'medical_dense': '--psm 1 -l eng',
            'medical_single_column': '--psm 4 -l eng',
            'medical_tables': '--psm 6 -l eng -c preserve_interword_spaces=1'
        }
    
    def extract_text_from_image(self, image: Image.Image, config_type: str = 'medical_default') -> Tuple[str, float]:
        """
        Extract text from image using Tesseract.
        
        Args:
            image: PIL Image object
            config_type: OCR configuration type
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            # Convert PIL to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image
            processed_image = ImagePreprocessor.preprocess_for_ocr(opencv_image)
            
            # Convert back to PIL
            pil_processed = Image.fromarray(processed_image)
            
            # Get OCR configuration
            config = self.config_options.get(config_type, self.config_options['medical_default'])
            
            # Extract text with confidence
            text = pytesseract.image_to_string(pil_processed, config=config)
            
            # Get confidence data
            confidence_data = pytesseract.image_to_data(pil_processed, config=config, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in confidence_data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return text.strip(), avg_confidence / 100.0
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            raise DocumentProcessingError(f"OCR processing failed: {str(e)}")
    
    def extract_from_pdf_pages(self, pdf_path: str) -> List[Tuple[str, float]]:
        """
        Extract text from all PDF pages using OCR.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of (text, confidence) tuples for each page
        """
        results = []
        
        try:
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                
                # Convert page to high-resolution image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(img_data))
                
                # Extract text
                text, confidence = self.extract_text_from_image(image)
                results.append((text, confidence))
            
            pdf_document.close()
            return results
            
        except Exception as e:
            logger.error(f"PDF OCR processing failed: {e}")
            raise DocumentProcessingError(f"PDF OCR failed: {str(e)}")


class GoogleVisionOCR:
    """Google Vision API OCR implementation (optional, requires API key)."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_VISION_API_KEY")
        self.available = bool(self.api_key)
    
    def extract_text_from_image(self, image: Image.Image) -> Tuple[str, float]:
        """
        Extract text using Google Vision API.
        
        Args:
            image: PIL Image object
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        if not self.available:
            raise DocumentProcessingError("Google Vision API key not available")
        
        try:
            # Convert image to base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Prepare API request
            import requests
            
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"
            
            payload = {
                "requests": [
                    {
                        "image": {"content": image_base64},
                        "features": [{"type": "TEXT_DETECTION", "maxResults": 1}]
                    }
                ]
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if 'responses' in result and result['responses']:
                text_annotations = result['responses'][0].get('textAnnotations', [])
                if text_annotations:
                    text = text_annotations[0]['description']
                    # Google Vision doesn't provide confidence per word, estimate based on response
                    confidence = 0.9  # Default high confidence for Google Vision
                    return text.strip(), confidence
            
            return "", 0.0
            
        except Exception as e:
            logger.error(f"Google Vision OCR failed: {e}")
            raise DocumentProcessingError(f"Google Vision OCR failed: {str(e)}")


class MultiModalOCR:
    """Multi-modal OCR processor combining different OCR engines."""
    
    def __init__(self):
        self.tesseract = TesseractOCR()
        self.google_vision = GoogleVisionOCR()
        
    def process_document(self, uploaded_file, ocr_method: str = "auto") -> OCRResult:
        """
        Process document with optimal OCR method.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            ocr_method: OCR method ("auto", "tesseract", "google_vision")
            
        Returns:
            OCRResult object
        """
        import time
        start_time = time.time()
        
        # File validation
        self._validate_file(uploaded_file)
        
        # Get file info
        file_info = {
            "name": uploaded_file.name,
            "size": uploaded_file.size,
            "type": uploaded_file.type
        }
        
        # Determine file type and processing method
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        try:
            if file_ext == 'pdf':
                text, confidence, method = self._process_pdf(uploaded_file, ocr_method)
                page_count = self._get_pdf_page_count(uploaded_file)
            else:
                # Image file
                image = Image.open(uploaded_file)
                text, confidence, method = self._process_image(image, ocr_method)
                page_count = 1
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=text,
                confidence=confidence,
                method=method,
                processing_time=processing_time,
                page_count=page_count,
                file_info=file_info
            )
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            raise DocumentProcessingError(f"OCR processing failed: {str(e)}")
    
    def _process_pdf(self, uploaded_file, ocr_method: str) -> Tuple[str, float, str]:
        """Process PDF file."""
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        
        try:
            # Try standard text extraction first
            uploaded_file.seek(0)
            pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            
            standard_text = ""
            for page in pdf:
                page_text = page.get_text()
                if page_text.strip():
                    standard_text += page_text + "\n"
            
            pdf.close()
            
            # If sufficient text extracted, use it
            if len(standard_text.strip()) > 100:
                return standard_text, 0.95, "standard_extraction"
            
            # Otherwise, use OCR
            if ocr_method == "google_vision" and self.google_vision.available:
                # Use Google Vision for first page only (demo)
                pdf = fitz.open(tmp_file_path)
                page = pdf.load_page(0)
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                pdf.close()
                
                text, confidence = self.google_vision.extract_text_from_image(image)
                return text, confidence, "google_vision"
            else:
                # Use Tesseract
                page_results = self.tesseract.extract_from_pdf_pages(tmp_file_path)
                texts = [result[0] for result in page_results if result[0].strip()]
                confidences = [result[1] for result in page_results if result[0].strip()]
                
                combined_text = "\n".join(texts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                return combined_text, avg_confidence, "tesseract_ocr"
        
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_file_path)
            except:
                pass
    
    def _process_image(self, image: Image.Image, ocr_method: str) -> Tuple[str, float, str]:
        """Process image file."""
        if ocr_method == "google_vision" and self.google_vision.available:
            text, confidence = self.google_vision.extract_text_from_image(image)
            return text, confidence, "google_vision"
        else:
            text, confidence = self.tesseract.extract_text_from_image(image)
            return text, confidence, "tesseract_ocr"
    
    def _get_pdf_page_count(self, uploaded_file) -> int:
        """Get PDF page count."""
        try:
            uploaded_file.seek(0)
            pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            page_count = len(pdf)
            pdf.close()
            return page_count
        except:
            return 1
    
    def _validate_file(self, uploaded_file):
        """Validate uploaded file."""
        if uploaded_file.size > MAX_FILE_SIZE_BYTES:
            raise DocumentProcessingError(
                ERROR_MESSAGES["file_too_large"].format(max_size=MAX_FILE_SIZE_BYTES/(1024*1024))
            )
        
        allowed_types = ['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp']
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        if file_ext not in allowed_types:
            raise DocumentProcessingError(f"Unsupported file type: {file_ext}")


class OCRModuleUI:
    """Streamlit UI components for OCR module."""
    
    def __init__(self):
        self.ocr_processor = MultiModalOCR()
    
    def render_upload_interface(self) -> Optional[OCRResult]:
        """Render file upload and OCR processing interface."""
        st.header("📄 Module 1: Document Upload & OCR")
        st.markdown("Upload your PET scan report for advanced text extraction.")
        
        # File upload
        col1, col2 = st.columns([3, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Choose your PET scan report",
                type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'],
                help="Supports PDF documents and image files"
            )
        
        with col2:
            ocr_method = st.selectbox(
                "OCR Method",
                ["auto", "tesseract", "google_vision"],
                help="Choose OCR processing method"
            )
            
            if ocr_method == "google_vision" and not self.ocr_processor.google_vision.available:
                st.warning("⚠️ Google Vision API key not configured")
        
        if uploaded_file is not None:
            # Display file info
            st.info(f"**File:** {uploaded_file.name} | **Size:** {uploaded_file.size:,} bytes")
            
            # Process button
            if st.button("🔍 Extract Text", type="primary"):
                with st.spinner("Processing document with advanced OCR..."):
                    try:
                        result = self.ocr_processor.process_document(uploaded_file, ocr_method)
                        
                        # Display results
                        self._display_ocr_results(result)
                        
                        return result
                        
                    except Exception as e:
                        st.error(f"❌ OCR processing failed: {str(e)}")
                        return None
        
        return None
    
    def _display_ocr_results(self, result: OCRResult):
        """Display OCR processing results."""
        st.success("✅ Text extraction completed!")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Confidence", f"{result.confidence:.1%}")
        
        with col2:
            st.metric("Processing Time", f"{result.processing_time:.2f}s")
        
        with col3:
            st.metric("Method", result.method.replace("_", " ").title())
        
        with col4:
            st.metric("Pages", result.page_count)
        
        # Text length and quality indicators
        text_length = len(result.text)
        word_count = len(result.text.split())
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Text Length", f"{text_length:,} chars")
        with col2:
            st.metric("Word Count", f"{word_count:,} words")
        
        # Quality assessment
        if result.confidence > 0.8:
            st.success("🟢 High quality extraction")
        elif result.confidence > 0.6:
            st.warning("🟡 Moderate quality extraction")
        else:
            st.error("🔴 Low quality extraction - manual review recommended")
        
        # Preview extracted text
        with st.expander("📝 Preview Extracted Text", expanded=True):
            if text_length > 5000:
                st.text_area(
                    "Extracted Text (First 5000 characters)",
                    result.text[:5000] + "...",
                    height=300
                )
                st.info(f"Full text contains {text_length:,} characters. Click 'View Full Text' below to see complete extraction.")
                
                if st.button("📄 View Full Text"):
                    st.text_area("Complete Extracted Text", result.text, height=500)
            else:
                st.text_area("Extracted Text", result.text, height=300)
        
        # Download option
        if st.button("💾 Download Extracted Text"):
            st.download_button(
                label="📥 Download TXT",
                data=result.text,
                file_name=f"extracted_text_{result.file_info['name']}.txt",
                mime="text/plain"
            )
