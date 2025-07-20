"""
OncoStaging - Cancer Staging Application (Refactored)

This module provides a Streamlit-based web interface for cancer staging
based on medical reports. It includes features for file upload, text extraction,
feature extraction, and TNM staging.
"""
import os
import sys
import streamlit as st
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Configure logging before other imports
from config.settings import config, init_config
from utils.logging_config import setup_logging, get_logger
from utils.file_utils import read_file_content
from feature_extractor import MedGemmaFeatureExtractor
from exceptions import (
    DocumentProcessingError, FileValidationError, 
    FeatureExtractionError, StagingError
)

# Initialize configuration and logging
init_config()
log_file = os.path.join(config.get("paths.logs_dir", "logs"), "oncostaging.log")
setup_logging(log_file=log_file)
logger = get_logger(__name__)

# Import staging functionality
try:
    from tnm_staging import determine_tnm_stage
except ImportError as e:
    logger.error(f"Failed to import staging module: {e}")
    raise

# Constants
SUPPORTED_CANCER_TYPES = [
    "Gallbladder",
    "Esophageal",
    "Breast",
    "Lung",
    "Colorectal",
    "Head and Neck",
    "Prostate",
    "Pancreatic",
    "Ovarian",
    "Liver"
]

class OncoStagingApp:
    """Main application class for OncoStaging."""
    
    def __init__(self):
        """Initialize the application."""
        self.setup_ui()
        
    def setup_ui(self):
        st.title("OncoStaging: Cancer Staging Chatbot")
        st.markdown("""
        Upload a PET/CT/biopsy report (PDF or DOCX) to extract cancer features, determine TNM stage, and receive treatment guidance.
        """)
        st.sidebar.header("Options")
        self.selected_cancer_type = st.sidebar.selectbox(
            "Select Cancer Type",
            SUPPORTED_CANCER_TYPES
        )
        self.show_summary = st.sidebar.checkbox("Show Summary", value=True)
        self.show_treatment = st.sidebar.checkbox("Show Treatment Advice", value=True)
        self.use_medgemma = st.sidebar.checkbox("Summarize Report with MedGemma AI", value=False)
        if self.use_medgemma:
            st.info("MedGemma AI will provide a summary and staging suggestion for your uploaded report.")
        self.medgemma_extractor = MedGemmaFeatureExtractor() if self.use_medgemma else None
    
    def run(self):
        """Run the main application loop."""
        try:
            self.handle_file_upload()
        except Exception as e:
            st.error(f"Application error: {e}")
            logger.exception("Application error")

    def handle_file_upload(self):
        uploaded_file = st.file_uploader(
            "Choose a PDF or DOCX report to analyze",
            type=["pdf", "docx"]
        )
        if uploaded_file is not None:
            try:
                file_content = self.process_uploaded_file(uploaded_file)
                if not file_content:
                    st.error("Could not extract text from the uploaded file.")
                    return
                st.success("File uploaded and processed successfully.")
                st.text_area("Extracted Report Text", file_content, height=200)
                if self.use_medgemma and self.medgemma_extractor is not None:
                    with st.spinner("Summarizing report with MedGemma AI..."):
                        try:
                            summary = self.medgemma_extractor.summarize_report(file_content)
                            st.markdown("**MedGemma AI Summary & Staging Suggestion:**")
                            st.info(summary)
                        except Exception as e:
                            st.error(f"MedGemma summarization error: {str(e)}")
                features = self.extract_features(file_content)
                self.show_staging_results(features)
            except (FileValidationError, DocumentProcessingError) as e:
                st.error(f"File processing error: {str(e)}")
            except FeatureExtractionError as e:
                st.error("❌ Error extracting features from the document.")
                logger.error(f"Feature extraction error: {e}")
            except StagingError as e:
                st.error("❌ Error determining cancer stage.")
                logger.error(f"Staging error: {e}")
            except Exception as e:
                st.error("❌ An unexpected error occurred. Please try again.")
                logger.exception("Unexpected error in file processing")
    
    def process_uploaded_file(self, uploaded_file) -> str:
        """Process the uploaded file and return its content."""
        logger.info(f"Processing uploaded file: {uploaded_file.name}")
        try:
            return read_file_content(uploaded_file)
        except Exception as e:
            logger.error(f"Error reading file content: {e}")
            raise DocumentProcessingError(str(e))
    
    def extract_features(self, text: str) -> Dict[str, Any]:
        """Extract relevant features from the text."""
        try:
            # Placeholder for actual feature extraction logic
            # This would call your NLP pipeline or regex-based extractor
            from tnm_staging import extract_features
            return extract_features(text)
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            raise FeatureExtractionError(str(e))
    
    def show_staging_results(self, features: Dict[str, Any]):
        """Display the staging results to the user."""
        try:
            cancer_type = features.get("cancer_type", self.selected_cancer_type)
            staging = determine_tnm_stage(cancer_type, features)
            st.subheader(f"Staging Results for {cancer_type.title()}")
            st.json(staging)
            if self.show_summary:
                self._show_summary(staging.get("Stage", "Unknown"), cancer_type)
            if self.show_treatment:
                self._show_treatment_advice(cancer_type, staging.get("Stage", "Unknown"))
        except Exception as e:
            st.error(f"Error displaying staging results: {e}")
            logger.error(f"Display error: {e}")
    
    def _show_summary(self, stage: str, cancer_type: str):
        st.markdown(f"**Summary for {cancer_type.title()} (Stage {stage}):**")
        st.write(f"This is a summary for {cancer_type.title()} cancer at stage {stage}.")
    
    def _show_treatment_advice(self, cancer_type: str, stage: str):
        st.markdown(f"**Treatment Advice for {cancer_type.title()} (Stage {stage}):**")
        st.write(f"This is a placeholder for treatment advice for {cancer_type.title()} cancer at stage {stage}.")

def main():
    """Main entry point for the application."""
    try:
        app = OncoStagingApp()
        app.run()
    except Exception as e:
        logger.error(f"Failed to start app: {e}")
        st.error(f"Failed to start app: {e}")

if __name__ == "__main__":
    main()
