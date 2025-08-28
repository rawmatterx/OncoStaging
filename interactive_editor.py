"""
Interactive Editor for extracted medical data.
Allows users to review, edit, and correct OCR/NER extraction results.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from advanced_document_processor import ExtractedMedicalData


class MedicalDataEditor:
    """Interactive editor for medical data with validation."""
    
    def __init__(self):
        self.validation_rules = self._setup_validation_rules()
    
    def _setup_validation_rules(self) -> Dict[str, Any]:
        """Setup validation rules for medical fields."""
        return {
            "cancer_types": [
                "lung", "breast", "colon", "prostate", "liver", "pancreatic",
                "gastric", "esophageal", "ovarian", "cervical", "head and neck",
                "kidney", "bladder", "melanoma", "lymphoma", "leukemia"
            ],
            "tnm_t_stages": ["T0", "Tis", "T1", "T1a", "T1b", "T2", "T3", "T4", "T4a", "T4b", "Tx"],
            "tnm_n_stages": ["N0", "N1", "N1a", "N1b", "N2", "N2a", "N2b", "N3", "Nx"],
            "tnm_m_stages": ["M0", "M1", "M1a", "M1b", "Mx"],
            "overall_stages": ["Stage 0", "Stage I", "Stage IA", "Stage IB", "Stage II", 
                             "Stage IIA", "Stage IIB", "Stage III", "Stage IIIA", 
                             "Stage IIIB", "Stage IIIC", "Stage IV", "Stage IVA", "Stage IVB"],
            "genders": ["Male", "Female", "Other", "Not specified"],
            "study_types": ["PET/CT", "PET", "CT", "MRI", "Combined"],
            "suv_range": {"min": 0.0, "max": 50.0}
        }
    
    def render_editor_interface(self, extracted_data: ExtractedMedicalData) -> ExtractedMedicalData:
        """Render interactive editing interface."""
        st.header("📝 Review and Edit Extracted Data")
        st.markdown("Please review the extracted information and make corrections as needed.")
        
        # Create tabs for different data categories
        tabs = st.tabs([
            "👤 Patient Info", 
            "🏥 Study Details", 
            "🎯 Cancer Info", 
            "📏 Tumor Details",
            "🔬 TNM Staging",
            "🩺 Clinical Findings",
            "📊 Report Sections"
        ])
        
        edited_data = ExtractedMedicalData()
        
        # Tab 1: Patient Information
        with tabs[0]:
            edited_data = self._edit_patient_info(extracted_data, edited_data)
        
        # Tab 2: Study Details
        with tabs[1]:
            edited_data = self._edit_study_info(extracted_data, edited_data)
        
        # Tab 3: Cancer Information
        with tabs[2]:
            edited_data = self._edit_cancer_info(extracted_data, edited_data)
        
        # Tab 4: Tumor Details
        with tabs[3]:
            edited_data = self._edit_tumor_details(extracted_data, edited_data)
        
        # Tab 5: TNM Staging
        with tabs[4]:
            edited_data = self._edit_tnm_staging(extracted_data, edited_data)
        
        # Tab 6: Clinical Findings
        with tabs[5]:
            edited_data = self._edit_clinical_findings(extracted_data, edited_data)
        
        # Tab 7: Report Sections
        with tabs[6]:
            edited_data = self._edit_report_sections(extracted_data, edited_data)
        
        # Validation summary
        self._display_validation_summary(edited_data)
        
        return edited_data
    
    def _edit_patient_info(self, original: ExtractedMedicalData, edited: ExtractedMedicalData) -> ExtractedMedicalData:
        """Edit patient information section."""
        st.subheader("Patient Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            edited.patient_id = st.text_input(
                "Patient ID",
                value=original.patient_id,
                help="Unique patient identifier"
            )
            
            edited.patient_name = st.text_input(
                "Patient Name",
                value=original.patient_name,
                help="Patient's full name (optional for privacy)"
            )
        
        with col2:
            edited.age = st.text_input(
                "Age",
                value=original.age,
                help="Patient age at time of study"
            )
            
            edited.gender = st.selectbox(
                "Gender",
                options=self.validation_rules["genders"],
                index=self._get_selectbox_index(original.gender, self.validation_rules["genders"]),
                help="Patient gender"
            )
        
        return edited
    
    def _edit_study_info(self, original: ExtractedMedicalData, edited: ExtractedMedicalData) -> ExtractedMedicalData:
        """Edit study information section."""
        st.subheader("Study Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            edited.study_date = st.date_input(
                "Study Date",
                value=self._parse_date(original.study_date),
                help="Date when the study was performed"
            ).strftime("%Y-%m-%d") if st.date_input("Study Date", value=self._parse_date(original.study_date)) else ""
            
            edited.study_type = st.selectbox(
                "Study Type",
                options=self.validation_rules["study_types"],
                index=self._get_selectbox_index(original.study_type, self.validation_rules["study_types"]),
                help="Type of imaging study"
            )
        
        with col2:
            edited.modality = st.text_input(
                "Imaging Modality",
                value=original.modality,
                help="Specific imaging modality details"
            )
            
            edited.referring_physician = st.text_input(
                "Referring Physician",
                value=original.referring_physician,
                help="Name of referring doctor"
            )
        
        return edited
    
    def _edit_cancer_info(self, original: ExtractedMedicalData, edited: ExtractedMedicalData) -> ExtractedMedicalData:
        """Edit cancer information section."""
        st.subheader("Cancer Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Cancer type with autocomplete
            cancer_type_input = st.text_input(
                "Cancer Type",
                value=original.cancer_type,
                help="Primary cancer type"
            )
            
            # Show suggestions
            if cancer_type_input:
                suggestions = [ct for ct in self.validation_rules["cancer_types"] 
                             if cancer_type_input.lower() in ct.lower()]
                if suggestions:
                    suggested = st.selectbox(
                        "Suggested cancer types:",
                        options=["Keep current input"] + suggestions,
                        key="cancer_type_suggestions"
                    )
                    if suggested != "Keep current input":
                        cancer_type_input = suggested
            
            edited.cancer_type = cancer_type_input
            
            edited.primary_site = st.text_input(
                "Primary Site",
                value=original.primary_site,
                help="Anatomical location of primary tumor"
            )
        
        with col2:
            edited.histology = st.text_area(
                "Histology",
                value=original.histology,
                height=100,
                help="Histological type and characteristics"
            )
        
        return edited
    
    def _edit_tumor_details(self, original: ExtractedMedicalData, edited: ExtractedMedicalData) -> ExtractedMedicalData:
        """Edit tumor details section."""
        st.subheader("Tumor Characteristics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            edited.tumor_size = st.text_input(
                "Tumor Size",
                value=original.tumor_size,
                help="Tumor dimensions (e.g., 3.2 x 2.1 cm)"
            )
            
            edited.tumor_location = st.text_input(
                "Tumor Location",
                value=original.tumor_location,
                help="Specific anatomical location"
            )
            
            edited.suv_max = st.text_input(
                "SUV Max",
                value=original.suv_max,
                help="Maximum Standard Uptake Value"
            )
            
            # Validate SUV Max
            if edited.suv_max:
                try:
                    suv_val = float(edited.suv_max.replace(',', '.'))
                    if not (self.validation_rules["suv_range"]["min"] <= suv_val <= self.validation_rules["suv_range"]["max"]):
                        st.warning(f"SUV Max value seems unusually high/low. Normal range: {self.validation_rules['suv_range']['min']}-{self.validation_rules['suv_range']['max']}")
                except ValueError:
                    st.warning("SUV Max should be a numeric value")
        
        with col2:
            edited.suv_peak = st.text_input(
                "SUV Peak",
                value=original.suv_peak,
                help="Peak Standard Uptake Value"
            )
            
            edited.metabolic_tumor_volume = st.text_input(
                "Metabolic Tumor Volume (MTV)",
                value=original.metabolic_tumor_volume,
                help="Metabolic tumor volume"
            )
            
            edited.total_lesion_glycolysis = st.text_input(
                "Total Lesion Glycolysis (TLG)",
                value=original.total_lesion_glycolysis,
                help="Total lesion glycolysis"
            )
        
        edited.tumor_description = st.text_area(
            "Tumor Description",
            value=original.tumor_description,
            height=80,
            help="Detailed tumor characteristics"
        )
        
        return edited
    
    def _edit_tnm_staging(self, original: ExtractedMedicalData, edited: ExtractedMedicalData) -> ExtractedMedicalData:
        """Edit TNM staging section."""
        st.subheader("TNM Staging")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            edited.t_stage = st.selectbox(
                "T Stage",
                options=[""] + self.validation_rules["tnm_t_stages"],
                index=self._get_selectbox_index(original.t_stage, [""] + self.validation_rules["tnm_t_stages"]),
                help="Primary tumor classification"
            )
        
        with col2:
            edited.n_stage = st.selectbox(
                "N Stage",
                options=[""] + self.validation_rules["tnm_n_stages"],
                index=self._get_selectbox_index(original.n_stage, [""] + self.validation_rules["tnm_n_stages"]),
                help="Regional lymph node classification"
            )
        
        with col3:
            edited.m_stage = st.selectbox(
                "M Stage",
                options=[""] + self.validation_rules["tnm_m_stages"],
                index=self._get_selectbox_index(original.m_stage, [""] + self.validation_rules["tnm_m_stages"]),
                help="Distant metastasis classification"
            )
        
        with col4:
            edited.overall_stage = st.selectbox(
                "Overall Stage",
                options=[""] + self.validation_rules["overall_stages"],
                index=self._get_selectbox_index(original.overall_stage, [""] + self.validation_rules["overall_stages"]),
                help="Overall cancer stage"
            )
        
        # TNM staging validation
        if edited.t_stage and edited.n_stage and edited.m_stage:
            if not edited.overall_stage:
                st.info("💡 Consider adding the overall stage based on TNM classification")
        
        return edited
    
    def _edit_clinical_findings(self, original: ExtractedMedicalData, edited: ExtractedMedicalData) -> ExtractedMedicalData:
        """Edit clinical findings section."""
        st.subheader("Clinical Findings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            edited.lymph_nodes_involved = st.text_input(
                "Lymph Nodes Involved",
                value=original.lymph_nodes_involved,
                help="Number or description of involved lymph nodes"
            )
            
            # Lymph node stations (editable list)
            st.write("Lymph Node Stations:")
            edited.lymph_node_stations = self._edit_string_list(
                original.lymph_node_stations, 
                "lymph_node_stations",
                placeholder="e.g., 2R, 4L, 7"
            )
        
        with col2:
            # Metastatic sites (editable list)
            st.write("Metastatic Sites:")
            edited.metastatic_sites = self._edit_string_list(
                original.metastatic_sites,
                "metastatic_sites", 
                placeholder="e.g., liver, bone, brain"
            )
            
            # Distant metastases (editable list)
            st.write("Distant Metastases:")
            edited.distant_metastases = self._edit_string_list(
                original.distant_metastases,
                "distant_metastases",
                placeholder="e.g., hepatic metastases"
            )
        
        # Additional findings
        st.write("Additional Findings:")
        edited.additional_findings = self._edit_string_list(
            original.additional_findings,
            "additional_findings",
            placeholder="e.g., pleural effusion, ascites"
        )
        
        # Recommendations
        st.write("Recommendations:")
        edited.recommendations = self._edit_string_list(
            original.recommendations,
            "recommendations",
            placeholder="e.g., follow-up scan in 3 months"
        )
        
        return edited
    
    def _edit_report_sections(self, original: ExtractedMedicalData, edited: ExtractedMedicalData) -> ExtractedMedicalData:
        """Edit report sections."""
        st.subheader("Report Sections")
        
        edited.impression = st.text_area(
            "Impression/Conclusion",
            value=original.impression,
            height=120,
            help="Main findings and conclusions"
        )
        
        edited.findings = st.text_area(
            "Findings",
            value=original.findings,
            height=120,
            help="Detailed imaging findings"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            edited.comparison = st.text_area(
                "Comparison",
                value=original.comparison,
                height=80,
                help="Comparison with previous studies"
            )
        
        with col2:
            edited.technique = st.text_area(
                "Technique",
                value=original.technique,
                height=80,
                help="Imaging technique and protocol"
            )
        
        return edited
    
    def _edit_string_list(self, original_list: List[str], key: str, placeholder: str = "") -> List[str]:
        """Create editable string list interface."""
        if f"{key}_items" not in st.session_state:
            st.session_state[f"{key}_items"] = original_list.copy() if original_list else []
        
        items = st.session_state[f"{key}_items"]
        
        # Display existing items with delete option
        for i, item in enumerate(items):
            col1, col2 = st.columns([4, 1])
            with col1:
                items[i] = st.text_input(f"Item {i+1}", value=item, key=f"{key}_item_{i}")
            with col2:
                if st.button("🗑️", key=f"{key}_delete_{i}", help="Delete item"):
                    items.pop(i)
                    st.rerun()
        
        # Add new item
        new_item = st.text_input(f"Add new item", placeholder=placeholder, key=f"{key}_new")
        if st.button(f"➕ Add", key=f"{key}_add") and new_item.strip():
            items.append(new_item.strip())
            st.rerun()
        
        # Filter out empty items
        st.session_state[f"{key}_items"] = [item for item in items if item.strip()]
        return st.session_state[f"{key}_items"]
    
    def _get_selectbox_index(self, value: str, options: List[str]) -> int:
        """Get index for selectbox with fallback."""
        try:
            return options.index(value) if value in options else 0
        except:
            return 0
    
    def _parse_date(self, date_str: str):
        """Parse date string to datetime object."""
        if not date_str:
            return datetime.now().date()
        
        try:
            # Try various date formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return datetime.now().date()
        except:
            return datetime.now().date()
    
    def _display_validation_summary(self, edited_data: ExtractedMedicalData):
        """Display validation summary."""
        st.subheader("📋 Data Validation Summary")
        
        # Check completeness
        critical_fields = ["cancer_type", "t_stage", "n_stage", "m_stage"]
        completed_fields = sum(1 for field in critical_fields if getattr(edited_data, field, ""))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Critical Fields Completed", f"{completed_fields}/{len(critical_fields)}")
        
        with col2:
            completeness = (completed_fields / len(critical_fields)) * 100
            st.metric("Completeness", f"{completeness:.0f}%")
        
        with col3:
            if completeness >= 75:
                st.success("✅ Good data quality")
            elif completeness >= 50:
                st.warning("⚠️ Moderate data quality")
            else:
                st.error("❌ Incomplete data")
        
        # Show missing critical fields
        missing_fields = [field for field in critical_fields if not getattr(edited_data, field, "")]
        if missing_fields:
            st.warning(f"Missing critical fields: {', '.join(missing_fields)}")
    
    def export_edited_data(self, edited_data: ExtractedMedicalData) -> Dict[str, Any]:
        """Export edited data for further processing."""
        return {
            "edited_data": edited_data.to_dict(),
            "validation_status": self._validate_final_data(edited_data),
            "export_timestamp": datetime.now().isoformat(),
            "ready_for_phase2": self._check_phase2_readiness(edited_data)
        }
    
    def _validate_final_data(self, data: ExtractedMedicalData) -> Dict[str, Any]:
        """Final validation of edited data."""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Required field validation
        required_fields = ["cancer_type"]
        for field in required_fields:
            if not getattr(data, field, ""):
                validation["errors"].append(f"Missing required field: {field}")
                validation["is_valid"] = False
        
        # TNM consistency check
        tnm_fields = [data.t_stage, data.n_stage, data.m_stage]
        if any(tnm_fields) and not all(tnm_fields):
            validation["warnings"].append("Incomplete TNM staging - some components missing")
        
        return validation
    
    def _check_phase2_readiness(self, data: ExtractedMedicalData) -> bool:
        """Check if data is ready for Phase 2 processing."""
        # Minimum requirements for Phase 2
        return bool(data.cancer_type and (data.t_stage or data.tumor_size))
