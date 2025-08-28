"""
Refactored OncoStaging Application with MVC Architecture and AI Integration.
Main application file implementing Model-View-Controller pattern.
"""

import streamlit as st
import logging
import os
from typing import Dict, Any, Optional, List
import json
import csv
from datetime import datetime
from pathlib import Path

# Import modules
from config import (
    setup_logging, PAGE_TITLE, PAGE_ICON, SIDEBAR_STATE,
    ERROR_MESSAGES, SUCCESS_MESSAGES, FEEDBACK_CSV_FILE,
    TREATMENT_GUIDELINES_URLS, get_config
)
from exceptions import OncoStagingError
from document_processor import DocumentProcessor
from feature_extractor import FeatureExtractor, MedicalFeatures
from staging_engine import StagingEngine, TNMStaging
from ai_integration import MedicalAIAssistant, AIIntegrationError
from tnm_staging import determine_tnm_stage  # For backward compatibility

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class OncoStagingModel:
    """Model class handling business logic and data processing."""
    
    def __init__(self):
        """Initialize the model with necessary components."""
        self.document_processor = DocumentProcessor()
        self.feature_extractor = FeatureExtractor()
        self.staging_engine = StagingEngine()
        
        # Initialize AI assistant if API key is available
        self.ai_assistant = None
        if os.getenv("OPENROUTER_API_KEY"):
            try:
                self.ai_assistant = MedicalAIAssistant()
                logger.info("AI Assistant initialized successfully")
            except AIIntegrationError as e:
                logger.warning(f"AI Assistant initialization failed: {e}")
    
    def process_report(self, uploaded_file) -> Dict[str, Any]:
        """
        Process uploaded medical report through the pipeline.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Step 1: Process document
            doc_result = self.document_processor.process_document(uploaded_file)
            
            # Step 2: Extract features
            features = self.feature_extractor.extract_features(doc_result['text'])
            
            # Step 3: Calculate staging
            staging = self.staging_engine.calculate_staging(features)
            
            # Step 4: Get AI analysis if available
            ai_analysis = None
            if self.ai_assistant and features.cancer_type:
                try:
                    ai_response = self.ai_assistant.client.analyze_medical_report(
                        doc_result['text'],
                        features.to_dict(),
                        staging.to_dict()
                    )
                    ai_analysis = ai_response.content
                except Exception as e:
                    logger.error(f"AI analysis failed: {e}")
            
            return {
                'success': True,
                'document': doc_result,
                'features': features,
                'staging': staging,
                'ai_analysis': ai_analysis
            }
            
        except OncoStagingError as e:
            logger.error(f"Processing error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                'success': False,
                'error': ERROR_MESSAGES["processing_error"]
            }
    
    def get_treatment_info(self, cancer_type: str, stage: str) -> Dict[str, Any]:
        """
        Get treatment information for specific cancer and stage.
        
        Args:
            cancer_type: Type of cancer
            stage: Cancer stage
            
        Returns:
            Treatment information
        """
        treatment_info = {
            "guidelines_url": TREATMENT_GUIDELINES_URLS.get(cancer_type, ""),
            "ai_recommendations": None
        }
        
        # Get AI-powered recommendations if available
        if self.ai_assistant:
            try:
                recommendations = self.ai_assistant.get_treatment_recommendations(
                    cancer_type, stage
                )
                treatment_info["ai_recommendations"] = recommendations
            except Exception as e:
                logger.error(f"Failed to get AI recommendations: {e}")
        
        # Get standard treatment info (backward compatibility)
        treatment_info["standard_treatment"] = self._get_standard_treatment(cancer_type, stage)
        
        return treatment_info
    
    def _get_standard_treatment(self, cancer_type: str, stage: str) -> str:
        """Get standard treatment guidelines (legacy support)."""
        # Treatment dictionary from original app
        treatment_dict = {
            "gallbladder": {
                "I": "Surgical resection (simple cholecystectomy or wedge resection).",
                "II": "Extended cholecystectomy with lymph node dissection.",
                "III": "Surgical resection ± adjuvant chemoradiotherapy.",
                "IV": "Systemic chemotherapy (e.g., gemcitabine + cisplatin)."
            },
            "esophageal": {
                "I": "Endoscopic mucosal resection or esophagectomy.",
                "II": "Neoadjuvant chemoradiotherapy followed by surgery.",
                "III": "Definitive chemoradiation or surgery after neoadjuvant therapy.",
                "IV": "Systemic therapy or palliative RT/stent placement."
            },
            "breast": {
                "I": "Surgery (BCS or mastectomy) ± adjuvant RT.",
                "II": "Surgery + chemo/hormonal therapy + radiation.",
                "III": "Neoadjuvant chemotherapy → surgery + adjuvant therapy.",
                "IV": "Systemic therapy based on biomarkers."
            },
            "lung": {
                "I": "Surgical resection ± adjuvant chemo.",
                "II": "Surgery + chemo ± radiation.",
                "III": "Concurrent chemoradiotherapy ± immunotherapy.",
                "IV": "Targeted therapy, immunotherapy, or chemo."
            },
            "colorectal": {
                "I": "Surgical resection (segmental colectomy).",
                "II": "Surgery ± adjuvant chemo (if high-risk).",
                "III": "Surgery + adjuvant FOLFOX or CAPOX.",
                "IV": "Systemic therapy ± targeted therapy."
            },
            "head and neck": {
                "I": "Surgery or radiation alone.",
                "II": "Surgery ± adjuvant RT.",
                "III": "Surgery + RT/chemo or concurrent chemoradiation.",
                "IV": "Systemic therapy ± RT. Consider immunotherapy."
            }
        }
        
        # Determine stage group
        if stage.startswith("Stage I") and "V" not in stage:
            stage_group = "I"
        elif "II" in stage:
            stage_group = "II"
        elif "III" in stage:
            stage_group = "III"
        elif "IV" in stage:
            stage_group = "IV"
        else:
            return "Treatment information not available."
        
        return treatment_dict.get(cancer_type, {}).get(stage_group, "Treatment information not available.")
    
    def save_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """
        Save user feedback to CSV file.
        
        Args:
            feedback_data: Feedback data dictionary
            
        Returns:
            Success status
        """
        try:
            file_exists = os.path.isfile(FEEDBACK_CSV_FILE)
            
            with open(FEEDBACK_CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
                fieldnames = ['timestamp', 'helpful', 'anxiety', 'stage', 'cancer_type', 'ai_used']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                feedback_data['timestamp'] = datetime.now().isoformat()
                feedback_data['ai_used'] = self.ai_assistant is not None
                writer.writerow(feedback_data)
            
            logger.info("Feedback saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
            return False
    
    def answer_question(self, question: str, context: Dict[str, Any]) -> str:
        """
        Answer user question using AI or predefined responses.
        
        Args:
            question: User's question
            context: Medical context
            
        Returns:
            Answer string
        """
        # Try AI assistant first
        if self.ai_assistant:
            try:
                response = self.ai_assistant.client.answer_patient_question(
                    question, context
                )
                return response.content
            except Exception as e:
                logger.error(f"AI question answering failed: {e}")
        
        # Fallback to predefined responses
        return self._get_predefined_answer(question, context)
    
    def _get_predefined_answer(self, question: str, context: Dict[str, Any]) -> str:
        """Get predefined answer for common questions."""
        stage = context.get('stage', 'Unknown')
        cancer_type = context.get('cancer_type', 'unknown')
        
        if "stage" in question.lower():
            return f"Your cancer is at **{stage}** stage."
        elif "treatment" in question.lower():
            treatment = self._get_standard_treatment(cancer_type, stage)
            return f"Standard treatment: {treatment}"
        elif "mean" in question.lower() or "simple" in question.lower():
            return self._generate_simple_explanation(stage, cancer_type)
        else:
            return "More information is needed to answer this question. Please consult your doctor."
    
    def _generate_simple_explanation(self, stage: str, cancer_type: str) -> str:
        """Generate simple explanation of staging."""
        msg = f"According to your report, this is **{stage} {cancer_type} cancer**.\n\n"
        
        if "IV" in stage:
            msg += "This indicates advanced disease that has spread to distant organs.\n"
        elif "III" in stage:
            msg += "This is a locally advanced stage.\n"
        elif "II" in stage:
            msg += "This is an early regional stage.\n"
        else:
            msg += "This appears to be an early stage disease.\n"
        
        msg += "\n⚠️ Please consult your oncologist for final medical decisions."
        return msg


class OncoStagingView:
    """View class handling UI rendering and user interactions."""
    
    def __init__(self):
        """Initialize the view."""
        self.setup_page()
    
    def setup_page(self):
        """Setup Streamlit page configuration."""
        st.set_page_config(
            page_title=PAGE_TITLE,
            page_icon=PAGE_ICON,
            layout="wide",
            initial_sidebar_state=SIDEBAR_STATE
        )
    
    def render_header(self):
        """Render application header."""
        col1, col2 = st.columns([5, 1])
        with col1:
            st.title(PAGE_TITLE)
            st.markdown("Upload your PET/CT report and get AI-assisted analysis. 🤖")
        with col2:
            if st.button("ℹ️ Help"):
                self.show_help()
    
    def show_help(self):
        """Show help information."""
        with st.expander("How to Use", expanded=True):
            st.markdown("""
            ### OncoStaging User Guide:
            
            1. **📤 File Upload**: Upload your PET/CT report (PDF or DOCX)
            2. **🔍 Analysis**: System will automatically analyze the report
            3. **📊 Results**: View TNM staging and detailed information
            4. **🤖 AI Assistance**: Ask questions and get AI-powered answers
            5. **💬 Feedback**: Share your experience
            
            **Note**: This is for informational purposes only. Consult your doctor for medical decisions.
            """)
    
    def render_sidebar(self, ai_available: bool):
        """Render sidebar with options and info."""
        with st.sidebar:
            st.header("⚙️ Settings")
            
            # AI Status
            if ai_available:
                st.success("✅ AI Assistant Active")
                
                # Model selection
                model = st.selectbox(
                    "Select AI Model",
                    ["deepseek-chat", "gemma-7b", "gemma-2b", "llama-3-8b", "mistral-7b"],
                    help="Free models are marked with ':free'"
                )
                st.session_state['selected_model'] = model
            else:
                st.warning("⚠️ AI Assistant Inactive")
                st.info("Set OPENROUTER_API_KEY to activate AI")
            
            # Configuration info
            st.header("📋 Configuration")
            config = get_config()
            st.json(config)
            
            # Cache stats
            if st.button("🗑️ Clear Cache"):
                st.cache_data.clear()
                st.success("Cache cleared!")
    
    def render_file_uploader(self) -> Any:
        """Render file upload widget."""
        return st.file_uploader(
            "📤 Upload PET/CT Report (.pdf or .docx)",
            type=["pdf", "docx"],
            help="Maximum file size: 50MB"
        )
    
    def render_processing_results(self, results: Dict[str, Any]):
        """Render processing results."""
        if not results['success']:
            st.error(f"❌ {results['error']}")
            return
        
        st.success(SUCCESS_MESSAGES["processing_complete"])
        
        # Create tabs for different sections
        tabs = st.tabs(["📊 TNM Staging", "🧠 Extracted Features", "🤖 AI Analysis", "📄 Report Summary"])
        
        with tabs[0]:
            self.render_staging_results(results['staging'])
        
        with tabs[1]:
            self.render_extracted_features(results['features'])
        
        with tabs[2]:
            self.render_ai_analysis(results.get('ai_analysis'))
        
        with tabs[3]:
            self.render_report_summary(results)
    
    def render_staging_results(self, staging: TNMStaging):
        """Render TNM staging results."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("T (Tumor)", staging.T)
        with col2:
            st.metric("N (Nodes)", staging.N)
        with col3:
            st.metric("M (Metastasis)", staging.M)
        with col4:
            st.metric("Overall Stage", staging.get_full_stage())
        
        st.info(f"**ব্যাখ্যা**: {staging.description}")
    
    def render_extracted_features(self, features: MedicalFeatures):
        """Render extracted medical features."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Medical Information")
            st.write(f"**Cancer Type**: {features.cancer_type or 'Not identified'}")
            st.write(f"**Tumor Size**: {features.tumor_size_cm} cm")
            st.write(f"**Lymph Nodes**: {features.lymph_nodes_involved}")
            st.write(f"**Metastasis**: {'Yes' if features.distant_metastasis else 'No'}")
        
        with col2:
            st.subheader("Confidence Scores")
            for feature, score in features.confidence_scores.items():
                progress = st.progress(score)
                st.caption(f"{feature}: {score:.0%}")
    
    def render_ai_analysis(self, ai_analysis: Optional[str]):
        """Render AI analysis section."""
        if ai_analysis:
            st.markdown("### 🤖 AI Analysis")
            st.write(ai_analysis)
        else:
            st.info("AI analysis not available. Set API key or try again later.")
    
    def render_report_summary(self, results: Dict[str, Any]):
        """Render downloadable report summary."""
        features = results['features']
        staging = results['staging']
        
        summary = f"""OncoStaging Report Summary
