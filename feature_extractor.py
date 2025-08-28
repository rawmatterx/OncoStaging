"""
Medical feature extraction module for OncoStaging application.
Extracts medical features with validation and confidence scoring.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import streamlit as st

from config import (
    CANCER_TYPE_KEYWORDS, TNM_KEYWORDS, TUMOR_SIZE_RANGE,
    LYMPH_NODES_RANGE, CONFIDENCE_THRESHOLD, ERROR_MESSAGES
)
from exceptions import (
    FeatureExtractionError, MedicalDataValidationError,
    OncoStagingError
)

logger = logging.getLogger(__name__)


@dataclass
class MedicalFeatures:
    """Data class for medical features extracted from reports."""
    cancer_type: str = ""
    tumor_size_cm: float = 0.0
    lymph_nodes_involved: int = 0
    distant_metastasis: bool = False
    liver_invasion: bool = False
    tumor_depth: str = ""
    confidence_scores: Dict[str, float] = None
    extracted_values: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.confidence_scores is None:
            self.confidence_scores = {}
        if self.extracted_values is None:
            self.extracted_values = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def is_valid(self) -> bool:
        """Check if extracted features are valid for staging."""
        return bool(self.cancer_type) and self.tumor_size_cm >= 0


class FeatureExtractor:
    """Extracts medical features from clinical reports with confidence scoring."""
    
    def __init__(self):
        """Initialize the feature extractor."""
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for efficient matching."""
        return {
            # Tumor size patterns
            'tumor_size': re.compile(
                r'(?:tumor|mass|lesion|growth)[\s\w]*?'
                r'(?:measuring|measures|size|sized?)\s*'
                r'(?:approximately|approx\.?|about)?\s*'
                r'(\d+(?:\.\d+)?)\s*(?:x\s*\d+(?:\.\d+)?)*\s*(cm|mm)',
                re.IGNORECASE
            ),
            
            # Alternative size pattern
            'size_alt': re.compile(
                r'(\d+(?:\.\d+)?)\s*(cm|mm)\s*'
                r'(?:tumor|mass|lesion|nodule|growth)',
                re.IGNORECASE
            ),
            
            # Lymph node patterns
            'lymph_nodes': re.compile(
                r'(?:(?P<num>\d+)|multiple|several|numerous)\s*'
                r'(?:positive|involved|metastatic|malignant|enlarged)?\s*'
                r'(?:lymph\s*nodes?|nodes?|LN)',
                re.IGNORECASE
            ),
            
            # Metastasis patterns
            'metastasis': re.compile(
                r'(?:distant\s*)?(?:metastas[ei]s|metastatic\s*disease|'
                r'secondary\s*deposits?|disseminated)',
                re.IGNORECASE
            ),
            
            # Liver invasion patterns
            'liver_invasion': re.compile(
                r'(?:liver|hepatic)\s*(?:invasion|involvement|infiltration|'
                r'extension|involvement)|involving\s*(?:liver|segments?)',
                re.IGNORECASE
            ),
            
            # TNM patterns
            'tnm_staging': re.compile(
                r'[pPcC]?T[0-4][a-c]?\s*[pPcC]?N[0-3][a-c]?\s*[pPcC]?M[0-1][a-c]?',
                re.IGNORECASE
            )
        }
    
    def extract_cancer_type(self, text: str) -> Tuple[str, float]:
        """
        Extract cancer type from text with confidence score.
        
        Returns:
            Tuple of (cancer_type, confidence_score)
        """
        text_lower = text.lower()
        best_match = ""
        best_score = 0.0
        matches_found = []
        
        for cancer_type, keywords in CANCER_TYPE_KEYWORDS.items():
            score = 0.0
            keyword_matches = []
            
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    # Higher score for more specific keywords
                    keyword_score = len(keyword.split()) * 0.3
                    score += keyword_score
                    keyword_matches.append(keyword)
            
            if score > best_score:
                best_score = score
                best_match = cancer_type
                matches_found = keyword_matches
        
        # Normalize confidence score
        confidence = min(best_score / 3.0, 1.0) if best_score > 0 else 0.0
        
        if matches_found:
            logger.info(f"Cancer type detected: {best_match} (confidence: {confidence:.2f})")
            logger.debug(f"Matched keywords: {matches_found}")
        
        return best_match, confidence
    
    def extract_tumor_size(self, text: str) -> Tuple[float, float, List[str]]:
        """
        Extract tumor size from text with confidence score.
        
        Returns:
            Tuple of (size_cm, confidence_score, extracted_values)
        """
        sizes_found = []
        extracted_values = []
        
        # Try primary pattern
        for match in self.patterns['tumor_size'].finditer(text):
            size_value = float(match.group(1))
            unit = match.group(2).lower()
            
            if unit == 'mm':
                size_value /= 10  # Convert to cm
            
            sizes_found.append(size_value)
            extracted_values.append(match.group(0))
        
        # Try alternative pattern if no matches
        if not sizes_found:
            for match in self.patterns['size_alt'].finditer(text):
                size_value = float(match.group(1))
                unit = match.group(2).lower()
                
                if unit == 'mm':
                    size_value /= 10
                
                sizes_found.append(size_value)
                extracted_values.append(match.group(0))
        
        if sizes_found:
            # Take the largest size (worst case)
            tumor_size = max(sizes_found)
            
            # Validate size
            if TUMOR_SIZE_RANGE['min'] <= tumor_size <= TUMOR_SIZE_RANGE['max']:
                confidence = 0.9 if len(sizes_found) == 1 else 0.7
                logger.info(f"Tumor size: {tumor_size}cm (confidence: {confidence:.2f})")
                return tumor_size, confidence, extracted_values
            else:
                logger.warning(f"Tumor size out of range: {tumor_size}cm")
                return tumor_size, 0.3, extracted_values
        
        return 0.0, 0.0, []
    
    def extract_lymph_nodes(self, text: str) -> Tuple[int, float, List[str]]:
        """
        Extract lymph node involvement with confidence score.
        
        Returns:
            Tuple of (count, confidence_score, extracted_values)
        """
        node_counts = []
        extracted_values = []
        
        for match in self.patterns['lymph_nodes'].finditer(text):
            extracted_values.append(match.group(0))
            
            if match.group('num'):
                count = int(match.group('num'))
                node_counts.append(count)
            else:
                # Handle qualitative descriptions
                qualifier = match.group(0).lower()
                if 'multiple' in qualifier or 'numerous' in qualifier:
                    node_counts.append(5)  # Estimate
                elif 'several' in qualifier:
                    node_counts.append(3)  # Estimate
        
        if node_counts:
            # Take maximum count (worst case)
            total_nodes = max(node_counts)
            
            # Validate count
            if LYMPH_NODES_RANGE['min'] <= total_nodes <= LYMPH_NODES_RANGE['max']:
                confidence = 0.9 if all(isinstance(n, int) for n in node_counts) else 0.6
                logger.info(f"Lymph nodes: {total_nodes} (confidence: {confidence:.2f})")
                return total_nodes, confidence, extracted_values
            else:
                logger.warning(f"Lymph node count out of range: {total_nodes}")
                return total_nodes, 0.3, extracted_values
        
        return 0, 0.5, []  # Default confidence 0.5 if not found
    
    def extract_metastasis(self, text: str) -> Tuple[bool, float, List[str]]:
        """
        Extract distant metastasis information.
        
        Returns:
            Tuple of (has_metastasis, confidence_score, extracted_values)
        """
        matches = list(self.patterns['metastasis'].finditer(text))
        
        if matches:
            extracted_values = [m.group(0) for m in matches]
            
            # Check for negation
            has_metastasis = True
            for match in matches:
                # Look for negation within 50 characters before match
                start = max(0, match.start() - 50)
                context = text[start:match.start()].lower()
                
                if any(neg in context for neg in ['no ', 'without', 'negative', 'absent']):
                    has_metastasis = False
                    break
            
            confidence = 0.9 if has_metastasis else 0.8
            logger.info(f"Metastasis: {has_metastasis} (confidence: {confidence:.2f})")
            return has_metastasis, confidence, extracted_values
        
        return False, 0.6, []  # Default confidence 0.6 if not found
    
    def extract_liver_invasion(self, text: str) -> Tuple[bool, float, List[str]]:
        """
        Extract liver invasion information.
        
        Returns:
            Tuple of (has_invasion, confidence_score, extracted_values)
        """
        matches = list(self.patterns['liver_invasion'].finditer(text))
        
        if matches:
            extracted_values = [m.group(0) for m in matches]
            confidence = 0.9
            logger.info(f"Liver invasion detected (confidence: {confidence:.2f})")
            return True, confidence, extracted_values
        
        return False, 0.7, []
    
    def extract_tumor_depth(self, text: str) -> Tuple[str, float]:
        """
        Extract tumor depth information.
        
        Returns:
            Tuple of (depth, confidence_score)
        """
        text_lower = text.lower()
        depths_found = []
        
        for depth_keyword in TNM_KEYWORDS['tumor_depth']:
            if depth_keyword in text_lower:
                depths_found.append(depth_keyword)
        
        if depths_found:
            # Priority order for depth
            depth_priority = [
                'adventitia', 'serosa', 'subserosa', 
                'muscularis propria', 'muscularis', 
                'submucosa', 'mucosa'
            ]
            
            for depth in depth_priority:
                if depth in depths_found:
                    confidence = 0.9 if len(depths_found) == 1 else 0.7
                    logger.info(f"Tumor depth: {depth} (confidence: {confidence:.2f})")
                    return depth, confidence
        
        return "", 0.0
    
    def validate_features(self, features: MedicalFeatures) -> None:
        """
        Validate extracted medical features.
        
        Raises:
            MedicalDataValidationError: If validation fails
        """
        # Validate tumor size
        if features.tumor_size_cm < 0:
            raise MedicalDataValidationError("Tumor size cannot be negative")
        
        if features.tumor_size_cm > TUMOR_SIZE_RANGE['max']:
            raise MedicalDataValidationError(
                f"Tumor size exceeds maximum expected value ({TUMOR_SIZE_RANGE['max']}cm)"
            )
        
        # Validate lymph nodes
        if features.lymph_nodes_involved < 0:
            raise MedicalDataValidationError("Lymph node count cannot be negative")
        
        if features.lymph_nodes_involved > LYMPH_NODES_RANGE['max']:
            raise MedicalDataValidationError(
                f"Lymph node count exceeds maximum expected value ({LYMPH_NODES_RANGE['max']})"
            )
        
        # Check confidence scores
        min_confidence = min(features.confidence_scores.values()) if features.confidence_scores else 0
        if min_confidence < CONFIDENCE_THRESHOLD and not features.cancer_type:
            logger.warning("Low confidence in extracted features")
    
    @st.cache_data(ttl=3600)
    def extract_features(_self, text: str) -> MedicalFeatures:
        """
        Extract all medical features from text.
        
        Args:
            text: Clinical report text
            
        Returns:
            MedicalFeatures object with extracted data
            
        Raises:
            FeatureExtractionError: If extraction fails
        """
        try:
            features = MedicalFeatures()
            
            # Extract cancer type
            cancer_type, cancer_conf = _self.extract_cancer_type(text)
            features.cancer_type = cancer_type
            features.confidence_scores['cancer_type'] = cancer_conf
            
            # Extract tumor size
            size, size_conf, size_values = _self.extract_tumor_size(text)
            features.tumor_size_cm = size
            features.confidence_scores['tumor_size'] = size_conf
            features.extracted_values['tumor_size'] = size_values
            
            # Extract lymph nodes
            nodes, nodes_conf, nodes_values = _self.extract_lymph_nodes(text)
            features.lymph_nodes_involved = nodes
            features.confidence_scores['lymph_nodes'] = nodes_conf
            features.extracted_values['lymph_nodes'] = nodes_values
            
            # Extract metastasis
            mets, mets_conf, mets_values = _self.extract_metastasis(text)
            features.distant_metastasis = mets
            features.confidence_scores['metastasis'] = mets_conf
            features.extracted_values['metastasis'] = mets_values
            
            # Extract liver invasion
            liver, liver_conf, liver_values = _self.extract_liver_invasion(text)
            features.liver_invasion = liver
            features.confidence_scores['liver_invasion'] = liver_conf
            features.extracted_values['liver_invasion'] = liver_values
            
            # Extract tumor depth
            depth, depth_conf = _self.extract_tumor_depth(text)
            features.tumor_depth = depth
            features.confidence_scores['tumor_depth'] = depth_conf
            
            # Validate features
            _self.validate_features(features)
            
            logger.info("Feature extraction completed successfully")
            return features
            
        except OncoStagingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in feature extraction: {e}")
            raise FeatureExtractionError(ERROR_MESSAGES["extraction_error"])
    
    def get_feature_summary(self, features: MedicalFeatures) -> Dict[str, Any]:
        """Get summary of extracted features with confidence scores."""
        summary = {
            "cancer_type": {
                "value": features.cancer_type,
                "confidence": features.confidence_scores.get('cancer_type', 0)
            },
            "tumor_size_cm": {
                "value": features.tumor_size_cm,
                "confidence": features.confidence_scores.get('tumor_size', 0)
            },
            "lymph_nodes_involved": {
                "value": features.lymph_nodes_involved,
                "confidence": features.confidence_scores.get('lymph_nodes', 0)
            },
            "distant_metastasis": {
                "value": features.distant_metastasis,
                "confidence": features.confidence_scores.get('metastasis', 0)
            },
            "overall_confidence": sum(features.confidence_scores.values()) / len(features.confidence_scores)
            if features.confidence_scores else 0
        }
        
        return summary
