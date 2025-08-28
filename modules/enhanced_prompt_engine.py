"""
Enhanced LLM Prompt Engine
Implementation of detailed clinical prompts for extraction and recommendations
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ai_integration import MedicalAIAssistant
from exceptions import FeatureExtractionError

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Structured result from extraction prompt."""
    patient_name: str = ""
    age: str = ""
    gender: str = ""
    patient_id: str = ""
    scan_date: str = ""
    cancer_type: str = ""
    tumor_location: str = ""
    tumor_size_cm: str = ""
    suv_max: str = ""
    lymph_node_involvement: Dict[str, str] = None
    distant_metastasis: Dict[str, str] = None
    clinical_impression: str = ""
    tnm_details: str = ""
    summary: str = ""
    
    def __post_init__(self):
        if self.lymph_node_involvement is None:
            self.lymph_node_involvement = {"present": "", "description": ""}
        if self.distant_metastasis is None:
            self.distant_metastasis = {"present": "", "description": ""}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_name": self.patient_name,
            "age": self.age,
            "gender": self.gender,
            "patient_id": self.patient_id,
            "scan_date": self.scan_date,
            "cancer_type": self.cancer_type,
            "tumor_location": self.tumor_location,
            "tumor_size_cm": self.tumor_size_cm,
            "suv_max": self.suv_max,
            "lymph_node_involvement": self.lymph_node_involvement,
            "distant_metastasis": self.distant_metastasis,
            "clinical_impression": self.clinical_impression,
            "tnm_details": self.tnm_details,
            "summary": self.summary
        }


@dataclass
class ClinicalRecommendation:
    """Structured clinical recommendation result."""
    ajcc_stage: str = ""
    stage_group: str = ""
    diagnostic_recommendations: List[str] = None
    treatment_recommendations: List[str] = None
    clinical_rationale: str = ""
    
    def __post_init__(self):
        if self.diagnostic_recommendations is None:
            self.diagnostic_recommendations = []
        if self.treatment_recommendations is None:
            self.treatment_recommendations = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ajcc_stage": self.ajcc_stage,
            "stage_group": self.stage_group,
            "diagnostic_recommendations": self.diagnostic_recommendations,
            "treatment_recommendations": self.treatment_recommendations,
            "clinical_rationale": self.clinical_rationale
        }


