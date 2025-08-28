"""
TNM staging engine for OncoStaging application.
Implements TNM staging algorithms with cancer-specific stagers.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import streamlit as st

from config import ERROR_MESSAGES
from exceptions import StagingError, OncoStagingError
from feature_extractor import MedicalFeatures

logger = logging.getLogger(__name__)


@dataclass
class TNMStaging:
    """Data class for TNM staging results."""
    T: str = "Tx"
    N: str = "Nx"
    M: str = "Mx"
    stage: str = "Unknown"
    substage: str = ""
    description: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)
    
    def get_full_stage(self) -> str:
        """Get full stage with substage."""
        if self.substage:
            return f"{self.stage}{self.substage}"
        return self.stage


class CancerStager(ABC):
    """Abstract base class for cancer-specific staging."""
    
    @abstractmethod
    def stage(self, features: MedicalFeatures) -> TNMStaging:
        """Calculate TNM staging for specific cancer type."""
        pass
    
    @abstractmethod
    def get_stage_description(self, staging: TNMStaging) -> str:
        """Get description for the staging."""
        pass


class GallbladderCancerStager(CancerStager):
    """Staging logic for gallbladder cancer."""
    
    def stage(self, features: MedicalFeatures) -> TNMStaging:
        """Calculate TNM staging for gallbladder cancer."""
        staging = TNMStaging()
        
        # Determine T stage
        if features.liver_invasion:
            staging.T = "T3"
        elif features.tumor_size_cm > 2:
            staging.T = "T2"
        elif features.tumor_size_cm > 0:
            staging.T = "T1"
        else:
            staging.T = "Tx"
        
        # Determine N stage
        if features.lymph_nodes_involved == 0:
            staging.N = "N0"
        elif 1 <= features.lymph_nodes_involved <= 3:
            staging.N = "N1"
        elif features.lymph_nodes_involved > 3:
            staging.N = "N2"
        else:
            staging.N = "Nx"
        
        # Determine M stage
        staging.M = "M1" if features.distant_metastasis else "M0"
        
        # Calculate overall stage
        if staging.M == "M1":
            staging.stage = "Stage IV"
            staging.substage = "B"
        elif staging.T == "T3" and staging.N != "N0":
            staging.stage = "Stage IV"
            staging.substage = "A"
        elif staging.T == "T3":
            staging.stage = "Stage III"
            staging.substage = "B"
        elif staging.T == "T2" and staging.N == "N0":
            staging.stage = "Stage II"
        elif staging.T in ["T1", "T2"] and staging.N != "N0":
            staging.stage = "Stage III"
            staging.substage = "A"
        elif staging.T == "T1" and staging.N == "N0":
            staging.stage = "Stage I"
        else:
            staging.stage = "Stage Unknown"
        
        staging.description = self.get_stage_description(staging)
        return staging
    
    def get_stage_description(self, staging: TNMStaging) -> str:
        """Get description for gallbladder cancer staging."""
        descriptions = {
            "Stage I": "Early stage cancer confined to gallbladder wall",
            "Stage II": "Tumor has reached outer layer of gallbladder",
            "Stage IIIA": "Tumor has spread to nearby lymph nodes",
            "Stage IIIB": "Tumor has invaded liver or nearby organs",
            "Stage IVA": "Tumor has spread to major blood vessels or multiple organs",
            "Stage IVB": "Advanced cancer with distant metastasis"
        }
        
        full_stage = staging.get_full_stage()
        return descriptions.get(full_stage, "Staging information not available")


class EsophagealCancerStager(CancerStager):
    """Staging logic for esophageal cancer."""
    
    def stage(self, features: MedicalFeatures) -> TNMStaging:
        """Calculate TNM staging for esophageal cancer."""
        staging = TNMStaging()
        
        # Determine T stage based on depth
        depth_to_t = {
            "mucosa": "T1a",
            "submucosa": "T1b",
            "muscularis": "T2",
            "adventitia": "T3",
            "adjacent structures": "T4"
        }
        
        staging.T = depth_to_t.get(features.tumor_depth.lower(), "Tx")
        
        # Determine N stage
        if features.lymph_nodes_involved == 0:
            staging.N = "N0"
        elif 1 <= features.lymph_nodes_involved <= 2:
            staging.N = "N1"
        elif 3 <= features.lymph_nodes_involved <= 6:
            staging.N = "N2"
        elif features.lymph_nodes_involved > 6:
            staging.N = "N3"
        else:
            staging.N = "Nx"
        
        # Determine M stage
        staging.M = "M1" if features.distant_metastasis else "M0"
        
        # Calculate overall stage
        if staging.M == "M1":
            staging.stage = "Stage IV"
            staging.substage = "B"
        elif staging.T == "T4" or staging.N == "N3":
            staging.stage = "Stage IV"
            staging.substage = "A"
        elif staging.T in ["T2", "T3"] and staging.N in ["N0", "N1"]:
            staging.stage = "Stage II"
        elif staging.T == "T1" and staging.N == "N0":
            staging.stage = "Stage I"
        else:
            staging.stage = "Stage III"
        
        staging.description = self.get_stage_description(staging)
        return staging
    
    def get_stage_description(self, staging: TNMStaging) -> str:
        """Get description for esophageal cancer staging."""
        descriptions = {
            "Stage I": "Early stage confined to inner layer of esophagus",
            "Stage II": "Tumor has reached deeper layers of esophagus",
            "Stage III": "Spread to nearby lymph nodes",
            "Stage IVA": "Invaded nearby organs",
            "Stage IVB": "Metastasis to distant organs"
        }
        
        full_stage = staging.get_full_stage()
        return descriptions.get(full_stage, staging.stage)


class BreastCancerStager(CancerStager):
    """Staging logic for breast cancer."""
    
    def stage(self, features: MedicalFeatures) -> TNMStaging:
        """Calculate TNM staging for breast cancer."""
        staging = TNMStaging()
        
        # Determine T stage
        if features.tumor_size_cm <= 2:
            staging.T = "T1"
        elif features.tumor_size_cm <= 5:
            staging.T = "T2"
        elif features.tumor_size_cm > 5:
            staging.T = "T3"
        else:
            staging.T = "Tx"
        
        # Determine N stage
        if features.lymph_nodes_involved == 0:
            staging.N = "N0"
        elif features.lymph_nodes_involved <= 3:
            staging.N = "N1"
        elif features.lymph_nodes_involved <= 9:
            staging.N = "N2"
        elif features.lymph_nodes_involved > 9:
            staging.N = "N3"
        else:
            staging.N = "Nx"
        
        # Determine M stage
        staging.M = "M1" if features.distant_metastasis else "M0"
        
        # Calculate overall stage
        if staging.M == "M1":
            staging.stage = "Stage IV"
        elif staging.T == "T1" and staging.N == "N0":
            staging.stage = "Stage I"
        elif staging.T in ["T1", "T2"] and staging.N == "N1":
            staging.stage = "Stage II"
        elif staging.T == "T3" or staging.N in ["N2", "N3"]:
            staging.stage = "Stage III"
        else:
            staging.stage = "Stage Unknown"
        
        staging.description = self.get_stage_description(staging)
        return staging
    
    def get_stage_description(self, staging: TNMStaging) -> str:
        """Get description for breast cancer staging."""
        descriptions = {
            "Stage I": "Early stage, small tumor, no lymph node spread",
            "Stage II": "Moderate-sized tumor or limited lymph node involvement",
            "Stage III": "Large tumor or extensive lymph node involvement",
            "Stage IV": "Metastasis to distant organs"
        }
        
        return descriptions.get(staging.stage, "Staging information not available")


class LungCancerStager(CancerStager):
    """Staging logic for lung cancer."""
    
    def stage(self, features: MedicalFeatures) -> TNMStaging:
        """Calculate TNM staging for lung cancer."""
        staging = TNMStaging()
        
        # Determine T stage
        if features.tumor_size_cm <= 3:
            staging.T = "T1"
        elif features.tumor_size_cm <= 5:
            staging.T = "T2"
        elif features.tumor_size_cm <= 7:
            staging.T = "T3"
        else:
            staging.T = "T4"
        
        # Determine N stage
        if features.lymph_nodes_involved == 0:
            staging.N = "N0"
        elif features.lymph_nodes_involved <= 3:
            staging.N = "N1"
        else:
            staging.N = "N2"
        
        # Determine M stage
        staging.M = "M1" if features.distant_metastasis else "M0"
        
        # Calculate overall stage
        if staging.M == "M1":
            staging.stage = "Stage IV"
        elif staging.T == "T1" and staging.N == "N0":
            staging.stage = "Stage I"
        elif staging.T in ["T2", "T3"] and staging.N in ["N0", "N1"]:
            staging.stage = "Stage II"
        elif staging.T in ["T3", "T4"] or staging.N == "N2":
            staging.stage = "Stage III"
        else:
            staging.stage = "Stage Unknown"
        
        staging.description = self.get_stage_description(staging)
        return staging
    
    def get_stage_description(self, staging: TNMStaging) -> str:
        """Get description for lung cancer staging."""
        descriptions = {
            "Stage I": "Early stage confined to lung only",
            "Stage II": "Large tumor or spread to nearby lymph nodes",
            "Stage III": "Locally advanced, spread within chest",
            "Stage IV": "Metastasis to distant organs"
        }
        
        return descriptions.get(staging.stage, "Staging information not available")


class ColorectalCancerStager(CancerStager):
    """Staging logic for colorectal cancer."""
    
    def stage(self, features: MedicalFeatures) -> TNMStaging:
        """Calculate TNM staging for colorectal cancer."""
        staging = TNMStaging()
        
        # Determine T stage based on depth
        depth_to_t = {
            "submucosa": "T1",
            "muscularis propria": "T2",
            "subserosa": "T3",
            "peritoneum": "T4a",
            "invasion": "T4b"
        }
        
        staging.T = depth_to_t.get(features.tumor_depth.lower(), "Tx")
        
        # Determine N stage
        if features.lymph_nodes_involved == 0:
            staging.N = "N0"
        elif features.lymph_nodes_involved <= 3:
            staging.N = "N1"
        else:
            staging.N = "N2"
        
        # Determine M stage
        staging.M = "M1" if features.distant_metastasis else "M0"
        
        # Calculate overall stage
        if staging.M == "M1":
            staging.stage = "Stage IV"
        elif staging.T in ["T1", "T2"] and staging.N == "N0":
            staging.stage = "Stage I"
        elif staging.T == "T3" and staging.N == "N0":
            staging.stage = "Stage II"
        elif staging.N in ["N1", "N2"]:
            staging.stage = "Stage III"
        else:
            staging.stage = "Stage Unknown"
        
        staging.description = self.get_stage_description(staging)
        return staging
    
    def get_stage_description(self, staging: TNMStaging) -> str:
        """Get description for colorectal cancer staging."""
        descriptions = {
            "Stage I": "Early stage confined to bowel wall",
            "Stage II": "Penetrated bowel wall but no lymph node spread",
            "Stage III": "Spread to nearby lymph nodes",
            "Stage IV": "Metastasis to distant organs"
        }
        
        return descriptions.get(staging.stage, "Staging information not available")


class HeadNeckCancerStager(CancerStager):
    """Staging logic for head and neck cancer."""
    
    def stage(self, features: MedicalFeatures) -> TNMStaging:
        """Calculate TNM staging for head and neck cancer."""
        staging = TNMStaging()
        
        # Determine T stage
        if features.tumor_size_cm <= 2:
            staging.T = "T1"
        elif features.tumor_size_cm <= 4:
            staging.T = "T2"
        else:
            staging.T = "T3"
        
        # Determine N stage
        if features.lymph_nodes_involved == 0:
            staging.N = "N0"
        elif features.lymph_nodes_involved == 1:
            staging.N = "N1"
        elif 2 <= features.lymph_nodes_involved <= 3:
            staging.N = "N2"
        else:
            staging.N = "N3"
        
        # Determine M stage
        staging.M = "M1" if features.distant_metastasis else "M0"
        
        # Calculate overall stage
        if staging.M == "M1":
            staging.stage = "Stage IV"
            staging.substage = "C"
        elif staging.T == "T1" and staging.N == "N0":
            staging.stage = "Stage I"
        elif staging.T in ["T1", "T2"] and staging.N in ["N1", "N2"]:
            staging.stage = "Stage III"
        elif staging.T == "T3" or staging.N == "N3":
            staging.stage = "Stage IV"
            staging.substage = "A"
        else:
            staging.stage = "Stage II"
        
        staging.description = self.get_stage_description(staging)
        return staging
    
    def get_stage_description(self, staging: TNMStaging) -> str:
        """Get description for head and neck cancer staging."""
        descriptions = {
            "Stage I": "Small tumor, locally confined",
            "Stage II": "Large tumor but no lymph node spread",
            "Stage III": "Spread to nearby lymph nodes",
            "Stage IVA": "Locally advanced disease",
            "Stage IVC": "Distant metastasis"
        }
        
        full_stage = staging.get_full_stage()
        return descriptions.get(full_stage, staging.stage)


class StagingEngine:
    """Main staging engine that coordinates cancer-specific stagers."""
    
    def __init__(self):
        """Initialize the staging engine with cancer-specific stagers."""
        self.stagers = {
            "gallbladder": GallbladderCancerStager(),
            "esophageal": EsophagealCancerStager(),
            "breast": BreastCancerStager(),
            "lung": LungCancerStager(),
            "colorectal": ColorectalCancerStager(),
            "head and neck": HeadNeckCancerStager()
        }
    
    @st.cache_data(ttl=3600)
    def calculate_staging(_self, features: MedicalFeatures) -> TNMStaging:
        """
        Calculate TNM staging based on extracted features.
        
        Args:
            features: Extracted medical features
            
        Returns:
            TNMStaging object with staging results
            
        Raises:
            StagingError: If staging calculation fails
        """
        try:
            # Check if we have a valid cancer type
            if not features.cancer_type:
                raise StagingError(ERROR_MESSAGES["cancer_type_not_found"])
            
            # Check if cancer type is supported
            if features.cancer_type not in _self.stagers:
                logger.warning(f"Unsupported cancer type: {features.cancer_type}")
                return TNMStaging(
                    stage="Not Available",
                    description=f"{features.cancer_type} ক্যান্সারের জন্য স্টেজিং এখনও উপলব্ধ নয়"
                )
            
            # Get appropriate stager
            stager = _self.stagers[features.cancer_type]
            
            # Calculate staging
            staging = stager.stage(features)
            
            logger.info(
                f"Staging calculated for {features.cancer_type}: "
                f"T{staging.T} N{staging.N} M{staging.M} - {staging.get_full_stage()}"
            )
            
            return staging
            
        except OncoStagingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in staging calculation: {e}")
            raise StagingError(ERROR_MESSAGES["staging_error"])
    
    def get_staging_summary(self, staging: TNMStaging, cancer_type: str) -> Dict[str, Any]:
        """Get comprehensive staging summary."""
        return {
            "cancer_type": cancer_type,
            "tnm": {
                "T": staging.T,
                "N": staging.N,
                "M": staging.M
            },
            "stage": staging.get_full_stage(),
            "description": staging.description,
            "prognosis_indicator": self._get_prognosis_indicator(staging.stage)
        }
    
    def _get_prognosis_indicator(self, stage: str) -> str:
        """Get general prognosis indicator based on stage."""
        if "I" in stage and "V" not in stage:
            return "Generally good prognosis"
        elif "II" in stage:
            return "Moderate prognosis"
        elif "III" in stage:
            return "Guarded prognosis"
        elif "IV" in stage:
            return "Serious prognosis"
        else:
            return "Prognosis information not available"
