"""
Refactored OncoStaging application with improved architecture.
Implements MVC pattern with proper separation of concerns.
"""

import streamlit as st
import logging
import csv
import os
from typing import Optional, Dict, Any

from config import config_manager
from document_processor import DocumentProcessor
from feature_extractor import FeatureExtractor, MedicalFeatures
from staging_engine import StagingEngine, TNMStaging
from exceptions import (
    OncoStagingError, DocumentProcessingError, 
    FeatureExtractionError, StagingError
)


class OncoStagingController:
    """Main controller for the OncoStaging application."""
    
    def __init__(self):
        self.config = config_manager.config
        self.document_processor = DocumentProcessor()
        self.feature_extractor = FeatureExtractor()
        self.staging_engine = StagingEngine()
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup application logging."""
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
    
    def process_document(self, uploaded_file) -> Optional[str]:
        """Process uploaded document and extract text."""
        try:
            text = self.document_processor.extract_text(uploaded_file)
            self.logger.info(f"Document processed successfully: {uploaded_file.name}")
            return text
        except (DocumentProcessingError, Exception) as e:
            self.logger.error(f"Document processing failed: {str(e)}")
            st.error(f"❌ Document processing failed: {str(e)}")
            return None
    
    def extract_features(self, text: str) -> Optional[MedicalFeatures]:
        """Extract medical features from text."""
        try:
            features = self.feature_extractor.extract_features(text)
            self.logger.info(f"Features extracted: {features.cancer_type}")
            return features
        except (FeatureExtractionError, Exception) as e:
            self.logger.error(f"Feature extraction failed: {str(e)}")
            st.error(f"❌ Feature extraction failed: {str(e)}")
            return None
    
    def determine_staging(self, cancer_type: str, features: MedicalFeatures) -> Optional[TNMStaging]:
        """Determine cancer staging."""
        try:
            staging = self.staging_engine.determine_stage(cancer_type, features)
            self.logger.info(f"Staging determined: {staging.Stage}")
            return staging
        except (StagingError, Exception) as e:
            self.logger.error(f"Staging failed: {str(e)}")
            st.error(f"❌ Staging failed: {str(e)}")
            return None


class OncoStagingView:
    """View layer for the OncoStaging application."""
    
    def __init__(self, controller: OncoStagingController):
        self.controller = controller
        self.config = config_manager.config
    
    def setup_page(self):
        """Setup Streamlit page configuration."""
        st.set_page_config(
            page_title=self.config.PAGE_TITLE,
            page_icon=self.config.PAGE_ICON,
            layout="centered"
        )
        
        st.title(f"{self.config.PAGE_ICON} {self.config.PAGE_TITLE}")
        st.markdown("Upload your PET/CT report to get a staging summary and ask questions.")
        
        # Add information about supported cancer types
        with st.expander("ℹ️ Supported Cancer Types"):
            cancer_types = self.controller.staging_engine.get_supported_cancer_types()
            formatted_types = [ct.replace("_", " ").title() for ct in cancer_types]
            st.write("• " + "\n• ".join(formatted_types))
    
    def render_file_upload(self):
        """Render file upload widget."""
        allowed_types = self.config.ALLOWED_EXTENSIONS
        max_size = self.config.MAX_FILE_SIZE_MB
        
        st.markdown(f"**📤 Upload PET/CT Report**")
        st.markdown(f"*Supported formats: {', '.join(allowed_types)} (max {max_size}MB)*")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=allowed_types,
            help=f"Upload medical reports in PDF or DOCX format (max {max_size}MB)"
        )
        
        return uploaded_file
    
    def run(self):
        """Main application entry point."""
        self.setup_page()
        
        # File upload section
        uploaded_file = self.render_file_upload()
        
        if uploaded_file is not None:
            # Process document
            with st.spinner("🔄 Processing document..."):
                text = self.controller.process_document(uploaded_file)
            
            if text:
                st.success("✅ Document processed successfully!")
                
                # Extract features
                with st.spinner("🧠 Extracting medical features..."):
                    features = self.controller.extract_features(text)
                
                if features and features.cancer_type:
                    # Display extracted features
                    self.render_features_display(features)
                    
                    # Determine staging
                    with st.spinner("📊 Determining cancer staging..."):
                        staging = self.controller.determine_staging(features.cancer_type, features)
                    
                    if staging:
                        self.render_staging_results(staging, features.cancer_type)
                        self.render_feedback_section()
                else:
                    st.warning("⚠️ Could not extract sufficient medical information from the document.")
    
    def render_features_display(self, features: MedicalFeatures):
        """Render extracted features display."""
        st.subheader("🧠 Extracted Features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Cancer Type", features.cancer_type.title() if features.cancer_type else "Unknown")
            st.metric("Tumor Size (cm)", f"{features.tumor_size_cm:.1f}" if features.tumor_size_cm > 0 else "Not specified")
            st.metric("Lymph Nodes Involved", features.lymph_nodes_involved)
        
        with col2:
            st.metric("Distant Metastasis", "Yes" if features.distant_metastasis else "No")
            st.metric("Liver Invasion", "Yes" if features.liver_invasion else "No")
            st.metric("Confidence Score", f"{features.confidence_score:.2f}")
    
    def render_staging_results(self, staging: TNMStaging, cancer_type: str):
        """Render staging results."""
        st.subheader("📊 TNM Staging Results")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("T (Tumor)", staging.T)
        with col2:
            st.metric("N (Nodes)", staging.N)
        with col3:
            st.metric("M (Metastasis)", staging.M)
        with col4:
            st.metric("Overall Stage", staging.Stage)
        
        # Display confidence and guidelines
        st.info(f"**Confidence:** {staging.confidence:.2f} | **Guidelines:** [NCCN]({staging.guidelines_url})")
        
        # Generate summary
        summary = self.generate_summary(staging, cancer_type)
        st.markdown(summary)
    
    def generate_summary(self, staging: TNMStaging, cancer_type: str) -> str:
        """Generate staging summary."""
        stage = staging.Stage
        msg = f"Based on the report, this appears to be **{stage} {cancer_type.capitalize()} Cancer**.\n\n"
        
        if "IV" in stage:
            msg += "This indicates advanced disease with distant spread.\n"
        elif "III" in stage:
            msg += "This is a locally advanced stage.\n"
        elif "II" in stage:
            msg += "This is an early regional stage.\n"
        else:
            msg += "This appears to be an early stage disease.\n"
        
        msg += f"\n**Confidence Score:** {staging.confidence:.2f}\n"
        msg += "\n⚠️ Please consult your oncologist before making any treatment decisions."
        return msg
    
    def render_feedback_section(self):
        """Render user feedback section."""
        st.subheader("💬 Feedback")
        
        col1, col2 = st.columns(2)
        with col1:
            helpful = st.radio("Was this helpful?", ["Yes", "No", "Partially"])
        with col2:
            anxiety = st.radio("Did this reduce your anxiety?", ["Yes", "No", "Neutral"])
        
        if st.button("Submit Feedback"):
            self.controller.log_feedback(helpful, anxiety)
            st.success("Thank you for your feedback!")


def main():
    """Main application entry point."""
    try:
        controller = OncoStagingController()
        view = OncoStagingView(controller)
        view.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please refresh the page and try again.")


if __name__ == "__main__":
    main()