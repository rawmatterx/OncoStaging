"""
Advanced Document Processing module for OncoStaging application.
Implements OCR, NER, and LLM-based extraction with interactive editing.
"""

import os
import logging
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import base64
from pathlib import Path
import re

import streamlit as st
import fitz  # PyMuPDF
import docx
from PIL import Image
import pytesseract
import cv2
import numpy as np

from config import ERROR_MESSAGES, SUCCESS_MESSAGES
from exceptions import DocumentProcessingError, FeatureExtractionError
from ai_integration import MedicalAIAssistant

logger = logging.getLogger(__name__)


@dataclass
class ExtractedMedicalData:
    """Structured medical data extracted from reports."""
    
    # Patient Information
    patient_id: str = ""
    patient_name: str = ""
    age: str = ""
    gender: str = ""
    
    # Study Information
    study_date: str = ""
    study_type: str = ""
    modality: str = ""
    referring_physician: str = ""
    
    # Cancer Information
    cancer_type: str = ""
    primary_site: str = ""
    histology: str = ""
    
    # Tumor Characteristics
    tumor_size: str = ""
    tumor_location: str = ""
    tumor_description: str = ""
    
    # TNM Components
    t_stage: str = ""
    n_stage: str = ""
    m_stage: str = ""
    overall_stage: str = ""
    
    # PET/CT Specific
    suv_max: str = ""
    suv_peak: str = ""
    metabolic_tumor_volume: str = ""
    total_lesion_glycolysis: str = ""
    
    # Lymph Nodes
    lymph_nodes_involved: str = ""
    lymph_node_stations: List[str] = None
    
    # Metastases
    distant_metastases: List[str] = None
    metastatic_sites: List[str] = None
    
    # Additional Findings
    additional_findings: List[str] = None
    recommendations: List[str] = None
    
    # Confidence Scores
    extraction_confidence: Dict[str, float] = None
    
    # Raw Text Sections
    impression: str = ""
    findings: str = ""
    comparison: str = ""
    technique: str = ""
    
    def __post_init__(self):
        if self.lymph_node_stations is None:
            self.lymph_node_stations = []
        if self.distant_metastases is None:
            self.distant_metastases = []
        if self.metastatic_sites is None:
            self.metastatic_sites = []
        if self.additional_findings is None:
            self.additional_findings = []
        if self.recommendations is None:
            self.recommendations = []
        if self.extraction_confidence is None:
            self.extraction_confidence = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of key extracted data."""
        return {
            "patient": {
                "id": self.patient_id,
                "age": self.age,
                "gender": self.gender
            },
            "study": {
                "date": self.study_date,
                "type": self.study_type,
                "modality": self.modality
            },
            "cancer": {
                "type": self.cancer_type,
                "primary_site": self.primary_site,
                "histology": self.histology
            },
            "staging": {
                "T": self.t_stage,
                "N": self.n_stage,
                "M": self.m_stage,
                "overall": self.overall_stage
            },
            "tumor": {
                "size": self.tumor_size,
                "location": self.tumor_location,
                "suv_max": self.suv_max
            }
        }


class AdvancedOCRProcessor:
    """Advanced OCR processing with image preprocessing."""
    
    def __init__(self):
        self.tesseract_config = '--psm 6 -l eng'
        
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR accuracy."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from image using OCR."""
        try:
            # Convert PIL to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image
            processed_image = self.preprocess_image(opencv_image)
            
            # Convert back to PIL
            pil_image = Image.fromarray(processed_image)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(pil_image, config=self.tesseract_config)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            raise DocumentProcessingError(f"OCR failed: {str(e)}")
    
    def extract_from_pdf_images(self, pdf_path: str) -> List[str]:
        """Extract text from PDF pages using OCR."""
        extracted_texts = []
        
        try:
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                
                # Convert page to image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(img_data))
                
                # Extract text using OCR
                text = self.extract_text_from_image(image)
                if text.strip():
                    extracted_texts.append(text)
            
            pdf_document.close()
            return extracted_texts
            
        except Exception as e:
            logger.error(f"PDF OCR processing error: {e}")
            raise DocumentProcessingError(f"PDF OCR failed: {str(e)}")


