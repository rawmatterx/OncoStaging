"""
Feature extraction module for OncoStaging application.
Extracts medical features from text with validation and error handling.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from config import config_manager
from exceptions import FeatureExtractionError, MedicalDataValidationError


@dataclass
class MedicalFeatures:
    """Data class for extracted medical features."""
    cancer_type: str = ""
    tumor_size_cm: float = 0.0
    lymph_nodes_involved: int = 0
    distant_metastasis: bool = False
    liver_invasion: bool = False
    tumor_depth: str = ""
    confidence_score: float = 0.0
    extracted_terms: List[str] = None
    
    def __post_init__(self):
        if self.extracted_terms is None:
            self.extracted_terms = []


class FeatureExtractor:
    """Extracts medical features from text with comprehensive validation."""
    
    def __init__(self):
        self.config = config_manager.config
        self.logger = logging.getLogger(__name__)
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Setup regex patterns for feature extraction."""
        self.cancer_patterns = {
            "gallbladder": [
                r"gallbladder\s+(?:cancer|carcinoma|tumor|neoplasm)",
                r"cholangiocarcinoma",
                r"gb\s+(?:cancer|carcinoma)"
            ],
            "esophageal": [
                r"esophag(?:us|eal)\s+(?:cancer|carcinoma|tumor)",
                r"esophageal\s+adenocarcinoma",
                r"squamous\s+cell\s+carcinoma.*esophag"
            ],
            "breast": [
                r"breast\s+(?:cancer|carcinoma|tumor)",
                r"mammary\s+(?:cancer|carcinoma)",
                r"ductal\s+carcinoma.*breast",
                r"lobular\s+carcinoma.*breast"
            ],
            "lung": [
                r"lung\s+(?:cancer|carcinoma|tumor)",
                r"pulmonary\s+(?:cancer|carcinoma)",
                r"non-small\s+cell\s+lung\s+cancer",
                r"nsclc",
                r"small\s+cell\s+lung\s+cancer",
                r"sclc"
            ],
            "colorectal": [
                r"colon\s+(?:cancer|carcinoma|tumor)",
                r"rectal\s+(?:cancer|carcinoma|tumor)",
                r"colorectal\s+(?:cancer|carcinoma)",
                r"adenocarcinoma.*(?:colon|rectum)"
            ],
            "head_and_neck": [
                r"head\s+and\s+neck\s+(?:cancer|carcinoma)",
                r"oral\s+cavity\s+(?:cancer|carcinoma)",
                r"oropharyn(?:x|geal)\s+(?:cancer|carcinoma)",
                r"laryn(?:x|geal)\s+(?:cancer|carcinoma)"
            ]
        }
        
        self.size_patterns = [
            r"(?:tumor|mass|lesion)\s+(?:size|measuring|measures)\s+(?:approximately\s+)?(\d+(?:\.\d+)?)\s*(?:x\s*\d+(?:\.\d+)?\s*)?cm",
            r"(\d+(?:\.\d+)?)\s*cm\s+(?:tumor|mass|lesion)",
            r"(?:diameter|size).*?(\d+(?:\.\d+)?)\s*cm",
            r"tumor\s+measures\s+(\d+(?:\.\d+)?)\s*x\s*\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\s*cm",
            r"measures\s+(\d+(?:\.\d+)?)\s*x\s*\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\s*cm",
            r"(\d+(?:\.\d+)?)\s*x\s*\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\s*cm"
        ]
        
        self.lymph_node_patterns = [
            r"(\d+)\s+(?:lymph\s+)?nodes?\s+(?:involved|positive|enlarged)",
            r"(?:lymph\s+)?node\s+involvement.*?(\d+)",
            r"n(\d+)\s+disease",
            r"(\d+)\s+of\s+\d+\s+lymph\s+nodes\s+positive",
            r"(\d+)\s+lymph\s+nodes\s+(?:are\s+)?involved",
            r"(?:two|three|four|five|six|seven|eight|nine|ten)\s+lymph\s+nodes?\s+(?:involved|positive)"
        ]
        
        self.metastasis_patterns = [
            r"distant\s+metastas(?:is|es)",
            r"metastatic\s+disease",
            r"m1\s+disease",
            r"spread\s+to\s+(?:liver|lung|bone|brain)"
        ]
        
        self.liver_invasion_patterns = [
            r"liver\s+invasion",
            r"hepatic\s+invasion",
            r"invad(?:es|ing)\s+(?:the\s+)?liver"
        ]
    
    def extract_features(self, text: str) -> MedicalFeatures:
        """
        Extract medical features from text with comprehensive validation.
        
        Args:
            text: Input medical text
            
        Returns:
            MedicalFeatures: Extracted and validated features
            
        Raises:
            FeatureExtractionError: If feature extraction fails
        """
        try:
            if not text or not text.strip():
                raise FeatureExtractionError("Input text is empty")
            
            text_lower = text.lower()
            features = MedicalFeatures()
            
            # Extract cancer type
            features.cancer_type = self._extract_cancer_type(text_lower)
            
            # Extract tumor size
            features.tumor_size_cm = self._extract_tumor_size(text_lower)
            
            # Extract lymph node involvement
            features.lymph_nodes_involved = self._extract_lymph_nodes(text_lower)
            
            # Extract metastasis status
            features.distant_metastasis = self._extract_metastasis(text_lower)
            
            # Extract liver invasion
            features.liver_invasion = self._extract_liver_invasion(text_lower)
            
            # Extract tumor depth (basic implementation)
            features.tumor_depth = self._extract_tumor_depth(text_lower)
            
            # Calculate confidence score
            features.confidence_score = self._calculate_confidence(features, text_lower)
            
            # Validate extracted features
            self._validate_features(features)
            
            self.logger.info(f"Feature extraction successful: {features.cancer_type}")
            return features
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {str(e)}")
            if isinstance(e, (FeatureExtractionError, MedicalDataValidationError)):
                raise
            raise FeatureExtractionError(f"Failed to extract features: {str(e)}")
    
    def _extract_cancer_type(self, text: str) -> str:
        """Extract cancer type from text."""
        for cancer_type, patterns in self.cancer_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return cancer_type
        return ""
    
    def _extract_tumor_size(self, text: str) -> float:
        """Extract tumor size in centimeters."""
        for pattern in self.size_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    size = float(match.group(1))
                    return min(size, self.config.MAX_TUMOR_SIZE_CM)  # Cap at maximum
                except (ValueError, IndexError):
                    continue
        return 0.0
    
    def _extract_lymph_nodes(self, text: str) -> int:
        """Extract number of involved lymph nodes."""
        # First try numeric patterns
        for pattern in self.lymph_node_patterns[:-1]:  # Exclude text pattern
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    nodes = int(match.group(1))
                    return min(nodes, self.config.MAX_LYMPH_NODES)  # Cap at maximum
                except (ValueError, IndexError):
                    continue
        
        # Try text-based pattern
        text_pattern = self.lymph_node_patterns[-1]
        match = re.search(text_pattern, text, re.IGNORECASE)
        if match:
            word_to_num = {
                'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
            }
            word = match.group(0).split()[0].lower()
            return word_to_num.get(word, 0)
        
        return 0
    
    def _extract_metastasis(self, text: str) -> bool:
        """Extract distant metastasis status."""
        for pattern in self.metastasis_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _extract_liver_invasion(self, text: str) -> bool:
        """Extract liver invasion status."""
        for pattern in self.liver_invasion_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _extract_tumor_depth(self, text: str) -> str:
        """Extract tumor depth information."""
        depth_patterns = [
            r"(?:tumor|cancer)\s+(?:extends|invades)\s+(?:into|through)\s+(\w+)",
            r"(?:t\d+)\s+(?:tumor|disease)",
            r"(?:superficial|deep|invasive)\s+(?:tumor|cancer)"
        ]
        
        for pattern in depth_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return ""
    
    def _calculate_confidence(self, features: MedicalFeatures, text: str) -> float:
        """Calculate confidence score based on extracted features."""
        confidence = 0.0
        
        # Cancer type confidence
        if features.cancer_type:
            confidence += 0.3
        
        # Specific measurements increase confidence
        if features.tumor_size_cm > 0:
            confidence += 0.2
        
        if features.lymph_nodes_involved > 0:
            confidence += 0.2
        
        # Clear indicators increase confidence
        if features.distant_metastasis or features.liver_invasion:
            confidence += 0.1
        
        # Text quality indicators
        medical_terms = [
            "staging", "tnm", "grade", "histology", "pathology",
            "biopsy", "imaging", "ct", "pet", "mri"
        ]
        
        term_count = sum(1 for term in medical_terms if term in text.lower())
        confidence += min(term_count * 0.05, 0.2)
        
        return min(confidence, 1.0)
    
    def _validate_features(self, features: MedicalFeatures):
        """Validate extracted medical features."""
        # Validate tumor size
        if features.tumor_size_cm < 0:
            raise MedicalDataValidationError("Tumor size cannot be negative")
        
        if features.tumor_size_cm > self.config.MAX_TUMOR_SIZE_CM:
            raise MedicalDataValidationError(
                f"Tumor size ({features.tumor_size_cm}cm) exceeds maximum allowed "
                f"({self.config.MAX_TUMOR_SIZE_CM}cm)"
            )
        
        # Validate lymph nodes
        if features.lymph_nodes_involved < 0:
            raise MedicalDataValidationError("Lymph node count cannot be negative")
        
        if features.lymph_nodes_involved > self.config.MAX_LYMPH_NODES:
            raise MedicalDataValidationError(
                f"Lymph node count ({features.lymph_nodes_involved}) exceeds maximum allowed "
                f"({self.config.MAX_LYMPH_NODES})"
            )
        
        # Validate confidence score
        if not 0 <= features.confidence_score <= 1:
            raise MedicalDataValidationError("Confidence score must be between 0 and 1")
    
    def get_supported_cancer_types(self) -> List[str]:
        """Get list of supported cancer types."""
        return list(self.cancer_patterns.keys())