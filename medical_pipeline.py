"""
Complete Medical AI Pipeline for PET Scan Report Processing
Implements 3-step clinical workflow with NCCN/AJCC integration
"""

import logging
import streamlit as st
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import json
import io

from advanced_document_processor import AdvancedDocumentProcessor, ExtractedMedicalData
from interactive_editor import MedicalDataEditor
from medical_guidelines import NCCNGuidelinesManager, AJCCTNMClassifier
from ai_integration import MedicalAIAssistant

logger = logging.getLogger(__name__)


class MedicalAIPipeline:
    """
    Complete Medical AI Pipeline following clinical workflow:
    Step 1: OCR and Data Extraction
    Step 2: Data Verification Interface  
    Step 3: Clinical Interpretation with Guidelines
    """
    
    def __init__(self):
        self.document_processor = AdvancedDocumentProcessor()
        self.data_editor = MedicalDataEditor()
        self.nccn_manager = NCCNGuidelinesManager()
        self.ajcc_classifier = AJCCTNMClassifier()
        self.ai_assistant = MedicalAIAssistant()
        
        # Initialize session state
        if 'pipeline_state' not in st.session_state:
            st.session_state.pipeline_state = {
                'current_step': 1,
                'raw_extraction': None,
                'verified_data': None,
                'clinical_analysis': None
            }
    
    def run_complete_pipeline(self):
        """Run the complete medical AI pipeline."""
        st.title("🏥 Medical AI Pipeline - PET Scan Report Analysis")
        st.markdown("**Clinical-grade analysis following NCCN Guidelines and AJCC TNM 9th Edition**")
        
        # Progress indicator
        self._render_progress_indicator()
        
        # Current step display
        current_step = st.session_state.pipeline_state['current_step']
        
        if current_step == 1:
            self._step1_ocr_extraction()
        elif current_step == 2:
            self._step2_data_verification()
        elif current_step == 3:
            self._step3_clinical_interpretation()
        
        # Navigation buttons
        self._render_navigation_buttons()
    
    def _render_progress_indicator(self):
        """Render pipeline progress indicator."""
        steps = [
            "📄 OCR & Extraction",
            "✏️ Data Verification", 
            "🏥 Clinical Analysis"
        ]
        
        current = st.session_state.pipeline_state['current_step']
        
        cols = st.columns(3)
        for i, (col, step) in enumerate(zip(cols, steps), 1):
            with col:
                if i < current:
                    st.success(f"✅ {step}")
                elif i == current:
                    st.info(f"🔄 {step}")
                else:
                    st.write(f"⏳ {step}")
    
    def _step1_ocr_extraction(self):
        """Step 1: OCR and Data Extraction from PET scan reports."""
        st.header("📄 Step 1: Document Processing & Data Extraction")
        st.markdown("""
        **Upload your PET scan report** for advanced processing:
        - **OCR (Optical Character Recognition)** for scanned documents
        - **AI-powered NER (Named Entity Recognition)** using DeepSeek
        - **Medical entity extraction** with confidence scoring
        """)
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose PET scan report file",
            type=['pdf', 'docx', 'png', 'jpg', 'jpeg'],
            help="Supports PDF, DOCX, and image files"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.info(f"**File:** {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            # Processing button
            if st.button("🔍 Process Document", type="primary"):
                with st.spinner("Processing document with advanced OCR and AI..."):
                    # Process document
                    result = self.document_processor.process_document_advanced(uploaded_file)
                    
                    if result['success']:
                        # Store results
                        st.session_state.pipeline_state['raw_extraction'] = result
                        
                        # Display extraction results
                        self._display_extraction_results(result)
                        
                        # Enable next step
                        st.success("✅ Document processed successfully! Ready for verification.")
                        if st.button("➡️ Proceed to Data Verification"):
                            st.session_state.pipeline_state['current_step'] = 2
                            st.rerun()
                    else:
                        st.error(f"❌ Processing failed: {result['error']}")
        
        # Show sample if no file uploaded
        else:
            with st.expander("📋 See sample extraction format"):
                self._show_sample_extraction()
    
    def _display_extraction_results(self, result: Dict[str, Any]):
        """Display extraction results from Step 1."""
        st.subheader("📊 Extraction Results")
        
        extracted_data = result['extracted_data']
        quality = result['extraction_quality']
        
        # Quality metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Completeness", f"{quality['completeness']:.0%}")
        with col2:
            st.metric("Confidence", f"{quality['confidence']:.0%}")
        with col3:
            st.metric("Critical Fields", f"{quality['critical_fields_found']}/7")
        
        # Key extracted data
        st.subheader("🎯 Key Medical Information")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Patient & Study:**")
            st.write(f"• **Patient ID:** {extracted_data.patient_id or 'Not found'}")
            st.write(f"• **Age:** {extracted_data.age or 'Not found'}")
            st.write(f"• **Gender:** {extracted_data.gender or 'Not found'}")
            st.write(f"• **Study Date:** {extracted_data.study_date or 'Not found'}")
            
        with col2:
            st.markdown("**Cancer Information:**")
            st.write(f"• **Cancer Type:** {extracted_data.cancer_type or 'Not found'}")
            st.write(f"• **Primary Site:** {extracted_data.primary_site or 'Not found'}")
            st.write(f"• **Tumor Size:** {extracted_data.tumor_size or 'Not found'}")
            st.write(f"• **SUV Max:** {extracted_data.suv_max or 'Not found'}")
        
        # TNM Information
        if any([extracted_data.t_stage, extracted_data.n_stage, extracted_data.m_stage]):
            st.markdown("**TNM Staging:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**T:** {extracted_data.t_stage or 'Not found'}")
            with col2:
                st.write(f"**N:** {extracted_data.n_stage or 'Not found'}")
            with col3:
                st.write(f"**M:** {extracted_data.m_stage or 'Not found'}")
        
        # Show raw extraction details
        with st.expander("🔍 View detailed extraction"):
            st.json(extracted_data.to_dict())
    
    def _step2_data_verification(self):
        """Step 2: Interactive Data Verification Interface."""
        st.header("✏️ Step 2: Data Verification & Correction")
        st.markdown("""
        **Review and correct the extracted information:**
        - Verify accuracy of OCR/AI extraction
        - Edit any incorrect or missing data
        - Add clinical context as needed
        """)
        
        raw_data = st.session_state.pipeline_state.get('raw_extraction')
        if not raw_data:
            st.warning("⚠️ No extracted data found. Please complete Step 1 first.")
            if st.button("← Back to Step 1"):
                st.session_state.pipeline_state['current_step'] = 1
                st.rerun()
            return
        
        extracted_data = raw_data['extracted_data']
        
        # Interactive editing interface
        st.subheader("📝 Interactive Data Editor")
        verified_data = self.data_editor.render_editor_interface(extracted_data)
        
        # Save verified data button
        if st.button("💾 Save Verified Data", type="primary"):
            # Export verified data
            export_result = self.data_editor.export_edited_data(verified_data)
            
            if export_result['validation_status']['is_valid']:
                st.session_state.pipeline_state['verified_data'] = export_result
                st.success("✅ Data verified and saved successfully!")
                
                if export_result['ready_for_phase2']:
                    if st.button("➡️ Proceed to Clinical Analysis"):
                        st.session_state.pipeline_state['current_step'] = 3
                        st.rerun()
                else:
                    st.warning("⚠️ Minimum data requirements not met for clinical analysis")
            else:
                st.error("❌ Data validation failed:")
                for error in export_result['validation_status']['errors']:
                    st.error(f"• {error}")
    
    def _step3_clinical_interpretation(self):
        """Step 3: Clinical Interpretation with NCCN/AJCC Guidelines."""
        st.header("🏥 Step 3: Clinical Interpretation & Guidelines")
        st.markdown("""
        **AI-powered clinical analysis using:**
        - 📋 **NCCN Clinical Practice Guidelines** (latest version)
        - 📚 **AJCC TNM Classification** (9th Edition)
        - 🤖 **DeepSeek AI** for clinical reasoning
        """)
        
        verified_data = st.session_state.pipeline_state.get('verified_data')
        if not verified_data:
            st.warning("⚠️ No verified data found. Please complete Step 2 first.")
            if st.button("← Back to Step 2"):
                st.session_state.pipeline_state['current_step'] = 2
                st.rerun()
            return
        
        medical_data = verified_data['edited_data']
        
        # Analyze button
        if st.button("🔍 Perform Clinical Analysis", type="primary"):
            with st.spinner("Analyzing with NCCN Guidelines and AJCC Classification..."):
                analysis_result = self._perform_clinical_analysis(medical_data)
                st.session_state.pipeline_state['clinical_analysis'] = analysis_result
        
        # Display analysis results
        if st.session_state.pipeline_state.get('clinical_analysis'):
            self._display_clinical_analysis()
    
    def _perform_clinical_analysis(self, medical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive clinical analysis."""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'patient_summary': self._create_patient_summary(medical_data),
            'tnm_classification': None,
            'nccn_recommendations': None,
            'ai_clinical_reasoning': None,
            'risk_stratification': None,
            'follow_up_plan': None
        }
        
        cancer_type = medical_data.get('cancer_type', '').lower()
        
        # 1. AJCC TNM Classification
        if all([medical_data.get('t_stage'), medical_data.get('n_stage'), medical_data.get('m_stage')]):
            analysis['tnm_classification'] = self.ajcc_classifier.classify_tnm_stage(
                cancer_type,
                medical_data['t_stage'],
                medical_data['n_stage'],
                medical_data['m_stage']
            )
        
        # 2. NCCN Guidelines
        if cancer_type in ['lung', 'breast', 'colon', 'prostate', 'pancreatic']:
            # Download/update guidelines
            self.nccn_manager.download_nccn_guidelines(cancer_type)
            
            # Get stage for recommendations
            stage = analysis['tnm_classification']['overall_stage'] if analysis['tnm_classification'] else medical_data.get('overall_stage', '')
            
            if stage:
                analysis['nccn_recommendations'] = self.nccn_manager.get_treatment_recommendations(
                    cancer_type, stage
                )
        
        # 3. AI Clinical Reasoning
        analysis['ai_clinical_reasoning'] = self._get_ai_clinical_reasoning(medical_data, analysis)
        
        # 4. Risk Stratification
        analysis['risk_stratification'] = self._perform_risk_stratification(medical_data, analysis)
        
        # 5. Follow-up Plan
        analysis['follow_up_plan'] = self._create_follow_up_plan(medical_data, analysis)
        
        return analysis
    
    def _get_ai_clinical_reasoning(self, medical_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Get AI-powered clinical reasoning."""
        try:
            prompt = self._create_clinical_reasoning_prompt(medical_data, analysis)
            
            response = self.ai_assistant.client.query_model(
                prompt=prompt,
                model="deepseek-chat",
                temperature=0.3,  # Low temperature for clinical accuracy
                max_tokens=1500
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"AI clinical reasoning failed: {e}")
            return "AI clinical reasoning unavailable due to technical issues."
    
    def _create_clinical_reasoning_prompt(self, medical_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Create prompt for AI clinical reasoning."""
        tnm_info = analysis.get('tnm_classification', {})
        nccn_info = analysis.get('nccn_recommendations', {})
        
        prompt = f"""You are an experienced oncologist providing clinical interpretation of a PET scan report.

PATIENT DATA:
- Cancer Type: {medical_data.get('cancer_type', 'Not specified')}
- Primary Site: {medical_data.get('primary_site', 'Not specified')}
- TNM Staging: T{medical_data.get('t_stage', 'x')} N{medical_data.get('n_stage', 'x')} M{medical_data.get('m_stage', 'x')}
- Overall Stage: {tnm_info.get('overall_stage', 'Not determined')}
- Tumor Size: {medical_data.get('tumor_size', 'Not specified')}
- SUV Max: {medical_data.get('suv_max', 'Not specified')}
- Lymph Nodes: {medical_data.get('lymph_nodes_involved', 'Not specified')}

AJCC CLASSIFICATION:
{json.dumps(tnm_info, indent=2) if tnm_info else 'Not available'}

NCCN RECOMMENDATIONS:
{json.dumps(nccn_info.get('recommendations', []), indent=2) if nccn_info else 'Not available'}

CLINICAL TASK:
Provide comprehensive clinical interpretation including:

1. **Clinical Summary**: Synthesize the key findings
2. **Staging Accuracy**: Validate TNM staging against imaging findings
3. **Prognostic Assessment**: Comment on prognosis based on stage and SUV values
4. **Treatment Implications**: Discuss treatment approach per NCCN guidelines
5. **Next Steps**: Recommend immediate next diagnostic or therapeutic steps
6. **Risk Factors**: Identify any concerning features requiring urgent attention

**Important**: 
- Base recommendations strictly on provided data
- Cite NCCN guidelines when applicable
- Note any data limitations
- Emphasize need for multidisciplinary consultation
- Use clear, professional medical language

CLINICAL INTERPRETATION:"""
        
        return prompt
    
    def _perform_risk_stratification(self, medical_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Perform risk stratification based on available data."""
        risk_factors = []
        risk_level = "Unknown"
        
        # Stage-based risk
        tnm = analysis.get('tnm_classification', {})
        stage = tnm.get('overall_stage', '')
        
        if 'Stage IV' in stage:
            risk_level = "High"
            risk_factors.append("Distant metastatic disease")
        elif 'Stage III' in stage:
            risk_level = "Intermediate-High"
            risk_factors.append("Locally advanced disease")
        elif 'Stage II' in stage:
            risk_level = "Intermediate"
            risk_factors.append("Regional involvement")
        elif 'Stage I' in stage:
            risk_level = "Low-Intermediate"
        
        # SUV-based risk (if available)
        suv_max = medical_data.get('suv_max', '')
        if suv_max:
            try:
                suv_value = float(suv_max)
                if suv_value > 10:
                    risk_factors.append("High metabolic activity (SUV >10)")
                elif suv_value > 5:
                    risk_factors.append("Moderate metabolic activity")
            except ValueError:
                pass
        
        # Size-based risk
        tumor_size = medical_data.get('tumor_size', '')
        if 'cm' in tumor_size:
            try:
                import re
                size_match = re.search(r'(\d+(?:\.\d+)?)', tumor_size)
                if size_match:
                    size_value = float(size_match.group(1))
                    if size_value > 5:
                        risk_factors.append("Large primary tumor (>5cm)")
            except:
                pass
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "prognostic_info": tnm.get('prognosis_info', {}) if 'tnm_classification' in analysis else {}
        }
    
    def _create_follow_up_plan(self, medical_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create follow-up plan based on findings."""
        cancer_type = medical_data.get('cancer_type', '').lower()
        stage = analysis.get('tnm_classification', {}).get('overall_stage', '')
        
        # Basic follow-up framework
        follow_up = {
            "immediate_actions": [
                "Multidisciplinary tumor board discussion",
                "Complete staging if not already done"
            ],
            "imaging_surveillance": [],
            "laboratory_monitoring": [],
            "specialist_referrals": [],
            "patient_education": []
        }
        
        # Stage-specific recommendations
        if 'Stage IV' in stage:
            follow_up["immediate_actions"].extend([
                "Palliative care consultation",
                "Molecular/biomarker testing if indicated"
            ])
            follow_up["imaging_surveillance"].append("Response assessment every 2-3 cycles of treatment")
        elif 'Stage III' in stage:
            follow_up["immediate_actions"].append("Radiation oncology consultation")
            follow_up["imaging_surveillance"].append("Post-treatment imaging in 8-12 weeks")
        elif 'Stage I-II' in stage:
            follow_up["imaging_surveillance"].append("Surveillance imaging every 6-12 months")
        
        # Cancer-specific additions
        if cancer_type == 'lung':
            follow_up["laboratory_monitoring"].append("CEA levels")
            follow_up["specialist_referrals"].append("Thoracic surgery consultation")
        elif cancer_type == 'breast':
            follow_up["laboratory_monitoring"].extend(["Tumor markers (if elevated)", "Hormone receptor status"])
        elif cancer_type == 'colon':
            follow_up["laboratory_monitoring"].append("CEA levels")
            follow_up["specialist_referrals"].append("Colorectal surgery consultation")
        
        return follow_up
    
    def _create_patient_summary(self, medical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create structured patient summary."""
        return {
            "demographics": {
                "age": medical_data.get('age', 'Not specified'),
                "gender": medical_data.get('gender', 'Not specified'),
                "patient_id": medical_data.get('patient_id', 'Not specified')
            },
            "diagnosis": {
                "primary_cancer": medical_data.get('cancer_type', 'Not specified'),
                "primary_site": medical_data.get('primary_site', 'Not specified'),
                "histology": medical_data.get('histology', 'Not specified')
            },
            "imaging_findings": {
                "study_date": medical_data.get('study_date', 'Not specified'),
                "tumor_size": medical_data.get('tumor_size', 'Not specified'),
                "suv_max": medical_data.get('suv_max', 'Not specified'),
                "lymph_nodes": medical_data.get('lymph_nodes_involved', 'Not specified'),
                "metastases": medical_data.get('metastatic_sites', [])
            }
        }
    
    def _display_clinical_analysis(self):
        """Display comprehensive clinical analysis results."""
        analysis = st.session_state.pipeline_state['clinical_analysis']
        
        st.subheader("🏥 Clinical Analysis Results")
        
        # Create tabs for different sections
        tabs = st.tabs([
            "📋 Summary",
            "🔬 TNM Classification", 
            "📚 NCCN Guidelines",
            "🤖 AI Analysis",
            "⚠️ Risk Assessment",
            "📅 Follow-up Plan"
        ])
        
        # Tab 1: Summary
        with tabs[0]:
            self._display_patient_summary(analysis['patient_summary'])
        
        # Tab 2: TNM Classification
        with tabs[1]:
            if analysis['tnm_classification']:
                self._display_tnm_classification(analysis['tnm_classification'])
            else:
                st.info("TNM classification not available - insufficient staging data")
        
        # Tab 3: NCCN Guidelines
        with tabs[2]:
            if analysis['nccn_recommendations']:
                self._display_nccn_recommendations(analysis['nccn_recommendations'])
            else:
                st.info("NCCN recommendations not available for this cancer type or stage")
        
        # Tab 4: AI Analysis
        with tabs[3]:
            st.markdown("### 🤖 AI Clinical Reasoning")
            st.write(analysis['ai_clinical_reasoning'])
        
        # Tab 5: Risk Assessment
        with tabs[4]:
            if analysis['risk_stratification']:
                self._display_risk_assessment(analysis['risk_stratification'])
        
        # Tab 6: Follow-up Plan
        with tabs[5]:
            if analysis['follow_up_plan']:
                self._display_follow_up_plan(analysis['follow_up_plan'])
        
        # Export options
        st.subheader("📥 Export Results")
        self._render_export_options(analysis)
    
    def _display_patient_summary(self, summary: Dict[str, Any]):
        """Display patient summary."""
        st.markdown("### 👤 Patient Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Demographics:**")
            demo = summary['demographics']
            st.write(f"• Age: {demo['age']}")
            st.write(f"• Gender: {demo['gender']}")
            st.write(f"• Patient ID: {demo['patient_id']}")
        
        with col2:
            st.markdown("**Diagnosis:**")
            diag = summary['diagnosis']
            st.write(f"• Primary Cancer: {diag['primary_cancer']}")
            st.write(f"• Primary Site: {diag['primary_site']}")
            st.write(f"• Histology: {diag['histology']}")
        
        st.markdown("**Imaging Findings:**")
        imaging = summary['imaging_findings']
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"• Study Date: {imaging['study_date']}")
            st.write(f"• Tumor Size: {imaging['tumor_size']}")
        
        with col2:
            st.write(f"• SUV Max: {imaging['suv_max']}")
            st.write(f"• Lymph Nodes: {imaging['lymph_nodes']}")
        
        with col3:
            if imaging['metastases']:
                st.write("• Metastases:")
                for site in imaging['metastases']:
                    st.write(f"  - {site}")
            else:
                st.write("• Metastases: None specified")
    
    def _display_tnm_classification(self, tnm: Dict[str, Any]):
        """Display AJCC TNM classification."""
        st.markdown("### 🔬 AJCC TNM Classification (9th Edition)")
        
        # TNM Components
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("T Stage", tnm['tnm_normalized']['T'])
            st.caption(tnm['t_description'])
        
        with col2:
            st.metric("N Stage", tnm['tnm_normalized']['N'])
            st.caption(tnm['n_description'])
        
        with col3:
            st.metric("M Stage", tnm['tnm_normalized']['M'])
            st.caption(tnm['m_description'])
        
        with col4:
            st.metric("Overall Stage", tnm['overall_stage'])
        
        # Prognosis information
        if 'prognosis_info' in tnm:
            prognosis = self.ajcc_classifier.get_stage_prognosis(
                tnm['cancer_type'], 
                tnm['overall_stage']
            )
            
            st.markdown("**Prognostic Information:**")
            prog_info = prognosis['prognosis_info']
            st.info(f"**{prog_info['description']}** - {prog_info['prognosis']}")
            st.caption(f"General 5-year survival: {prog_info['5_year_survival']}")
            st.caption(prog_info.get('note', ''))
    
    def _display_nccn_recommendations(self, nccn: Dict[str, Any]):
        """Display NCCN treatment recommendations."""
        st.markdown("### 📚 NCCN Treatment Recommendations")
        
        st.info(f"**Cancer Type:** {nccn['cancer_type'].title()} | **Stage:** {nccn['stage']}")
        
        recommendations = nccn.get('recommendations', [])
        if recommendations:
            st.markdown("**Treatment Options:**")
            for i, rec in enumerate(recommendations, 1):
                st.write(f"{i}. {rec}")
        else:
            st.warning("No specific recommendations available for this stage.")
        
        st.caption(f"Source: {nccn['source']} | Last updated: {nccn['last_updated']}")
    
    def _display_risk_assessment(self, risk: Dict[str, Any]):
        """Display risk stratification."""
        st.markdown("### ⚠️ Risk Stratification")
        
        # Risk level
        risk_level = risk['risk_level']
        if risk_level == "High":
            st.error(f"🔴 **Risk Level:** {risk_level}")
        elif risk_level == "Intermediate-High":
            st.warning(f"🟠 **Risk Level:** {risk_level}")
        elif risk_level == "Intermediate":
            st.info(f"🟡 **Risk Level:** {risk_level}")
        else:
            st.success(f"🟢 **Risk Level:** {risk_level}")
        
        # Risk factors
        if risk['risk_factors']:
            st.markdown("**Risk Factors:**")
            for factor in risk['risk_factors']:
                st.write(f"• {factor}")
        else:
            st.write("No specific risk factors identified.")
    
    def _display_follow_up_plan(self, plan: Dict[str, Any]):
        """Display follow-up plan."""
        st.markdown("### 📅 Follow-up Plan")
        
        for section, items in plan.items():
            if items:
                section_title = section.replace('_', ' ').title()
                st.markdown(f"**{section_title}:**")
                for item in items:
                    st.write(f"• {item}")
                st.write("")
    
    def _render_export_options(self, analysis: Dict[str, Any]):
        """Render export options for analysis results."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Export PDF Report"):
                self._export_pdf_report(analysis)
        
        with col2:
            if st.button("📊 Export JSON Data"):
                self._export_json_data(analysis)
        
        with col3:
            if st.button("📧 Email Summary"):
                st.info("Email functionality would be implemented here")
    
    def _export_pdf_report(self, analysis: Dict[str, Any]):
        """Export comprehensive PDF report."""
        # This would integrate with a PDF generation library
        st.success("PDF export functionality would be implemented here")
    
    def _export_json_data(self, analysis: Dict[str, Any]):
        """Export analysis data as JSON."""
        json_data = json.dumps(analysis, indent=2, default=str)
        
        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name=f"medical_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def _render_navigation_buttons(self):
        """Render navigation buttons."""
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        current_step = st.session_state.pipeline_state['current_step']
        
        with col1:
            if current_step > 1:
                if st.button("← Previous Step"):
                    st.session_state.pipeline_state['current_step'] -= 1
                    st.rerun()
        
        with col3:
            if current_step < 3:
                if st.button("Next Step →"):
                    st.session_state.pipeline_state['current_step'] += 1
                    st.rerun()
        
        # Reset pipeline button
        with col2:
            if st.button("🔄 Reset Pipeline", help="Start over with new document"):
                st.session_state.pipeline_state = {
                    'current_step': 1,
                    'raw_extraction': None,
                    'verified_data': None,
                    'clinical_analysis': None
                }
                st.rerun()
    
    def _show_sample_extraction(self):
        """Show sample extraction format."""
        sample_data = {
            "patient_info": {
                "patient_id": "PT001234",
                "age": "65",
                "gender": "Male"
            },
            "cancer_info": {
                "cancer_type": "lung",
                "primary_site": "right upper lobe",
                "tumor_size": "3.2 x 2.8 cm"
            },
            "pet_findings": {
                "suv_max": "8.5",
                "metabolic_activity": "High"
            },
            "tnm_staging": {
                "t_stage": "T2a",
                "n_stage": "N1",
                "m_stage": "M0"
            }
        }
        
        st.json(sample_data)