class PETScanExtractionPrompt:
    """Advanced extraction prompt for PET scan reports."""
    
    @staticmethod
    def create_extraction_prompt(ocr_text: str) -> str:
        """
        Create comprehensive extraction prompt based on your template.
        
        Args:
            ocr_text: Raw OCR extracted text
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a medical AI assistant that extracts structured information from PET scan reports.

Given the raw text from an OCR scan of a PET report, extract the following key data points in JSON format:
- Patient Name
- Patient Age  
- Gender
- Patient ID (if available)
- Scan Date
- Cancer Type / Diagnosis
- Tumor Location
- Tumor Size (cm)
- SUVmax (Standard Uptake Value)
- Lymph Node Involvement (Yes/No + description)
- Distant Metastasis (Yes/No + description)
- Clinical Impression
- TNM Details (if present)
- Report Summary

### Raw OCR Text:
{ocr_text}

### Important Instructions:
1. Extract only information explicitly mentioned in the text
2. Use "Not specified" for missing information
3. For numeric values, extract exact numbers when available
4. For Yes/No fields, use "Yes", "No", or "Not specified"
5. Preserve medical terminology and acronyms accurately
6. If multiple values exist for same field, use the most relevant one
7. For dates, use YYYY-MM-DD format when possible

### Output format (JSON):
{{
  "patient_name": "",
  "age": "",
  "gender": "",
  "patient_id": "",
  "scan_date": "",
  "cancer_type": "",
  "tumor_location": "",
  "tumor_size_cm": "",
  "suv_max": "",
  "lymph_node_involvement": {{
    "present": "",
    "description": ""
  }},
  "distant_metastasis": {{
    "present": "",
    "description": ""
  }},
  "clinical_impression": "",
  "tnm_details": "",
  "summary": ""
}}

JSON OUTPUT:"""
        
        return prompt
    
    @staticmethod
    def parse_extraction_response(response: str) -> ExtractionResult:
        """Parse LLM response into structured ExtractionResult."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
            
            # Create ExtractionResult object
            result = ExtractionResult(
                patient_name=data.get("patient_name", ""),
                age=data.get("age", ""),
                gender=data.get("gender", ""),
                patient_id=data.get("patient_id", ""),
                scan_date=data.get("scan_date", ""),
                cancer_type=data.get("cancer_type", ""),
                tumor_location=data.get("tumor_location", ""),
                tumor_size_cm=data.get("tumor_size_cm", ""),
                suv_max=data.get("suv_max", ""),
                lymph_node_involvement=data.get("lymph_node_involvement", {}),
                distant_metastasis=data.get("distant_metastasis", {}),
                clinical_impression=data.get("clinical_impression", ""),
                tnm_details=data.get("tnm_details", ""),
                summary=data.get("summary", "")
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse extraction response: {e}")
            raise FeatureExtractionError(f"Response parsing failed: {str(e)}")


class ClinicalRecommendationPrompt:
    """Advanced clinical recommendation prompt with NCCN/AJCC integration."""
    
    @staticmethod
    def create_recommendation_prompt(patient_data: Dict[str, Any]) -> str:
        """
        Create clinical recommendation prompt based on your template.
        
        Args:
            patient_data: Structured patient data
            
        Returns:
            Formatted prompt string
        """
        # Extract data with fallbacks
        age = patient_data.get("age", "Not specified")
        gender = patient_data.get("gender", "Not specified")
        cancer_type = patient_data.get("cancer_type", "Not specified")
        tumor_size = patient_data.get("tumor_size_cm", "Not specified")
        tumor_location = patient_data.get("tumor_location", "Not specified")
        suv_max = patient_data.get("suv_max", "Not specified")
        
        # Handle complex fields
        lymph_node_data = patient_data.get("lymph_node_involvement", {})
        if isinstance(lymph_node_data, dict):
            lymph_node_desc = lymph_node_data.get("description", "Not specified")
        else:
            lymph_node_desc = str(lymph_node_data) if lymph_node_data else "Not specified"
        
        metastasis_data = patient_data.get("distant_metastasis", {})
        if isinstance(metastasis_data, dict):
            metastasis_desc = metastasis_data.get("description", "Not specified")
        else:
            metastasis_desc = str(metastasis_data) if metastasis_data else "Not specified"
        
        tnm_details = patient_data.get("tnm_details", "Not specified")
        
        prompt = f"""You are a clinical oncology assistant with access to the latest NCCN Guidelines (2025) and AJCC TNM 9th Edition.

Using the following patient cancer data, provide:
1. AJCC TNM interpretation and Stage Group
2. Recommended next steps for diagnostics or staging (based on NCCN)
3. Initial treatment options and clinical rationale

### Patient Data:
- Age: {age}
- Gender: {gender}
- Cancer Type: {cancer_type}
- Tumor Size: {tumor_size} cm
- Tumor Location: {tumor_location}
- SUVmax: {suv_max}
- Lymph Node Involvement: {lymph_node_desc}
- Distant Metastasis: {metastasis_desc}
- TNM Classification: {tnm_details}

### Clinical Guidelines to Reference:
- NCCN Clinical Practice Guidelines in Oncology (2025)
- AJCC Cancer Staging Manual, 9th Edition
- Current evidence-based treatment protocols

### Instructions:
1. Provide accurate AJCC staging interpretation
2. Recommend evidence-based diagnostic workup
3. Suggest appropriate treatment options per NCCN guidelines
4. Include clinical rationale for recommendations
5. Note any limitations due to incomplete data
6. Emphasize multidisciplinary care when appropriate

### Expected Output Format (JSON):
{{
  "ajcc_stage": "",
  "stage_group": "",
  "diagnostic_recommendations": [],
  "treatment_recommendations": [],
  "clinical_rationale": "",
  "data_limitations": "",
  "multidisciplinary_care": "",
  "follow_up_recommendations": []
}}

