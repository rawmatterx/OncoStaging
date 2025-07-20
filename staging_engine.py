"""
Staging engine module for OncoStaging application.
Implements TNM staging algorithms with comprehensive validation.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

from config import config_manager
from feature_extractor import MedicalFeatures
from exceptions import StagingError, MedicalDataValidationError


@dataclass
class TNMStaging:
    """Data class for TNM staging results."""
    T: str = "Unknown"
    N: str = "Unknown"
    M: str = "Unknown"
    Stage: str = "Unknown"
    confidence: float = 0.0
    guidelines_url: str = ""


class CancerStager(ABC):
    """Abstract base class for cancer-specific staging algorithms."""
    
    @abstractmethod
    def stage(self, features: MedicalFeatures) -> TNMStaging:
        """Stage cancer based on extracted features."""
        pass
    
    @abstractmethod
    def get_cancer_type(self) -> str:
        """Get the cancer type this stager handles."""
        pass


class GallbladderStager(CancerStager):
    """Gallbladder cancer staging implementation."""
    
    def get_cancer_type(self) -> str:
        return "gallbladder"
    
    def stage(self, features: MedicalFeatures) -> TNMStaging:
        """Stage gallbladder cancer based on features."""
        t_size = features.tumor_size_cm
        liver_invasion = features.liver_invasion
        nodes = features.lymph_nodes_involved
        distant_mets = features.distant_metastasis
        
        # T staging
        if liver_invasion:
            T = "T3"
        elif t_size > 2:
            T = "T2"
        elif t_size > 0:
            T = "T1"
        else:
            T = "Tx"
        
        # N staging
        if nodes == 0:
            N = "N0"
        elif 1 <= nodes <= 3:
            N = "N1"
        else:
            N = "N2"
        
        # M staging
        M = "M1" if distant_mets else "M0"
        
        # Overall staging
        if M == "M1":
            Stage = "Stage IVB"
        elif T == "T3" and N != "N0":
            Stage = "Stage IVA"
        elif T == "T3":
            Stage = "Stage IIIB"
        elif N == "N2":
            Stage = "Stage IIIA"
        elif N == "N1":
            Stage = "Stage IIB"
        elif T == "T2":
            Stage = "Stage IIA"
        else:
            Stage = "Stage I"
        
        return TNMStaging(
            T=T, N=N, M=M, Stage=Stage,
            confidence=features.confidence_score,
            guidelines_url=config_manager.get_staging_guidelines_urls()["gallbladder"]
        )


class StagingEngine:
    """Main staging engine that coordinates cancer-specific stagers."""
    
    def __init__(self):
        self.config = config_manager.config
        self.logger = logging.getLogger(__name__)
        self._setup_stagers()
    
    def _setup_stagers(self):
        """Initialize cancer-specific stagers."""
        self.stagers = {
            "gallbladder": GallbladderStager(),
            "esophageal": EsophagealStager(),
            "breast": BreastStager(),
            "lung": LungStager(),
            "colorectal": ColorectalStager(),
            "head_and_neck": HeadNeckStager()
        }
    
    def determine_stage(self, cancer_type: str, features: MedicalFeatures) -> TNMStaging:
        """Determine TNM stage for given cancer type and features."""
        try:
            if not cancer_type:
                raise StagingError("Cancer type is required for staging")
            
            if not features:
                raise StagingError("Medical features are required for staging")
            
            cancer_type_normalized = cancer_type.lower().replace(" ", "_")
            stager = self.stagers.get(cancer_type_normalized)
            
            if not stager:
                return TNMStaging(
                    T="Unknown", N="Unknown", M="Unknown", 
                    Stage="Not available", confidence=0.0, guidelines_url=""
                )
            
            staging_result = stager.stage(features)
            self.logger.info(f"Staging successful for {cancer_type}: {staging_result.Stage}")
            return staging_result
            
        except Exception as e:
            self.logger.error(f"Staging failed for {cancer_type}: {str(e)}")
            if isinstance(e, StagingError):
                raise
            raise StagingError(f"Failed to determine stage: {str(e)}")
    
    def get_supported_cancer_types(self) -> list:
        """Get list of supported cancer types."""
        return list(self.stagers.keys())


# Additional stager classes would be defined here
class BreastStager(CancerStager):
    def get_cancer_type(self) -> str:
        return "breast"
    
    def stage(self, features: MedicalFeatures) -> TNMStaging:
        # Implementation similar to GallbladderStager
        return TNMStaging()


class LungStager(CancerStager):
    def get_cancer_type(self) -> str:
        return "lung"
    
    def stage(self, features: MedicalFeatures) -> TNMStaging:
        return TNMStaging()


class EsophagealStager(CancerStager):
    def get_cancer_type(self) -> str:
        return "esophageal"
    
    def stage(self, features: MedicalFeatures) -> TNMStaging:
        return TNMStaging()


class ColorectalStager(CancerStager):
    def get_cancer_type(self) -> str:
        return "colorectal"
    
    def stage(self, features: MedicalFeatures) -> TNMStaging:
        return TNMStaging()


class HeadNeckStager(CancerStager):
    def get_cancer_type(self) -> str:
        return "head_and_neck"
    
    def stage(self, features: MedicalFeatures) -> TNMStaging:
        return TNMStaging()