export interface MedicalFeatures {
  cancer_type: string;
  tumor_size_cm: number;
  lymph_nodes_involved: number;
  distant_metastasis: boolean;
  liver_invasion: boolean;
  tumor_depth: string;
  confidence_scores: Record<string, number>;
  extracted_values: Record<string, string[]>;
}

export interface TNMStaging {
  T: string;
  N: string;
  M: string;
  stage: string;
  substage?: string;
  description: string;
}

export interface ExtractedMedicalData {
  patient_id: string;
  patient_name: string;
  age: string;
  gender: string;
  study_date: string;
  study_type: string;
  modality: string;
  referring_physician: string;
  cancer_type: string;
  primary_site: string;
  histology: string;
  tumor_size: string;
  tumor_location: string;
  tumor_description: string;
  t_stage: string;
  n_stage: string;
  m_stage: string;
  overall_stage: string;
  suv_max: string;
  suv_peak: string;
  metabolic_tumor_volume: string;
  total_lesion_glycolysis: string;
  lymph_nodes_involved: string;
  lymph_node_stations: string[];
  distant_metastases: string[];
  metastatic_sites: string[];
  additional_findings: string[];
  recommendations: string[];
  extraction_confidence: Record<string, number>;
  impression: string;
  findings: string;
  comparison: string;
  technique: string;
}

export interface ProcessingResult {
  success: boolean;
  document?: {
    text: string;
    file_name: string;
    file_type: string;
    file_size: number;
    text_length: number;
    processing_time: number;
  };
  features?: MedicalFeatures;
  staging?: TNMStaging;
  ai_analysis?: string;
  error?: string;
}

export interface OCRResult {
  text: string;
  confidence: number;
  method: string;
  processing_time: number;
  page_count: number;
  file_info: {
    name: string;
    size: number;
    type: string;
  };
}

export interface ClinicalRecommendation {
  ajcc_stage: string;
  stage_group: string;
  diagnostic_recommendations: string[];
  treatment_recommendations: string[];
  clinical_rationale: string;
}

export interface AppState {
  current_step: number;
  ocr_result: OCRResult | null;
  extraction_result: ExtractedMedicalData | null;
  clinical_recommendations: ClinicalRecommendation | null;
  processing_results: ProcessingResult | null;
}