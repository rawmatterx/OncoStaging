"""
Module 3: Enhanced Data Verification Interface
Interactive editing with confidence scoring and validation
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import re

from modules.enhanced_prompt_engine import ExtractionResult, ClinicalRecommendation
from exceptions import MedicalDataValidationError

import logging
logger = logging.getLogger(__name__)


class DataValidator:
    """Advanced data validation for medical fields."""
    
    def __init__(self):
        self.validation_rules = self._setup_validation_rules()
    
    def _setup_validation_rules(self) -> Dict[str, Any]:
        """Setup comprehensive validation rules."""
        return {
            "age": {
                "type": "numeric",
                "min": 0,
                "max": 120,
                "format": r"^\d{1,3}$"
            },
            "gender": {
                "type": "categorical",
                "options": ["Male", "Female", "male", "female", "M", "F", "Not specified"]
            },
            "patient_id": {
                "type": "alphanumeric",
                "format": r"^[A-Za-z0-9\-_]{3,20}$"
            },
            "scan_date": {
                "type": "date",
                "formats": ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]
            },
            "cancer_types": [
                "lung", "breast", "colon", "prostate", "liver", "pancreatic",
                "gastric", "esophageal", "ovarian", "cervical", "kidney", "bladder",
                "head and neck", "melanoma", "lymphoma", "leukemia", "sarcoma",
                "adenocarcinoma", "carcinoma", "squamous cell carcinoma"
            ],
            "tumor_size": {
                "type": "measurement",
                "format": r"^\d+(\.\d+)?(\s*x\s*\d+(\.\d+)?)*\s*(cm|mm)$",
                "max_cm": 50
            },
            "suv_values": {
                "type": "numeric",
                "min": 0.0,
                "max": 50.0,
                "format": r"^\d+(\.\d+)?$"
            },
            "tnm_staging": {
                "t_stages": ["T0", "Tis", "T1", "T1a", "T1b", "T1c", "T2", "T2a", "T2b", "T3", "T4", "T4a", "T4b", "Tx"],
                "n_stages": ["N0", "N1", "N1a", "N1b", "N1c", "N2", "N2a", "N2b", "N2c", "N3", "Nx"],
                "m_stages": ["M0", "M1", "M1a", "M1b", "M1c", "Mx"],
                "overall_stages": [
                    "Stage 0", "Stage I", "Stage IA", "Stage IB", 
                    "Stage II", "Stage IIA", "Stage IIB", "Stage IIC",
                    "Stage III", "Stage IIIA", "Stage IIIB", "Stage IIIC",
                    "Stage IV", "Stage IVA", "Stage IVB", "Stage IVC"
                ]
            }
        }
    
    def validate_field(self, field_name: str, value: str) -> Tuple[bool, str, float]:
        """
        Validate individual field value.
        
        Args:
            field_name: Name of the field
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message, confidence_score)
        """
        if not value or value.strip().lower() in ["not specified", "not available", ""]:
            return True, "", 0.5  # Neutral confidence for empty values
        
        value = value.strip()
        
        # Age validation
        if field_name == "age":
            try:
                age_val = int(value)
                rules = self.validation_rules["age"]
                if rules["min"] <= age_val <= rules["max"]:
                    return True, "", 0.9
                else:
                    return False, f"Age should be between {rules['min']} and {rules['max']}", 0.3
            except ValueError:
                return False, "Age must be a number", 0.2
        
        # Gender validation
        elif field_name == "gender":
            options = self.validation_rules["gender"]["options"]
            if value in options:
                return True, "", 0.9
            else:
                return False, f"Gender should be one of: {', '.join(options[:4])}", 0.4
        
        # Patient ID validation
        elif field_name == "patient_id":
            pattern = self.validation_rules["patient_id"]["format"]
            if re.match(pattern, value):
                return True, "", 0.9
            else:
                return False, "Patient ID should be 3-20 alphanumeric characters", 0.3
        
        # Date validation
        elif field_name == "scan_date":
            for date_format in self.validation_rules["scan_date"]["formats"]:
                try:
                    datetime.strptime(value, date_format)
                    return True, "", 0.9
                except ValueError:
                    continue
            return False, "Date format should be YYYY-MM-DD, DD/MM/YYYY, or MM/DD/YYYY", 0.3
        
        # Cancer type validation
        elif field_name == "cancer_type":
            cancer_types = self.validation_rules["cancer_types"]
            value_lower = value.lower()
            
            # Exact match
            if value_lower in [ct.lower() for ct in cancer_types]:
                return True, "", 0.9
            
            # Partial match
            matches = [ct for ct in cancer_types if ct.lower() in value_lower or value_lower in ct.lower()]
            if matches:
                return True, f"Similar to: {', '.join(matches[:3])}", 0.7
            
            # Check for common patterns
            if any(term in value_lower for term in ["cancer", "carcinoma", "adenocarcinoma", "sarcoma"]):
                return True, "Contains cancer terminology", 0.6
            
            return False, "Cancer type not recognized", 0.3
        
        # Tumor size validation
        elif field_name == "tumor_size_cm":
            rules = self.validation_rules["tumor_size"]
            if re.match(rules["format"], value):
                # Extract numeric value for range check
                numbers = re.findall(r'\d+(\.\d+)?', value)
                if numbers:
                    max_size = max(float(num[0]) if num[0] else float(num) for num in numbers)
                    unit = "mm" if "mm" in value.lower() else "cm"
                    
                    if unit == "mm":
                        max_size = max_size / 10  # Convert to cm
                    
                    if max_size <= rules["max_cm"]:
                        return True, "", 0.9
                    else:
                        return False, f"Tumor size seems unusually large (>{rules['max_cm']}cm)", 0.4
            
            return False, "Tumor size format should be like '3.2 cm' or '2.1 x 1.8 cm'", 0.3
        
        # SUV validation
        elif field_name == "suv_max":
            try:
                suv_val = float(value)
                rules = self.validation_rules["suv_values"]
                if rules["min"] <= suv_val <= rules["max"]:
                    return True, "", 0.9
                else:
                    return False, f"SUV value should be between {rules['min']} and {rules['max']}", 0.3
            except ValueError:
                return False, "SUV value must be a number", 0.2
        
        # TNM staging validation
        elif field_name in ["tnm_details"]:
            # Check for TNM pattern
            tnm_pattern = r'[cCpP]?[TtNnMm][0-4][a-c]?(?:is)?'
            if re.search(tnm_pattern, value):
                return True, "", 0.8
            else:
                return False, "TNM staging format not recognized (e.g., T2N1M0)", 0.3
        
        # Default validation for text fields
        else:
            if len(value) > 1000:
                return False, "Text too long (>1000 characters)", 0.3
            elif len(value) < 2:
                return False, "Text too short", 0.4
            else:
                return True, "", 0.7


class ConfidenceScorer:
    """Calculate confidence scores for extracted data."""
    
    def __init__(self):
        self.validator = DataValidator()
    
    def calculate_field_confidence(self, field_name: str, value: str, context: str = "") -> float:
        """Calculate confidence score for a field."""
        if not value or value.strip().lower() in ["not specified", "not available", ""]:
            return 0.0
        
        # Base validation confidence
        is_valid, _, base_confidence = self.validator.validate_field(field_name, value)
        
        # Context-based adjustments
        context_bonus = self._analyze_context(field_name, value, context)
        
        # Format-based adjustments
        format_bonus = self._analyze_format(field_name, value)
        
        # Combine scores
        final_confidence = min(1.0, base_confidence + context_bonus + format_bonus)
        
        return final_confidence
    
    def _analyze_context(self, field_name: str, value: str, context: str) -> float:
        """Analyze context for confidence adjustment."""
        if not context:
            return 0.0
        
        context_lower = context.lower()
        value_lower = value.lower()
        
        # Look for supporting context
        if field_name == "cancer_type":
            if any(term in context_lower for term in ["diagnosis", "primary", "histology"]):
                return 0.1
        elif field_name == "suv_max":
            if any(term in context_lower for term in ["suv", "uptake", "fdg"]):
                return 0.1
        elif field_name == "tumor_size_cm":
            if any(term in context_lower for term in ["size", "measure", "dimension"]):
                return 0.1
        
        return 0.0
    
    def _analyze_format(self, field_name: str, value: str) -> float:
        """Analyze format quality for confidence adjustment."""
        # Specific format patterns increase confidence
        if field_name == "suv_max" and re.match(r'^\d+\.\d+$', value):
            return 0.05
        elif field_name == "tumor_size_cm" and re.search(r'\d+\.\d+', value):
            return 0.05
        elif field_name == "tnm_details" and re.search(r'T\d+N\d+M\d+', value):
            return 0.1
        
        return 0.0
    
    def calculate_overall_confidence(self, extraction_result: ExtractionResult) -> Dict[str, float]:
        """Calculate comprehensive confidence metrics."""
        field_confidences = {}
        critical_fields = ["cancer_type", "tumor_location", "tumor_size_cm", "suv_max", "tnm_details"]
        
        # Calculate individual field confidences
        for field_name in critical_fields:
            value = getattr(extraction_result, field_name, "")
            confidence = self.calculate_field_confidence(field_name, value)
            field_confidences[field_name] = confidence
        
        # Calculate aggregate metrics
        valid_confidences = [conf for conf in field_confidences.values() if conf > 0]
        
        return {
            "field_confidences": field_confidences,
            "average_confidence": sum(valid_confidences) / len(valid_confidences) if valid_confidences else 0.0,
            "critical_fields_confidence": sum(field_confidences.values()) / len(critical_fields),
            "high_confidence_fields": len([conf for conf in field_confidences.values() if conf > 0.8]),
            "low_confidence_fields": len([conf for conf in field_confidences.values() if 0 < conf < 0.5])
        }


class InteractiveEditor:
    """Interactive editor for medical data with real-time validation."""
    
    def __init__(self):
        self.validator = DataValidator()
        self.confidence_scorer = ConfidenceScorer()
    
    def render_editor_interface(self, extraction_result: ExtractionResult) -> ExtractionResult:
        """Render interactive editing interface with validation."""
        st.header("✏️ Module 3: Data Verification & Correction")
        st.markdown("Review and correct extracted information. Fields with low confidence are highlighted.")
        
        # Calculate confidence scores
        confidence_metrics = self.confidence_scorer.calculate_overall_confidence(extraction_result)
        
        # Display confidence summary
        self._display_confidence_summary(confidence_metrics)
        
        # Create editing tabs
        tabs = st.tabs([
            "👤 Patient Info",
            "🎯 Cancer Details", 
            "📏 Tumor & Imaging",
            "🔬 Clinical Findings"
        ])
        
        edited_result = ExtractionResult()
        
        with tabs[0]:
            self._edit_patient_info(extraction_result, edited_result, confidence_metrics)
        
        with tabs[1]:
            self._edit_cancer_info(extraction_result, edited_result, confidence_metrics)
        
        with tabs[2]:
            self._edit_tumor_imaging(extraction_result, edited_result, confidence_metrics)
        
        with tabs[3]:
            self._edit_clinical_findings(extraction_result, edited_result, confidence_metrics)
        
        # Validation summary
        self._display_validation_summary(edited_result)
        
        return edited_result
    
    def _display_confidence_summary(self, confidence_metrics: Dict[str, float]):
        """Display confidence score summary."""
        st.subheader("📊 Data Quality Assessment")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_conf = confidence_metrics["average_confidence"]
            st.metric("Overall Confidence", f"{avg_conf:.1%}")
        
        with col2:
            high_conf = confidence_metrics["high_confidence_fields"]
            st.metric("High Confidence Fields", high_conf)
        
        with col3:
            low_conf = confidence_metrics["low_confidence_fields"]
            st.metric("Low Confidence Fields", low_conf)
        
        with col4:
            crit_conf = confidence_metrics["critical_fields_confidence"]
            st.metric("Critical Fields Avg", f"{crit_conf:.1%}")
        
        # Quality indicator
        if avg_conf > 0.8:
            st.success("🟢 High quality extraction - minimal review needed")
        elif avg_conf > 0.6:
            st.warning("🟡 Moderate quality - please review highlighted fields")
        else:
            st.error("🔴 Low quality extraction - careful review recommended")
    
    def _edit_patient_info(self, original: ExtractionResult, edited: ExtractionResult, confidence_metrics: Dict):
        """Edit patient information with validation."""
        st.subheader("Patient Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Patient Name
            confidence = confidence_metrics["field_confidences"].get("patient_name", 0.5)
            edited.patient_name = self._render_validated_input(
                "Patient Name",
                original.patient_name,
                "patient_name",
                confidence,
                help_text="Patient's full name (optional for privacy)"
            )
            
            # Age
            confidence = confidence_metrics["field_confidences"].get("age", 0.5)
            edited.age = self._render_validated_input(
                "Age",
                original.age,
                "age",
                confidence,
                help_text="Patient age at time of scan"
            )
        
        with col2:
            # Gender
            confidence = confidence_metrics["field_confidences"].get("gender", 0.5)
            gender_options = ["Not specified", "Male", "Female", "male", "female", "M", "F"]
            edited.gender = self._render_validated_selectbox(
                "Gender",
                original.gender,
                gender_options,
                confidence,
                help_text="Patient gender"
            )
            
            # Patient ID
            confidence = confidence_metrics["field_confidences"].get("patient_id", 0.5)
            edited.patient_id = self._render_validated_input(
                "Patient ID",
                original.patient_id,
                "patient_id", 
                confidence,
                help_text="Unique patient identifier"
            )
        
        # Scan Date
        edited.scan_date = self._render_validated_input(
            "Scan Date",
            original.scan_date,
            "scan_date",
            0.5,
            help_text="Date of PET/CT scan (YYYY-MM-DD format preferred)"
        )
    
    def _edit_cancer_info(self, original: ExtractionResult, edited: ExtractionResult, confidence_metrics: Dict):
        """Edit cancer information with validation."""
        st.subheader("Cancer Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Cancer Type
            confidence = confidence_metrics["field_confidences"].get("cancer_type", 0.5)
            edited.cancer_type = self._render_validated_input(
                "Cancer Type",
                original.cancer_type,
                "cancer_type",
                confidence,
                help_text="Primary cancer diagnosis"
            )
            
            # Show cancer type suggestions
            if edited.cancer_type:
                suggestions = self._get_cancer_type_suggestions(edited.cancer_type)
                if suggestions:
                    suggested = st.selectbox(
                        "Suggested cancer types:",
                        ["Keep current input"] + suggestions,
                        key="cancer_suggestions"
                    )
                    if suggested != "Keep current input":
                        edited.cancer_type = suggested
        
        with col2:
            # Tumor Location
            confidence = confidence_metrics["field_confidences"].get("tumor_location", 0.5)
            edited.tumor_location = self._render_validated_input(
                "Tumor Location", 
                original.tumor_location,
                "tumor_location",
                confidence,
                help_text="Anatomical location of primary tumor"
            )
    
    def _edit_tumor_imaging(self, original: ExtractionResult, edited: ExtractionResult, confidence_metrics: Dict):
        """Edit tumor and imaging information."""
        st.subheader("Tumor & Imaging Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Tumor Size
            confidence = confidence_metrics["field_confidences"].get("tumor_size_cm", 0.5)
            edited.tumor_size_cm = self._render_validated_input(
                "Tumor Size",
                original.tumor_size_cm,
                "tumor_size_cm",
                confidence,
                help_text="Tumor dimensions (e.g., 3.2 cm or 2.1 x 1.8 cm)"
            )
            
            # SUV Max
            confidence = confidence_metrics["field_confidences"].get("suv_max", 0.5)
            edited.suv_max = self._render_validated_input(
                "SUV Max",
                original.suv_max,
                "suv_max",
                confidence,
                help_text="Maximum Standard Uptake Value"
            )
        
        with col2:
            # TNM Details
            confidence = confidence_metrics["field_confidences"].get("tnm_details", 0.5)
            edited.tnm_details = self._render_validated_input(
                "TNM Staging",
                original.tnm_details,
                "tnm_details",
                confidence,
                help_text="TNM classification (e.g., T2N1M0)"
            )
    
    def _edit_clinical_findings(self, original: ExtractionResult, edited: ExtractionResult, confidence_metrics: Dict):
        """Edit clinical findings."""
        st.subheader("Clinical Findings")
        
        # Lymph Node Involvement
        st.write("**Lymph Node Involvement**")
        col1, col2 = st.columns(2)
        
        with col1:
            ln_present = st.selectbox(
                "Lymph nodes involved?",
                ["Not specified", "Yes", "No"],
                index=self._get_selectbox_index(
                    original.lymph_node_involvement.get("present", ""), 
                    ["Not specified", "Yes", "No"]
                )
            )
        
        with col2:
            ln_description = st.text_area(
                "Description",
                value=original.lymph_node_involvement.get("description", ""),
                help="Describe lymph node involvement"
            )
        
        edited.lymph_node_involvement = {
            "present": ln_present,
            "description": ln_description
        }
        
        # Distant Metastasis
        st.write("**Distant Metastasis**")
        col1, col2 = st.columns(2)
        
        with col1:
            met_present = st.selectbox(
                "Distant metastasis present?",
                ["Not specified", "Yes", "No"],
                index=self._get_selectbox_index(
                    original.distant_metastasis.get("present", ""),
                    ["Not specified", "Yes", "No"]
                )
            )
        
        with col2:
            met_description = st.text_area(
                "Metastasis description",
                value=original.distant_metastasis.get("description", ""),
                help="Describe metastatic sites and findings"
            )
        
        edited.distant_metastasis = {
            "present": met_present,
            "description": met_description
        }
        
        # Clinical Impression
        edited.clinical_impression = st.text_area(
            "Clinical Impression",
            value=original.clinical_impression,
            height=100,
            help="Primary clinical impression or conclusion"
        )
        
        # Summary
        edited.summary = st.text_area(
            "Report Summary",
            value=original.summary,
            height=80,
            help="Brief summary of key findings"
        )
    
    def _render_validated_input(self, label: str, value: str, field_name: str, 
                               confidence: float, help_text: str = "") -> str:
        """Render input field with validation and confidence indicator."""
        
        # Color coding based on confidence
        if confidence > 0.8:
            label_suffix = " 🟢"
        elif confidence > 0.5:
            label_suffix = " 🟡"
        elif confidence > 0:
            label_suffix = " 🔴"
        else:
            label_suffix = " ⚪"
        
        # Render input
        new_value = st.text_input(
            f"{label}{label_suffix}",
            value=value,
            help=f"{help_text} (Confidence: {confidence:.1%})",
            key=f"input_{field_name}"
        )
        
        # Real-time validation
        if new_value:
            is_valid, error_msg, _ = self.validator.validate_field(field_name, new_value)
            if not is_valid:
                st.error(f"⚠️ {error_msg}")
        
        return new_value
    
    def _render_validated_selectbox(self, label: str, value: str, options: List[str],
                                   confidence: float, help_text: str = "") -> str:
        """Render selectbox with validation."""
        
        # Color coding
        if confidence > 0.8:
            label_suffix = " 🟢"
        elif confidence > 0.5:
            label_suffix = " 🟡"
        else:
            label_suffix = " 🔴"
        
        index = self._get_selectbox_index(value, options)
        
        return st.selectbox(
            f"{label}{label_suffix}",
            options=options,
            index=index,
            help=f"{help_text} (Confidence: {confidence:.1%})"
        )
    
    def _get_selectbox_index(self, value: str, options: List[str]) -> int:
        """Get index for selectbox."""
        try:
            return options.index(value) if value in options else 0
        except:
            return 0
    
    def _get_cancer_type_suggestions(self, input_value: str) -> List[str]:
        """Get cancer type suggestions."""
        cancer_types = self.validator.validation_rules["cancer_types"]
        input_lower = input_value.lower()
        
        suggestions = []
        for cancer_type in cancer_types:
            if input_lower in cancer_type.lower() or cancer_type.lower() in input_lower:
                suggestions.append(cancer_type)
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _display_validation_summary(self, edited_result: ExtractionResult):
        """Display final validation summary."""
        st.subheader("✅ Validation Summary")
        
        # Validate all fields
        validation_results = {}
        critical_fields = ["cancer_type", "tumor_location", "tumor_size_cm", "suv_max", "tnm_details"]
        
        for field in critical_fields:
            value = getattr(edited_result, field, "")
            is_valid, error_msg, confidence = self.validator.validate_field(field, value)
            validation_results[field] = {
                "valid": is_valid,
                "error": error_msg,
                "confidence": confidence,
                "has_value": bool(value and value.strip())
            }
        
        # Summary metrics
        valid_count = sum(1 for r in validation_results.values() if r["valid"])
        has_value_count = sum(1 for r in validation_results.values() if r["has_value"])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Valid Fields", f"{valid_count}/{len(critical_fields)}")
        
        with col2:
            st.metric("Fields with Data", f"{has_value_count}/{len(critical_fields)}")
        
        with col3:
            if valid_count == len(critical_fields):
                st.success("✅ All validations passed")
            else:
                st.warning(f"⚠️ {len(critical_fields) - valid_count} validation issues")
        
        # Show validation issues
        issues = [f"{field}: {r['error']}" for field, r in validation_results.items() if not r["valid"] and r["error"]]
        if issues:
            st.error("**Validation Issues:**")
            for issue in issues:
                st.write(f"• {issue}")


class VerificationModuleUI:
    """Main UI component for verification module."""
    
    def __init__(self):
        self.editor = InteractiveEditor()
    
    def render_verification_interface(self, extraction_result: ExtractionResult) -> Optional[ExtractionResult]:
        """Render complete verification interface."""
        if not extraction_result:
            st.warning("⚠️ No extraction data available. Please complete extraction first.")
            return None
        
        # Render editor
        edited_result = self.editor.render_editor_interface(extraction_result)
        
        # Save and export options
        st.subheader("💾 Save & Export")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Confirm Data", type="primary"):
                st.success("Data confirmed and ready for clinical analysis!")
                return edited_result
        
        with col2:
            if st.button("📄 Export JSON"):
                json_data = json.dumps(edited_result.to_dict(), indent=2, default=str)
                st.download_button(
                    "Download JSON",
                    data=json_data,
                    file_name=f"verified_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col3:
            if st.button("🔄 Reset to Original"):
                st.info("Reset to original extraction data")
                return extraction_result
        
        return edited_result