JSON OUTPUT:"""
        
        return prompt
    
    @staticmethod
    def parse_recommendation_response(response: str) -> ClinicalRecommendation:
        """Parse LLM response into structured ClinicalRecommendation."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
            
            # Create ClinicalRecommendation object
            result = ClinicalRecommendation(
                ajcc_stage=data.get("ajcc_stage", ""),
                stage_group=data.get("stage_group", ""),
                diagnostic_recommendations=data.get("diagnostic_recommendations", []),
                treatment_recommendations=data.get("treatment_recommendations", []),
                clinical_rationale=data.get("clinical_rationale", "")
            )
            
            # Add additional fields if present
            result.data_limitations = data.get("data_limitations", "")
            result.multidisciplinary_care = data.get("multidisciplinary_care", "")
            result.follow_up_recommendations = data.get("follow_up_recommendations", [])
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse recommendation response: {e}")
            raise FeatureExtractionError(f"Recommendation parsing failed: {str(e)}")


class EnhancedPromptEngine:
    """Main engine for advanced LLM prompting with clinical focus."""
    
    def __init__(self):
        self.ai_assistant = MedicalAIAssistant()
        self.extraction_prompt = PETScanExtractionPrompt()
        self.recommendation_prompt = ClinicalRecommendationPrompt()
    
    def extract_structured_data(self, ocr_text: str) -> ExtractionResult:
        """
        Extract structured data from OCR text using enhanced prompts.
        
        Args:
            ocr_text: Raw OCR extracted text
            
        Returns:
            ExtractionResult with structured data
        """
        try:
            # Create extraction prompt
            prompt = self.extraction_prompt.create_extraction_prompt(ocr_text)
            
            # Query DeepSeek model
            response = self.ai_assistant.client.query_model(
                prompt=prompt,
                model="deepseek-chat",
                temperature=0.1,  # Low temperature for factual extraction
                max_tokens=2048
            )
            
            # Parse response
            result = self.extraction_prompt.parse_extraction_response(response.content)
            
            logger.info("Enhanced extraction completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Enhanced extraction failed: {e}")
            raise FeatureExtractionError(f"Extraction failed: {str(e)}")
    
    def generate_clinical_recommendations(self, patient_data: Dict[str, Any]) -> ClinicalRecommendation:
        """
        Generate clinical recommendations using NCCN/AJCC guidelines.
        
        Args:
            patient_data: Structured patient data
            
        Returns:
            ClinicalRecommendation with evidence-based suggestions
        """
        try:
            # Create recommendation prompt
            prompt = self.recommendation_prompt.create_recommendation_prompt(patient_data)
            
            # Query DeepSeek model
            response = self.ai_assistant.client.query_model(
                prompt=prompt,
                model="deepseek-chat",
                temperature=0.2,  # Slightly higher for clinical reasoning
                max_tokens=2048
            )
            
            # Parse response
            result = self.recommendation_prompt.parse_recommendation_response(response.content)
            
            logger.info("Clinical recommendations generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Clinical recommendation failed: {e}")
            raise FeatureExtractionError(f"Recommendation generation failed: {str(e)}")
    
    def validate_extraction_quality(self, result: ExtractionResult) -> Dict[str, Any]:
        """
        Validate quality of extraction results.
        
        Args:
            result: ExtractionResult to validate
            
        Returns:
            Quality assessment dictionary
        """
        quality_metrics = {
            "completeness_score": 0.0,
            "critical_fields_present": 0,
            "total_fields": 0,
            "quality_level": "Unknown",
            "missing_critical_fields": [],
            "data_quality_issues": []
        }
        
        # Define critical fields for PET scan reports
        critical_fields = [
            "cancer_type", "tumor_location", "tumor_size_cm", 
            "suv_max", "tnm_details", "clinical_impression"
        ]
        
        optional_fields = [
            "patient_name", "age", "gender", "patient_id", 
            "scan_date", "summary"
        ]
        
        all_fields = critical_fields + optional_fields
        
        # Check critical fields
        critical_present = 0
        missing_critical = []
        
        for field in critical_fields:
            value = getattr(result, field, "")
            if value and value.strip() and value.lower() not in ["not specified", "not available", ""]:
                critical_present += 1
            else:
                missing_critical.append(field)
        
        # Check all fields
        total_present = 0
        for field in all_fields:
            value = getattr(result, field, "")
            if value and value.strip() and value.lower() not in ["not specified", "not available", ""]:
                total_present += 1
        
        # Calculate scores
        quality_metrics["critical_fields_present"] = critical_present
        quality_metrics["total_fields"] = total_present
        quality_metrics["missing_critical_fields"] = missing_critical
        quality_metrics["completeness_score"] = critical_present / len(critical_fields)
        
        # Determine quality level
        if quality_metrics["completeness_score"] >= 0.8:
            quality_metrics["quality_level"] = "High"
        elif quality_metrics["completeness_score"] >= 0.6:
            quality_metrics["quality_level"] = "Moderate"
        elif quality_metrics["completeness_score"] >= 0.4:
            quality_metrics["quality_level"] = "Low"
        else:
            quality_metrics["quality_level"] = "Poor"
        
        # Check for data quality issues
        issues = []
        
        # Validate SUV values
        if result.suv_max and result.suv_max.lower() not in ["not specified", ""]:
            try:
                suv_val = float(re.search(r'[\d.]+', result.suv_max).group())
                if suv_val > 50 or suv_val < 0:
                    issues.append("SUV value appears unrealistic")
            except:
                issues.append("SUV value format invalid")
        
        # Validate tumor size
        if result.tumor_size_cm and result.tumor_size_cm.lower() not in ["not specified", ""]:
            if not re.search(r'\d', result.tumor_size_cm):
                issues.append("Tumor size missing numeric value")
        
        # Validate TNM format
        if result.tnm_details and result.tnm_details.lower() not in ["not specified", ""]:
            if not re.search(r'[TtNnMm][0-9]', result.tnm_details):
                issues.append("TNM format may be incorrect")
        
        quality_metrics["data_quality_issues"] = issues
        
        return quality_metrics
    
    def generate_summary_report(self, extraction_result: ExtractionResult, 
                              clinical_recommendation: ClinicalRecommendation,
                              quality_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive summary report.
        
        Args:
            extraction_result: Structured extraction data
            clinical_recommendation: Clinical recommendations
            quality_metrics: Quality assessment
            
        Returns:
            Complete summary report
        """
        return {
            "report_metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "data_quality": quality_metrics["quality_level"],
                "completeness": f"{quality_metrics['completeness_score']:.1%}",
                "critical_fields_present": quality_metrics["critical_fields_present"],
                "extraction_method": "Enhanced DeepSeek LLM"
            },
            
            "patient_summary": {
                "demographics": {
                    "name": extraction_result.patient_name,
                    "age": extraction_result.age,
                    "gender": extraction_result.gender,
                    "patient_id": extraction_result.patient_id
                },
                "study_info": {
                    "scan_date": extraction_result.scan_date,
                    "cancer_type": extraction_result.cancer_type,
                    "tumor_location": extraction_result.tumor_location
                }
            },
            
            "imaging_findings": {
                "tumor_characteristics": {
                    "size": extraction_result.tumor_size_cm,
                    "location": extraction_result.tumor_location,
                    "suv_max": extraction_result.suv_max
                },
                "lymph_nodes": extraction_result.lymph_node_involvement,
                "metastases": extraction_result.distant_metastasis,
                "tnm_staging": extraction_result.tnm_details
            },
            
            "clinical_assessment": {
                "impression": extraction_result.clinical_impression,
                "summary": extraction_result.summary,
                "ajcc_staging": {
                    "tnm": clinical_recommendation.ajcc_stage,
                    "stage_group": clinical_recommendation.stage_group
                }
            },
            
            "recommendations": {
                "diagnostic": clinical_recommendation.diagnostic_recommendations,
                "treatment": clinical_recommendation.treatment_recommendations,
                "rationale": clinical_recommendation.clinical_rationale
            },
            
            "quality_assessment": quality_metrics,
            
            "clinical_notes": {
                "limitations": getattr(clinical_recommendation, 'data_limitations', ''),
                "multidisciplinary_care": getattr(clinical_recommendation, 'multidisciplinary_care', ''),
                "follow_up": getattr(clinical_recommendation, 'follow_up_recommendations', [])
            }
        }