class MedicalNERProcessor:
    """Medical Named Entity Recognition using LLM."""
    
    def __init__(self, ai_assistant: MedicalAIAssistant):
        self.ai_assistant = ai_assistant
    
    def create_ner_prompt(self, text: str) -> str:
        """Create prompt for medical NER extraction."""
        prompt = f"""You are a medical information extraction specialist. Extract structured data from the following PET/CT scan report.

REPORT TEXT:
{text}

Extract the following information and return in JSON format:

{{
    "patient_info": {{
        "patient_id": "extracted patient ID",
        "patient_name": "extracted patient name",
        "age": "extracted age",
        "gender": "extracted gender"
    }},
    "study_info": {{
        "study_date": "extracted study date",
        "study_type": "PET/CT, PET, CT, etc.",
        "modality": "imaging modality details",
        "referring_physician": "referring doctor name"
    }},
    "cancer_info": {{
        "cancer_type": "primary cancer type",
        "primary_site": "primary tumor location",
        "histology": "histological type if mentioned"
    }},
    "tumor_characteristics": {{
        "tumor_size": "tumor dimensions",
        "tumor_location": "anatomical location",
        "tumor_description": "detailed description",
        "suv_max": "maximum SUV value",
        "suv_peak": "peak SUV value",
        "metabolic_tumor_volume": "MTV value",
        "total_lesion_glycolysis": "TLG value"
    }},
    "tnm_staging": {{
        "t_stage": "T stage classification",
        "n_stage": "N stage classification", 
        "m_stage": "M stage classification",
        "overall_stage": "overall stage if mentioned"
    }},
    "lymph_nodes": {{
        "nodes_involved": "number or description of involved nodes",
        "node_stations": ["list", "of", "involved", "stations"]
    }},
    "metastases": {{
        "distant_metastases": ["list", "of", "distant", "metastases"],
        "metastatic_sites": ["list", "of", "sites"]
    }},
    "report_sections": {{
        "impression": "impression/conclusion section",
        "findings": "findings section",
        "comparison": "comparison section",
        "technique": "technique section"
    }},
    "additional": {{
        "findings": ["other", "significant", "findings"],
        "recommendations": ["recommended", "follow-up", "actions"]
    }},
    "confidence": {{
        "overall_confidence": 0.95,
        "field_confidence": {{
            "cancer_type": 0.9,
            "tnm_staging": 0.8,
            "tumor_size": 0.95
        }}
    }}
}}

INSTRUCTIONS:
1. Extract only information explicitly mentioned in the report
2. Use "Not specified" for missing information
3. Maintain medical terminology accuracy
4. Provide confidence scores (0.0-1.0) for extractions
5. Be conservative with staging information - only extract if clearly stated
6. Focus on oncological and imaging-relevant data"""
        
        return prompt
    
    def extract_medical_entities(self, text: str) -> ExtractedMedicalData:
        """Extract medical entities using DeepSeek LLM."""
        try:
            # Create NER prompt
            prompt = self.create_ner_prompt(text)
            
            # Query DeepSeek model
            response = self.ai_assistant.client.query_model(
                prompt=prompt,
                model="deepseek-chat",
                temperature=0.1,  # Low temperature for factual extraction
                max_tokens=2048
            )
            
            # Parse JSON response
            try:
                extracted_data = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from response
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    raise FeatureExtractionError("Failed to parse NER response")
            
            # Convert to ExtractedMedicalData
            medical_data = self._convert_to_medical_data(extracted_data)
            
            logger.info("Medical NER extraction completed successfully")
            return medical_data
            
        except Exception as e:
            logger.error(f"NER extraction error: {e}")
            raise FeatureExtractionError(f"Medical NER failed: {str(e)}")
    
    def _convert_to_medical_data(self, extracted_data: Dict) -> ExtractedMedicalData:
        """Convert extracted JSON data to ExtractedMedicalData object."""
        data = ExtractedMedicalData()
        
        # Patient information
        if "patient_info" in extracted_data:
            patient = extracted_data["patient_info"]
            data.patient_id = patient.get("patient_id", "")
            data.patient_name = patient.get("patient_name", "")
            data.age = patient.get("age", "")
            data.gender = patient.get("gender", "")
        
        # Study information
        if "study_info" in extracted_data:
            study = extracted_data["study_info"]
            data.study_date = study.get("study_date", "")
            data.study_type = study.get("study_type", "")
            data.modality = study.get("modality", "")
            data.referring_physician = study.get("referring_physician", "")
        
        # Cancer information
        if "cancer_info" in extracted_data:
            cancer = extracted_data["cancer_info"]
            data.cancer_type = cancer.get("cancer_type", "")
            data.primary_site = cancer.get("primary_site", "")
            data.histology = cancer.get("histology", "")
        
        # Tumor characteristics
        if "tumor_characteristics" in extracted_data:
            tumor = extracted_data["tumor_characteristics"]
            data.tumor_size = tumor.get("tumor_size", "")
            data.tumor_location = tumor.get("tumor_location", "")
            data.tumor_description = tumor.get("tumor_description", "")
            data.suv_max = tumor.get("suv_max", "")
            data.suv_peak = tumor.get("suv_peak", "")
            data.metabolic_tumor_volume = tumor.get("metabolic_tumor_volume", "")
            data.total_lesion_glycolysis = tumor.get("total_lesion_glycolysis", "")
        
        # TNM staging
        if "tnm_staging" in extracted_data:
            tnm = extracted_data["tnm_staging"]
            data.t_stage = tnm.get("t_stage", "")
            data.n_stage = tnm.get("n_stage", "")
            data.m_stage = tnm.get("m_stage", "")
            data.overall_stage = tnm.get("overall_stage", "")
        
        # Lymph nodes
        if "lymph_nodes" in extracted_data:
            nodes = extracted_data["lymph_nodes"]
            data.lymph_nodes_involved = nodes.get("nodes_involved", "")
            data.lymph_node_stations = nodes.get("node_stations", [])
        
        # Metastases
        if "metastases" in extracted_data:
            mets = extracted_data["metastases"]
            data.distant_metastases = mets.get("distant_metastases", [])
            data.metastatic_sites = mets.get("metastatic_sites", [])
        
        # Report sections
        if "report_sections" in extracted_data:
            sections = extracted_data["report_sections"]
            data.impression = sections.get("impression", "")
            data.findings = sections.get("findings", "")
            data.comparison = sections.get("comparison", "")
            data.technique = sections.get("technique", "")
        
        # Additional findings
        if "additional" in extracted_data:
            additional = extracted_data["additional"]
            data.additional_findings = additional.get("findings", [])
            data.recommendations = additional.get("recommendations", [])
        
        # Confidence scores
        if "confidence" in extracted_data:
            confidence = extracted_data["confidence"]
            data.extraction_confidence = confidence.get("field_confidence", {})
            data.extraction_confidence["overall"] = confidence.get("overall_confidence", 0.8)
        
        return data