========================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Cancer Type: {features.cancer_type}
Tumor Size: {features.tumor_size_cm} cm
Lymph Nodes: {features.lymph_nodes_involved}
Metastasis: {'Yes' if features.distant_metastasis else 'No'}

TNM Staging:
- T: {staging.T}
- N: {staging.N}
- M: {staging.M}
- Overall Stage: {staging.get_full_stage()}

Description: {staging.description}

⚠️ This is for informational purposes only. Please consult your oncologist for treatment decisions.
"""
        
        st.download_button(
            label="📥 Download Summary",
            data=summary,
            file_name=f"oncostaging_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    
    def render_qa_section(self, context: Dict[str, Any]):
        """Render Q&A section."""
        st.header("💬 Ask Questions")
        
        # Predefined questions
        questions = [
            "🧾 What is my cancer stage?",
            "💊 What treatment is usually given?",
            "🧠 What does this mean in simple terms?",
            "📋 What are the next steps?",
            "🤔 Ask your own question..."
        ]
        
        selected_q = st.radio("Select a question:", questions)
        
        if selected_q == "🤔 Ask your own question...":
            custom_q = st.text_input("Write your question:")
            if custom_q:
                selected_q = custom_q
        
        if st.button("Get Answer", type="primary"):
            return selected_q
        
        return None
    
    def render_feedback_section(self):
        """Render feedback section."""
        st.header("📝 Feedback")
        
        col1, col2 = st.columns(2)
        
        with col1:
            helpful = st.radio(
                "Was this analysis helpful?",
                ["👍 Yes", "👎 No"],
                key="helpful"
            )
        
        with col2:
            anxiety = st.radio(
                "After reading this information, your anxiety:",
                ["📈 Increased", "📉 Decreased", "➡️ Same"],
                key="anxiety"
            )
        
        if st.button("Submit Feedback"):
            return {
                'helpful': helpful,
                'anxiety': anxiety
            }
        
        return None
    
    def show_error(self, message: str):
        """Show error message."""
        st.error(f"❌ {message}")
    
    def show_success(self, message: str):
        """Show success message."""
        st.success(f"✅ {message}")
    
    def show_info(self, message: str):
        """Show info message."""
        st.info(f"ℹ️ {message}")


class OncoStagingController:
    """Controller class coordinating between Model and View."""
    
    def __init__(self):
        """Initialize the controller."""
        self.model = OncoStagingModel()
        self.view = OncoStagingView()
        
        # Initialize session state
        if 'processing_results' not in st.session_state:
            st.session_state.processing_results = None
        if 'selected_model' not in st.session_state:
            st.session_state.selected_model = "gemma-7b"
    
    def run(self):
        """Run the main application."""
        try:
            # Render UI components
            self.view.render_header()
            self.view.render_sidebar(self.model.ai_assistant is not None)
            
            # File upload section
            uploaded_file = self.view.render_file_uploader()
            
            if uploaded_file is not None:
                # Process the file
                with st.spinner("🔍 Analyzing report..."):
                    results = self.model.process_report(uploaded_file)
                    st.session_state.processing_results = results
                
                # Display results
                if results['success']:
                    self.view.render_processing_results(results)
                    
                    # Q&A Section
                    if results['features'].cancer_type:
                        context = {
                            'cancer_type': results['features'].cancer_type,
                            'stage': results['staging'].get_full_stage(),
                            'features': results['features'].to_dict(),
                            'staging': results['staging'].to_dict()
                        }
                        
                        question = self.view.render_qa_section(context)
                        if question:
                            with st.spinner("Finding answer..."):
                                answer = self.model.answer_question(question, context)
                                st.markdown("### Answer:")
                                st.write(answer)
                    
                    # Feedback Section
                    feedback = self.view.render_feedback_section()
                    if feedback:
                        feedback['stage'] = results['staging'].get_full_stage()
                        feedback['cancer_type'] = results['features'].cancer_type
                        
                        if self.model.save_feedback(feedback):
                            self.view.show_success(SUCCESS_MESSAGES["feedback_submitted"])
                        else:
                            self.view.show_error("Failed to save feedback")
                else:
                    self.view.show_error(results['error'])
            
            # Show placeholder when no file is uploaded
            else:
                self.show_placeholder()
        
        except Exception as e:
            logger.error(f"Application error: {e}")
            self.view.show_error("Application error occurred. Please try again.")
    
    def show_placeholder(self):
        """Show placeholder content when no file is uploaded."""
        st.markdown("""
        ### 🏥 Welcome to OncoStaging!
        
        This application helps you:
        - 📊 Determine TNM staging from PET/CT reports
        - 🤖 Get AI-powered analysis
        - 💊 Learn about treatment information
        - 📚 Understand medical terms in simple language
        
        **Upload your report above to get started.**
        """)
        
        # Show sample analysis if available
        if st.button("🔍 View Sample Analysis"):
            self.show_sample_analysis()
    
    def show_sample_analysis(self):
        """Show sample analysis for demonstration."""
        st.info("Sample Analysis (For Demo Purpose)")
        
        sample_features = MedicalFeatures(
            cancer_type="breast",
            tumor_size_cm=2.5,
            lymph_nodes_involved=2,
            distant_metastasis=False
        )
        
        sample_staging = TNMStaging(
            T="T2",
            N="N1",
            M="M0",
            stage="Stage II",
            description="Moderate-sized tumor with limited lymph node involvement"
        )
        
        results = {
            'success': True,
            'features': sample_features,
            'staging': sample_staging,
            'ai_analysis': "This is a sample analysis. Upload a file for actual report analysis."
        }
        
        self.view.render_processing_results(results)


def main():
    """Main entry point of the application."""
    controller = OncoStagingController()
    controller.run()


if __name__ == "__main__":
    main()
