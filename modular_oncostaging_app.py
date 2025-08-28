"""
Modular OncoStaging Application
Complete implementation of 6-module architecture with enhanced LLM prompts
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

# Import all modules
from modules.ocr_module import OCRModuleUI, OCRResult
from modules.medical_ner_module import MedicalNERUI, MedicalExtractionResult
from modules.enhanced_prompt_engine import EnhancedPromptEngine, ExtractionResult, ClinicalRecommendation
from modules.verification_module import VerificationModuleUI
from medical_guidelines import NCCNGuidelinesManager, AJCCTNMClassifier
from config import setup_logging, PAGE_TITLE, PAGE_ICON

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class ModularOncoStagingApp:
    """
    Complete modular OncoStaging application implementing:
    - Module 1: Document Upload & OCR
    - Module 2: Medical Data Extraction (LLM + NER) 
    - Module 3: Editable Data Verification
    - Module 4: TNM Classification (AJCC 9th Edition)
    - Module 5: NCCN Guidelines Decision Engine
    - Module 6: Report Generation & Export
    """
    
    def __init__(self):
        # Initialize all modules
        self.ocr_module = OCRModuleUI()
        self.ner_module = MedicalNERUI() 
        self.prompt_engine = EnhancedPromptEngine()
        self.verification_module = VerificationModuleUI()
        self.nccn_manager = NCCNGuidelinesManager()
        self.ajcc_classifier = AJCCTNMClassifier()
        
        # Initialize session state
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables."""
        if 'app_state' not in st.session_state:
            st.session_state.app_state = {
                'current_module': 1,
                'ocr_result': None,
                'extraction_result': None,
                'verified_data': None,
                'tnm_classification': None,
                'nccn_recommendations': None,
                'clinical_recommendations': None,
                'final_report': None
            }
    
    def run(self):
        """Run the complete modular application."""
        # Page configuration
        st.set_page_config(
            page_title=PAGE_TITLE,
            page_icon=PAGE_ICON,
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Header
        st.title("🏥 Modular OncoStaging - Clinical AI Platform")
        st.markdown("**Production-grade PET scan analysis with NCCN Guidelines & AJCC TNM 9th Edition**")
        
        # Sidebar navigation
        self._render_navigation_sidebar()
        
        # Main content area
        current_module = st.session_state.app_state['current_module']
        
        if current_module == 1:
            self._module1_ocr_processing()
        elif current_module == 2:
            self._module2_data_extraction()
        elif current_module == 3:
            self._module3_verification()
        elif current_module == 4:
            self._module4_tnm_classification()
        elif current_module == 5:
            self._module5_nccn_guidelines()
        elif current_module == 6:
            self._module6_report_generation()
        
        # Progress tracking
        self._render_progress_footer()
    
    def _render_navigation_sidebar(self):
        """Render navigation sidebar with module status."""
        with st.sidebar:
            st.header("🧩 Module Navigation")
            
            modules = [
                ("1️⃣ OCR Processing", 1),
                ("2️⃣ Data Extraction", 2), 
                ("3️⃣ Verification", 3),
                ("4️⃣ TNM Classification", 4),
                ("5️⃣ NCCN Guidelines", 5),
                ("6️⃣ Report Generation", 6)
            ]
            
            current = st.session_state.app_state['current_module']
            
            for module_name, module_num in modules:
                # Status indicator
                if module_num < current:
                    status = "✅"
                elif module_num == current:
                    status = "🔄"
                else:
                    status = "⏳"
                
                # Navigation button
                if st.button(f"{status} {module_name}", key=f"nav_{module_num}"):
                    st.session_state.app_state['current_module'] = module_num
                    st.rerun()
            
            # Data status
            st.markdown("---")
            st.subheader("📊 Data Status")
            
            state = st.session_state.app_state
            
            if state['ocr_result']:
                st.success("📄 OCR Complete")
            else:
                st.info("📄 OCR Pending")
            
            if state['extraction_result']:
                st.success("🔬 Extraction Complete")
            else:
                st.info("🔬 Extraction Pending")
            
            if state['verified_data']:
                st.success("✅ Verification Complete")
            else:
                st.info("✅ Verification Pending")
            
            if state['clinical_recommendations']:
                st.success("🏥 Analysis Complete")
            else:
                st.info("🏥 Analysis Pending")
            
            # Reset button
            st.markdown("---")
            if st.button("🔄 Reset Application"):
                self._reset_application()
                st.rerun()
    
    def _module1_ocr_processing(self):
        """Module 1: Document Upload & OCR Processing."""
        st.header("📄 Module 1: Document Upload & OCR")
        
        # Render OCR interface
        ocr_result = self.ocr_module.render_upload_interface()
        
        if ocr_result:
            # Store result
            st.session_state.app_state['ocr_result'] = ocr_result
            
            # Success message with navigation
            st.success("✅ OCR processing completed successfully!")
            
            if st.button("➡️ Proceed to Data Extraction", type="primary"):
                st.session_state.app_state['current_module'] = 2
                st.rerun()
        
        # Show sample if no data
        elif not st.session_state.app_state['ocr_result']:
            self._show_sample_ocr_data()
    
    def _module2_data_extraction(self):
        """Module 2: Medical Data Extraction using Enhanced LLM."""
        st.header("🔬 Module 2: Advanced Medical Data Extraction")
        
        ocr_result = st.session_state.app_state.get('ocr_result')
        
        if not ocr_result:
            st.warning("⚠️ Please complete OCR processing first.")
            if st.button("← Back to OCR"):
                st.session_state.app_state['current_module'] = 1
                st.rerun()
            return
        
        # Display OCR summary
        st.info(f"**Source:** {ocr_result.file_info['name']} | **Method:** {ocr_result.method} | **Confidence:** {ocr_result.confidence:.1%}")
        
        # Extraction options
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**Choose extraction method:**")
            use_enhanced_prompts = st.checkbox("Use Enhanced LLM Prompts", value=True, 
                                             help="Use production-grade clinical prompts for better accuracy")
        
        with col2:
            if st.button("🔍 Extract Medical Data", type="primary"):
                with st.spinner("Extracting structured medical data..."):
                    try:
                        if use_enhanced_prompts:
                            # Use enhanced prompt engine
                            extraction_result = self.prompt_engine.extract_structured_data(ocr_result.text)
                            
                            # Convert to consistent format and store
                            st.session_state.app_state['extraction_result'] = extraction_result
                            
                            # Display results
                            self._display_enhanced_extraction_results(extraction_result)
                            
                        else:
                            # Use basic NER module
                            ner_result = self.ner_module.ner_module.extract_medical_data(ocr_result.text)
                            st.session_state.app_state['extraction_result'] = ner_result
                            
                            # Display results  
                            self._display_ner_extraction_results(ner_result)
                        
                        # Navigation
                        if st.button("➡️ Proceed to Verification", type="primary"):
                            st.session_state.app_state['current_module'] = 3
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ Extraction failed: {str(e)}")
        
        # Show previous results if available
        if st.session_state.app_state.get('extraction_result'):
            st.markdown("---")
            st.subheader("📋 Previous Extraction Results")
            self._display_extraction_summary()
    
    def _module3_verification(self):
        """Module 3: Interactive Data Verification."""
        extraction_result = st.session_state.app_state.get('extraction_result')
        
        if not extraction_result:
            st.warning("⚠️ Please complete data extraction first.")
            if st.button("← Back to Extraction"):
                st.session_state.app_state['current_module'] = 2
                st.rerun()
            return
        
        # Render verification interface
        verified_data = self.verification_module.render_verification_interface(extraction_result)
        
        if verified_data:
            # Store verified data
            st.session_state.app_state['verified_data'] = verified_data
            
            # Navigation
            if st.button("➡️ Proceed to TNM Classification", type="primary"):
                st.session_state.app_state['current_module'] = 4
                st.rerun()
    
    def _module4_tnm_classification(self):
        """Module 4: AJCC TNM 9th Edition Classification."""
        st.header("🔬 Module 4: TNM Classification (AJCC 9th Edition)")
        
        verified_data = st.session_state.app_state.get('verified_data')
        
        if not verified_data:
            st.warning("⚠️ Please complete data verification first.")
            if st.button("← Back to Verification"):
                st.session_state.app_state['current_module'] = 3
                st.rerun()
            return
        
        # Display verified data summary
        st.subheader("📋 Verified Patient Data")
        self._display_verified_data_summary(verified_data)
        
        # TNM Classification
        st.subheader("🎯 AJCC TNM Classification")
        
        if st.button("🔍 Perform TNM Classification", type="primary"):
            with st.spinner("Applying AJCC 9th Edition classification..."):
                try:
                    # Extract TNM components
                    cancer_type = self._extract_cancer_type_for_classification(verified_data)
                    tnm_components = self._extract_tnm_components(verified_data)
                    
                    if cancer_type and all(tnm_components.values()):
                        # Perform classification
                        classification_result = self.ajcc_classifier.classify_tnm_stage(
                            cancer_type,
                            tnm_components['t_stage'],
                            tnm_components['n_stage'], 
                            tnm_components['m_stage']
                        )
                        
                        # Store result
                        st.session_state.app_state['tnm_classification'] = classification_result
                        
                        # Display results
                        self._display_tnm_classification_results(classification_result)
                        
                        # Navigation
                        if st.button("➡️ Proceed to NCCN Guidelines", type="primary"):
                            st.session_state.app_state['current_module'] = 5
                            st.rerun()
                    
                    else:
                        st.error("❌ Insufficient TNM data for classification. Please review verified data.")
                        st.info("**Required:** Cancer type, T stage, N stage, M stage")
                        
                except Exception as e:
                    st.error(f"❌ TNM classification failed: {str(e)}")
        
        # Show previous results if available
        if st.session_state.app_state.get('tnm_classification'):
            st.markdown("---")
            st.subheader("📊 Previous Classification Results")
            self._display_tnm_classification_results(st.session_state.app_state['tnm_classification'])
    
    def _module5_nccn_guidelines(self):
        """Module 5: NCCN Guidelines Decision Engine."""
        st.header("📚 Module 5: NCCN Guidelines & Clinical Recommendations")
        
        verified_data = st.session_state.app_state.get('verified_data')
        tnm_classification = st.session_state.app_state.get('tnm_classification')
        
        if not verified_data or not tnm_classification:
            st.warning("⚠️ Please complete TNM classification first.")
            if st.button("← Back to TNM Classification"):
                st.session_state.app_state['current_module'] = 4
                st.rerun()
            return
        
        # Display classification summary
        st.info(f"**Cancer Type:** {tnm_classification.get('cancer_type', 'Unknown')} | **Stage:** {tnm_classification.get('overall_stage', 'Unknown')}")
        
        # Clinical recommendations
        st.subheader("🏥 Generate Clinical Recommendations")
        
        if st.button("🔍 Generate Recommendations", type="primary"):
            with st.spinner("Generating clinical recommendations with NCCN guidelines..."):
                try:
                    # Prepare patient data for clinical analysis
                    patient_data = self._prepare_patient_data_for_recommendations(verified_data, tnm_classification)
                    
                    # Generate clinical recommendations using enhanced prompts
                    clinical_recommendations = self.prompt_engine.generate_clinical_recommendations(patient_data)
                    
                    # Get NCCN-specific recommendations
                    cancer_type = tnm_classification.get('cancer_type', '')
                    stage = tnm_classification.get('overall_stage', '')
                    
                    if cancer_type in ['lung', 'breast', 'colon', 'prostate', 'pancreatic']:
                        nccn_recommendations = self.nccn_manager.get_treatment_recommendations(cancer_type, stage)
                        st.session_state.app_state['nccn_recommendations'] = nccn_recommendations
                    
                    # Store clinical recommendations
                    st.session_state.app_state['clinical_recommendations'] = clinical_recommendations
                    
                    # Display results
                    self._display_clinical_recommendations(clinical_recommendations, 
                                                         st.session_state.app_state.get('nccn_recommendations'))
                    
                    # Navigation
                    if st.button("➡️ Generate Final Report", type="primary"):
                        st.session_state.app_state['current_module'] = 6
                        st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Recommendation generation failed: {str(e)}")
        
        # Show previous results if available
        if st.session_state.app_state.get('clinical_recommendations'):
            st.markdown("---")
            st.subheader("📋 Previous Recommendations")
            self._display_clinical_recommendations(
                st.session_state.app_state['clinical_recommendations'],
                st.session_state.app_state.get('nccn_recommendations')
            )
    
    def _module6_report_generation(self):
        """Module 6: Final Report Generation & Export."""
        st.header("📄 Module 6: Final Report Generation")
        
        # Check if all required data is available
        required_data = ['verified_data', 'tnm_classification', 'clinical_recommendations']
        missing_data = [key for key in required_data if not st.session_state.app_state.get(key)]
        
        if missing_data:
            st.warning(f"⚠️ Missing required data: {', '.join(missing_data)}")
            if st.button("← Back to Previous Module"):
                st.session_state.app_state['current_module'] = 5
                st.rerun()
            return
        
        # Generate comprehensive report
        if st.button("📋 Generate Comprehensive Report", type="primary"):
            with st.spinner("Generating final clinical report..."):
                try:
                    final_report = self._generate_comprehensive_report()
                    st.session_state.app_state['final_report'] = final_report
                    
                    # Display report
                    self._display_final_report(final_report)
                    
                except Exception as e:
                    st.error(f"❌ Report generation failed: {str(e)}")
        
        # Show existing report if available
        if st.session_state.app_state.get('final_report'):
            self._display_final_report(st.session_state.app_state['final_report'])
            
            # Export options
            self._render_export_options()
    
    def _display_enhanced_extraction_results(self, result: ExtractionResult):
        """Display enhanced extraction results."""
        st.success("✅ Enhanced extraction completed!")
        
        # Key findings summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Cancer Type", result.cancer_type or "Not specified")
        with col2:
            st.metric("Tumor Size", result.tumor_size_cm or "Not specified")
        with col3:
            st.metric("SUV Max", result.suv_max or "Not specified")
        
        # Detailed results in expandable section
        with st.expander("🔍 Detailed Extraction Results", expanded=False):
            st.json(result.to_dict())
    
    def _display_ner_extraction_results(self, result: MedicalExtractionResult):
        """Display NER extraction results."""
        st.success("✅ NER extraction completed!")
        
        # Display summary
        summary = result.to_dict()
        st.json(summary)
    
    def _display_extraction_summary(self):
        """Display extraction summary."""
        result = st.session_state.app_state['extraction_result']
        
        if isinstance(result, ExtractionResult):
            # Enhanced extraction result
            st.write(f"**Cancer Type:** {result.cancer_type}")
            st.write(f"**Tumor Location:** {result.tumor_location}")
            st.write(f"**TNM Details:** {result.tnm_details}")
        else:
            # Basic NER result
            st.write("Basic NER extraction completed")
    
    def _display_verified_data_summary(self, verified_data: ExtractionResult):
        """Display verified data summary."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Patient Info:**")
            st.write(f"• Age: {verified_data.age or 'Not specified'}")
            st.write(f"• Gender: {verified_data.gender or 'Not specified'}")
        
        with col2:
            st.write("**Cancer Info:**")
            st.write(f"• Type: {verified_data.cancer_type or 'Not specified'}")
            st.write(f"• Location: {verified_data.tumor_location or 'Not specified'}")
    
    def _extract_cancer_type_for_classification(self, verified_data: ExtractionResult) -> str:
        """Extract and normalize cancer type for classification."""
        cancer_type = verified_data.cancer_type.lower() if verified_data.cancer_type else ""
        
        # Normalize common cancer types
        if "lung" in cancer_type or "nsclc" in cancer_type or "sclc" in cancer_type:
            return "lung"
        elif "breast" in cancer_type:
            return "breast"
        elif "colon" in cancer_type or "colorectal" in cancer_type:
            return "colon"
        elif "prostate" in cancer_type:
            return "prostate"
        elif "pancreatic" in cancer_type:
            return "pancreatic"
        
        return cancer_type
    
    def _extract_tnm_components(self, verified_data: ExtractionResult) -> Dict[str, str]:
        """Extract TNM components from verified data."""
        tnm_text = verified_data.tnm_details or ""
        
        # Parse TNM string
        import re
        
        t_match = re.search(r'[cCpP]?T([0-4][a-c]?(?:is)?)', tnm_text)
        n_match = re.search(r'[cCpP]?N([0-3][a-c]?)', tnm_text)
        m_match = re.search(r'[cCpP]?M([0-1][a-c]?)', tnm_text)
        
        return {
            't_stage': f"T{t_match.group(1)}" if t_match else "",
            'n_stage': f"N{n_match.group(1)}" if n_match else "",
            'm_stage': f"M{m_match.group(1)}" if m_match else ""
        }
    
    def _display_tnm_classification_results(self, classification_result: Dict[str, Any]):
        """Display TNM classification results."""
        if 'error' in classification_result:
            st.error(f"❌ {classification_result['error']}")
            return
        
        st.success("✅ TNM classification completed!")
        
        # TNM Components
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("T Stage", classification_result.get('tnm_normalized', {}).get('T', 'Unknown'))
        with col2:
            st.metric("N Stage", classification_result.get('tnm_normalized', {}).get('N', 'Unknown'))
        with col3:
            st.metric("M Stage", classification_result.get('tnm_normalized', {}).get('M', 'Unknown'))
        with col4:
            st.metric("Overall Stage", classification_result.get('overall_stage', 'Unknown'))
        
        # Descriptions
        st.subheader("📝 Stage Descriptions")
        st.write(f"**T Stage:** {classification_result.get('t_description', 'N/A')}")
        st.write(f"**N Stage:** {classification_result.get('n_description', 'N/A')}")
        st.write(f"**M Stage:** {classification_result.get('m_description', 'N/A')}")
    
    def _prepare_patient_data_for_recommendations(self, verified_data: ExtractionResult, 
                                                tnm_classification: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare patient data for clinical recommendations."""
        return {
            'age': verified_data.age,
            'gender': verified_data.gender,
            'cancer_type': verified_data.cancer_type,
            'tumor_size_cm': verified_data.tumor_size_cm,
            'tumor_location': verified_data.tumor_location,
            'suv_max': verified_data.suv_max,
            'lymph_node_involvement': verified_data.lymph_node_involvement,
            'distant_metastasis': verified_data.distant_metastasis,
            'tnm_details': verified_data.tnm_details,
            'clinical_impression': verified_data.clinical_impression,
            'overall_stage': tnm_classification.get('overall_stage', ''),
            'ajcc_classification': tnm_classification
        }
    
    def _display_clinical_recommendations(self, clinical_recs: ClinicalRecommendation, 
                                        nccn_recs: Optional[Dict[str, Any]] = None):
        """Display clinical recommendations."""
        st.success("✅ Clinical recommendations generated!")
        
        # AJCC Staging
        st.subheader("🔬 AJCC Staging")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("AJCC Stage", clinical_recs.ajcc_stage)
        with col2:
            st.metric("Stage Group", clinical_recs.stage_group)
        
        # Recommendations
        st.subheader("🏥 Clinical Recommendations")
        
        if clinical_recs.diagnostic_recommendations:
            st.write("**Diagnostic Recommendations:**")
            for rec in clinical_recs.diagnostic_recommendations:
                st.write(f"• {rec}")
        
        if clinical_recs.treatment_recommendations:
            st.write("**Treatment Recommendations:**")
            for rec in clinical_recs.treatment_recommendations:
                st.write(f"• {rec}")
        
        # Clinical Rationale
        if clinical_recs.clinical_rationale:
            st.subheader("🧠 Clinical Rationale")
            st.write(clinical_recs.clinical_rationale)
        
        # NCCN Specific Recommendations
        if nccn_recs and 'recommendations' in nccn_recs:
            st.subheader("📚 NCCN Guidelines")
            for rec in nccn_recs['recommendations']:
                st.write(f"• {rec}")
    
    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive final report."""
        state = st.session_state.app_state
        
        return {
            'report_metadata': {
                'generation_timestamp': datetime.now().isoformat(),
                'report_type': 'Comprehensive OncoStaging Analysis',
                'modules_completed': 6,
                'data_sources': ['OCR', 'Enhanced LLM', 'AJCC 9th Edition', 'NCCN Guidelines']
            },
            'patient_data': state['verified_data'].to_dict() if state['verified_data'] else {},
            'imaging_analysis': {
                'ocr_result': {
                    'method': state['ocr_result'].method if state['ocr_result'] else 'Unknown',
                    'confidence': state['ocr_result'].confidence if state['ocr_result'] else 0,
                    'processing_time': state['ocr_result'].processing_time if state['ocr_result'] else 0
                }
            },
            'tnm_classification': state['tnm_classification'] or {},
            'clinical_recommendations': state['clinical_recommendations'].to_dict() if state['clinical_recommendations'] else {},
            'nccn_guidelines': state['nccn_recommendations'] or {},
            'report_summary': self._generate_executive_summary()
        }
    
    def _generate_executive_summary(self) -> str:
        """Generate executive summary."""
        state = st.session_state.app_state
        verified_data = state.get('verified_data')
        tnm_classification = state.get('tnm_classification')
        
        if not verified_data or not tnm_classification:
            return "Incomplete analysis - please complete all modules."
        
        summary = f"""
**EXECUTIVE SUMMARY**

Patient: {verified_data.age or 'Unknown'} year old {verified_data.gender or 'Unknown'} patient
Cancer Type: {verified_data.cancer_type or 'Not specified'}
Tumor Location: {verified_data.tumor_location or 'Not specified'}
Tumor Size: {verified_data.tumor_size_cm or 'Not specified'}
SUV Max: {verified_data.suv_max or 'Not specified'}

AJCC Classification: {tnm_classification.get('overall_stage', 'Unknown')}
TNM: {tnm_classification.get('tnm_normalized', {}).get('T', 'Tx')}{tnm_classification.get('tnm_normalized', {}).get('N', 'Nx')}{tnm_classification.get('tnm_normalized', {}).get('M', 'Mx')}

Clinical Impression: {verified_data.clinical_impression or 'Not specified'}

This analysis was performed using AI-assisted extraction, AJCC 9th Edition classification, and NCCN clinical guidelines. All recommendations should be reviewed by qualified oncology professionals.
"""
        return summary.strip()
    
    def _display_final_report(self, report: Dict[str, Any]):
        """Display final comprehensive report."""
        st.success("✅ Comprehensive report generated!")
        
        # Executive Summary
        st.subheader("📋 Executive Summary")
        st.text_area("Summary", report['report_summary'], height=200)
        
        # Key Metrics
        st.subheader("📊 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        patient_data = report.get('patient_data', {})
        tnm_data = report.get('tnm_classification', {})
        
        with col1:
            st.metric("Cancer Type", patient_data.get('cancer_type', 'Unknown'))
        with col2:
            st.metric("Stage", tnm_data.get('overall_stage', 'Unknown'))
        with col3:
            st.metric("SUV Max", patient_data.get('suv_max', 'Unknown'))
        with col4:
            st.metric("Analysis Confidence", "High" if report['imaging_analysis']['ocr_result'].get('confidence', 0) > 0.8 else "Moderate")
        
        # Detailed sections in tabs
        tabs = st.tabs(["🔬 Clinical Data", "📊 Classifications", "🏥 Recommendations", "📄 Full Report"])
        
        with tabs[0]:
            st.json(patient_data)
        
        with tabs[1]:
            st.json(tnm_data)
        
        with tabs[2]:
            clinical_recs = report.get('clinical_recommendations', {})
            nccn_recs = report.get('nccn_guidelines', {})
            st.write("**Clinical Recommendations:**")
            st.json(clinical_recs)
            if nccn_recs:
                st.write("**NCCN Guidelines:**")
                st.json(nccn_recs)
        
        with tabs[3]:
            st.json(report)
    
    def _render_export_options(self):
        """Render export options for final report."""
        st.subheader("📥 Export Options")
        
        report = st.session_state.app_state.get('final_report')
        if not report:
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # JSON Export
            json_data = json.dumps(report, indent=2, default=str)
            st.download_button(
                "📄 Download JSON Report",
                data=json_data,
                file_name=f"oncostaging_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            # Summary Export
            summary_text = f"""OncoStaging Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{report['report_summary']}

Clinical Recommendations:
{json.dumps(report.get('clinical_recommendations', {}), indent=2, default=str)}

NCCN Guidelines:
{json.dumps(report.get('nccn_guidelines', {}), indent=2, default=str)}

---
This report was generated using AI-assisted analysis and should be reviewed by qualified medical professionals.
"""
            st.download_button(
                "📝 Download Summary",
                data=summary_text,
                file_name=f"oncostaging_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with col3:
            if st.button("📧 Email Report"):
                st.info("Email functionality would be implemented here")
    
    def _render_progress_footer(self):
        """Render progress tracking footer."""
        st.markdown("---")
        
        # Progress bar
        current_module = st.session_state.app_state['current_module']
        progress = current_module / 6
        
        st.progress(progress)
        st.caption(f"Module {current_module}/6 - {progress:.0%} Complete")
    
    def _reset_application(self):
        """Reset entire application state."""
        st.session_state.app_state = {
            'current_module': 1,
            'ocr_result': None,
            'extraction_result': None,
            'verified_data': None,
            'tnm_classification': None,
            'nccn_recommendations': None,
            'clinical_recommendations': None,
            'final_report': None
        }
    
    def _show_sample_ocr_data(self):
        """Show sample OCR data for demonstration."""
        with st.expander("📋 View Sample Analysis", expanded=False):
            st.info("**Sample PET/CT Report Text:**")
            sample_text = """
Patient: John Doe, Age: 65, Male
Study Date: 2024-01-15
Indication: Lung cancer staging

FINDINGS:
There is a hypermetabolic mass in the right upper lobe measuring approximately 3.2 x 2.8 cm with SUVmax of 8.5.
Multiple enlarged mediastinal lymph nodes with increased FDG uptake, largest measuring 1.5 cm with SUVmax of 4.2.
No evidence of distant metastatic disease.

IMPRESSION:
1. Right upper lobe mass consistent with primary lung cancer (T2N2M0, Stage IIIA)
2. Mediastinal lymphadenopathy consistent with nodal metastases
3. No distant metastases identified

Recommend tissue confirmation and multidisciplinary evaluation.
"""
            st.text_area("Sample Report", sample_text, height=200)


def main():
    """Main entry point."""
    app = ModularOncoStagingApp()
    app.run()


if __name__ == "__main__":
    main()