class AdvancedDocumentProcessor:
    """Advanced document processor combining OCR, text extraction, and NER."""
    
    def __init__(self):
        self.ocr_processor = AdvancedOCRProcessor()
        self.ai_assistant = MedicalAIAssistant()
        self.ner_processor = MedicalNERProcessor(self.ai_assistant)
    
    def process_document_advanced(self, uploaded_file) -> Dict[str, Any]:
        """
        Advanced document processing with OCR and NER.
        
        Phase 1: Document Processing & Data Extraction
        """
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name
            
            # Reset file pointer for other operations
            uploaded_file.seek(0)
            
            # Step 1: Extract raw text
            raw_text = self._extract_text_combined(uploaded_file, tmp_file_path)
            
            # Step 2: Apply NER for structured extraction
            extracted_data = self.ner_processor.extract_medical_entities(raw_text)
            
            # Step 3: Validate and enhance extraction
            validated_data = self._validate_extraction(extracted_data, raw_text)
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
            return {
                "success": True,
                "raw_text": raw_text,
                "extracted_data": validated_data,
                "processing_method": "advanced_ocr_ner",
                "text_length": len(raw_text),
                "extraction_quality": self._assess_extraction_quality(validated_data)
            }
            
        except Exception as e:
            logger.error(f"Advanced document processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_method": "advanced_ocr_ner"
            }
    
    def _extract_text_combined(self, uploaded_file, tmp_file_path: str) -> str:
        """Extract text using both standard and OCR methods."""
        texts = []
        
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        # Method 1: Standard text extraction
        try:
            if file_ext == 'pdf':
                pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                for page in pdf:
                    page_text = page.get_text()
                    if page_text.strip():
                        texts.append(page_text)
                pdf.close()
            elif file_ext == 'docx':
                uploaded_file.seek(0)
                doc = docx.Document(uploaded_file)
                for para in doc.paragraphs:
                    if para.text.strip():
                        texts.append(para.text)
        except Exception as e:
            logger.warning(f"Standard text extraction failed: {e}")
        
        # Method 2: OCR extraction (if standard method yields little text)
        combined_text = "\n".join(texts)
        if len(combined_text.strip()) < 500:  # If too little text, try OCR
            try:
                logger.info("Attempting OCR extraction due to limited standard text")
                if file_ext == 'pdf':
                    ocr_texts = self.ocr_processor.extract_from_pdf_images(tmp_file_path)
                    texts.extend(ocr_texts)
            except Exception as e:
                logger.warning(f"OCR extraction failed: {e}")
        
        final_text = "\n".join(texts)
        if not final_text.strip():
            raise DocumentProcessingError("No text could be extracted from the document")
        
        return final_text
    
    def _validate_extraction(self, extracted_data: ExtractedMedicalData, raw_text: str) -> ExtractedMedicalData:
        """Validate and enhance extraction results."""
        # Basic validation rules
        if not extracted_data.cancer_type and not extracted_data.primary_site:
            # Try to extract basic cancer information using regex
            cancer_patterns = [
                r'(?i)(lung|breast|colon|prostate|liver|pancreatic|gastric|esophageal|ovarian|cervical)\s+(?:cancer|carcinoma|adenocarcinoma)',
                r'(?i)(adenocarcinoma|carcinoma|sarcoma|lymphoma|melanoma)',
                r'(?i)primary\s+(?:site|tumor|cancer):\s*([^\n]+)',
            ]
            
            for pattern in cancer_patterns:
                match = re.search(pattern, raw_text)
                if match:
                    if not extracted_data.cancer_type:
                        extracted_data.cancer_type = match.group(1) if match.group(1) else match.group(0)
                    break
        
        # Validate numeric values
        if extracted_data.suv_max:
            try:
                float_val = float(re.search(r'[\d.]+', extracted_data.suv_max).group())
                if float_val > 50:  # Unrealistic SUV value
                    extracted_data.extraction_confidence["suv_max"] = 0.3
            except:
                pass
        
        return extracted_data
    
    def _assess_extraction_quality(self, extracted_data: ExtractedMedicalData) -> Dict[str, Any]:
        """Assess quality of extraction results."""
        quality_metrics = {
            "completeness": 0.0,
            "confidence": 0.0,
            "critical_fields_found": 0,
            "total_fields_extracted": 0
        }
        
        # Critical fields for cancer staging
        critical_fields = [
            "cancer_type", "primary_site", "tumor_size", 
            "t_stage", "n_stage", "m_stage", "suv_max"
        ]
        
        fields_found = 0
        total_extracted = 0
        
        for field in critical_fields:
            value = getattr(extracted_data, field, "")
            if value and value != "Not specified":
                fields_found += 1
            
        # Count all non-empty fields
        for field, value in extracted_data.to_dict().items():
            if value and value != "Not specified" and value != [] and value != {}:
                total_extracted += 1
        
        quality_metrics["critical_fields_found"] = fields_found
        quality_metrics["total_fields_extracted"] = total_extracted
        quality_metrics["completeness"] = fields_found / len(critical_fields)
        
        # Average confidence
        if extracted_data.extraction_confidence:
            confidences = [v for v in extracted_data.extraction_confidence.values() if isinstance(v, (int, float))]
            quality_metrics["confidence"] = sum(confidences) / len(confidences) if confidences else 0.5
        
        return quality_metrics
