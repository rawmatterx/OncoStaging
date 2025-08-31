import { MedicalFeatures, TNMStaging } from '@/types/medical';

export function determineTNMStage(cancerType: string, features: MedicalFeatures): TNMStaging {
  const type = cancerType.toLowerCase();

  switch (type) {
    case 'gallbladder':
      return stageGallbladderCancer(features);
    case 'esophageal':
      return stageEsophagealCancer(features);
    case 'breast':
      return stageBreastCancer(features);
    case 'lung':
      return stageLungCancer(features);
    case 'colorectal':
      return stageColorectalCancer(features);
    case 'head and neck':
    case 'oral cavity':
    case 'oropharynx':
      return stageHeadNeckCancer(features);
    default:
      return {
        T: 'Unknown',
        N: 'Unknown',
        M: 'Unknown',
        stage: 'Not available',
        description: `Staging not available for ${cancerType}`
      };
  }
}

function stageGallbladderCancer(features: MedicalFeatures): TNMStaging {
  let T: string, N: string, M: string, stage: string;

  // Determine T stage
  if (features.liver_invasion) {
    T = 'T3';
  } else if (features.tumor_size_cm > 2) {
    T = 'T2';
  } else if (features.tumor_size_cm > 0) {
    T = 'T1';
  } else {
    T = 'Tx';
  }

  // Determine N stage
  if (features.lymph_nodes_involved === 0) {
    N = 'N0';
  } else if (features.lymph_nodes_involved <= 3) {
    N = 'N1';
  } else {
    N = 'N2';
  }

  // Determine M stage
  M = features.distant_metastasis ? 'M1' : 'M0';

  // Calculate overall stage
  if (M === 'M1') {
    stage = 'Stage IVB';
  } else if (T === 'T3' && N !== 'N0') {
    stage = 'Stage IVA';
  } else if (T === 'T3') {
    stage = 'Stage IIIB';
  } else if (T === 'T2' && N === 'N0') {
    stage = 'Stage II';
  } else if (['T1', 'T2'].includes(T) && N !== 'N0') {
    stage = 'Stage IIIA';
  } else if (T === 'T1' && N === 'N0') {
    stage = 'Stage I';
  } else {
    stage = 'Stage Unknown';
  }

  return {
    T,
    N,
    M,
    stage,
    description: getGallbladderStageDescription(stage)
  };
}

function stageEsophagealCancer(features: MedicalFeatures): TNMStaging {
  let T: string, N: string, M: string, stage: string;

  // Determine T stage based on depth
  const depthToT: Record<string, string> = {
    mucosa: 'T1',
    submucosa: 'T1b',
    muscularis: 'T2',
    adventitia: 'T3',
    'adjacent structures': 'T4'
  };

  T = depthToT[features.tumor_depth.toLowerCase()] || 'Tx';

  // Determine N stage
  if (features.lymph_nodes_involved === 0) {
    N = 'N0';
  } else if (features.lymph_nodes_involved <= 2) {
    N = 'N1';
  } else if (features.lymph_nodes_involved <= 6) {
    N = 'N2';
  } else {
    N = 'N3';
  }

  // Determine M stage
  M = features.distant_metastasis ? 'M1' : 'M0';

  // Calculate overall stage
  if (M === 'M1') {
    stage = 'Stage IVB';
  } else if (T === 'T4' || N === 'N3') {
    stage = 'Stage IVA';
  } else if (['T2', 'T3'].includes(T) && ['N0', 'N1'].includes(N)) {
    stage = 'Stage II';
  } else if (T === 'T1' && N === 'N0') {
    stage = 'Stage I';
  } else {
    stage = 'Stage III';
  }

  return {
    T,
    N,
    M,
    stage,
    description: getEsophagealStageDescription(stage)
  };
}

function stageBreastCancer(features: MedicalFeatures): TNMStaging {
  let T: string, N: string, M: string, stage: string;

  // Determine T stage
  if (features.tumor_size_cm <= 2) {
    T = 'T1';
  } else if (features.tumor_size_cm <= 5) {
    T = 'T2';
  } else {
    T = 'T3';
  }

  // Determine N stage
  if (features.lymph_nodes_involved === 0) {
    N = 'N0';
  } else if (features.lymph_nodes_involved <= 3) {
    N = 'N1';
  } else if (features.lymph_nodes_involved <= 9) {
    N = 'N2';
  } else {
    N = 'N3';
  }

  // Determine M stage
  M = features.distant_metastasis ? 'M1' : 'M0';

  // Calculate overall stage
  if (M === 'M1') {
    stage = 'Stage IV';
  } else if (T === 'T1' && N === 'N0') {
    stage = 'Stage I';
  } else if (['T1', 'T2'].includes(T) && N === 'N1') {
    stage = 'Stage II';
  } else if (T === 'T3' || ['N2', 'N3'].includes(N)) {
    stage = 'Stage III';
  } else {
    stage = 'Stage Unknown';
  }

  return {
    T,
    N,
    M,
    stage,
    description: getBreastStageDescription(stage)
  };
}

function stageLungCancer(features: MedicalFeatures): TNMStaging {
  let T: string, N: string, M: string, stage: string;

  // Determine T stage
  if (features.tumor_size_cm <= 3) {
    T = 'T1';
  } else if (features.tumor_size_cm <= 5) {
    T = 'T2';
  } else if (features.tumor_size_cm <= 7) {
    T = 'T3';
  } else {
    T = 'T4';
  }

  // Determine N stage
  if (features.lymph_nodes_involved === 0) {
    N = 'N0';
  } else if (features.lymph_nodes_involved <= 3) {
    N = 'N1';
  } else {
    N = 'N2';
  }

  // Determine M stage
  M = features.distant_metastasis ? 'M1' : 'M0';

  // Calculate overall stage
  if (M === 'M1') {
    stage = 'Stage IV';
  } else if (T === 'T1' && N === 'N0') {
    stage = 'Stage I';
  } else if (['T2', 'T3'].includes(T) && ['N0', 'N1'].includes(N)) {
    stage = 'Stage II';
  } else if (['T3', 'T4'].includes(T) || N === 'N2') {
    stage = 'Stage III';
  } else {
    stage = 'Stage Unknown';
  }

  return {
    T,
    N,
    M,
    stage,
    description: getLungStageDescription(stage)
  };
}

function stageColorectalCancer(features: MedicalFeatures): TNMStaging {
  let T: string, N: string, M: string, stage: string;

  // Determine T stage based on depth
  const depthToT: Record<string, string> = {
    submucosa: 'T1',
    'muscularis propria': 'T2',
    subserosa: 'T3',
    'peritoneum/invasion': 'T4'
  };

  T = depthToT[features.tumor_depth.toLowerCase()] || 'Tx';

  // Determine N stage
  if (features.lymph_nodes_involved === 0) {
    N = 'N0';
  } else if (features.lymph_nodes_involved <= 3) {
    N = 'N1';
  } else {
    N = 'N2';
  }

  // Determine M stage
  M = features.distant_metastasis ? 'M1' : 'M0';

  // Calculate overall stage
  if (M === 'M1') {
    stage = 'Stage IV';
  } else if (['T1', 'T2'].includes(T) && N === 'N0') {
    stage = 'Stage I';
  } else if (T === 'T3' && N === 'N0') {
    stage = 'Stage II';
  } else if (['N1', 'N2'].includes(N)) {
    stage = 'Stage III';
  } else {
    stage = 'Stage Unknown';
  }

  return {
    T,
    N,
    M,
    stage,
    description: getColorectalStageDescription(stage)
  };
}

function stageHeadNeckCancer(features: MedicalFeatures): TNMStaging {
  let T: string, N: string, M: string, stage: string;

  // Determine T stage
  if (features.tumor_size_cm <= 2) {
    T = 'T1';
  } else if (features.tumor_size_cm <= 4) {
    T = 'T2';
  } else {
    T = 'T3';
  }

  // Determine N stage
  if (features.lymph_nodes_involved === 0) {
    N = 'N0';
  } else if (features.lymph_nodes_involved === 1) {
    N = 'N1';
  } else if (features.lymph_nodes_involved <= 3) {
    N = 'N2';
  } else {
    N = 'N3';
  }

  // Determine M stage
  M = features.distant_metastasis ? 'M1' : 'M0';

  // Calculate overall stage
  if (M === 'M1') {
    stage = 'Stage IVC';
  } else if (T === 'T1' && N === 'N0') {
    stage = 'Stage I';
  } else if (['T1', 'T2'].includes(T) && ['N1', 'N2'].includes(N)) {
    stage = 'Stage II–III';
  } else if (T === 'T3' || N === 'N3') {
    stage = 'Stage IV';
  } else {
    stage = 'Stage Unknown';
  }

  return {
    T,
    N,
    M,
    stage,
    description: getHeadNeckStageDescription(stage)
  };
}

// Stage description functions
function getGallbladderStageDescription(stage: string): string {
  const descriptions: Record<string, string> = {
    'Stage I': 'Early stage cancer confined to gallbladder wall',
    'Stage II': 'Tumor has reached outer layer of gallbladder',
    'Stage IIIA': 'Tumor has spread to nearby lymph nodes',
    'Stage IIIB': 'Tumor has invaded liver or nearby organs',
    'Stage IVA': 'Tumor has spread to major blood vessels or multiple organs',
    'Stage IVB': 'Advanced cancer with distant metastasis'
  };
  return descriptions[stage] || 'Staging information not available';
}

function getEsophagealStageDescription(stage: string): string {
  const descriptions: Record<string, string> = {
    'Stage I': 'Early stage confined to inner layer of esophagus',
    'Stage II': 'Tumor has reached deeper layers of esophagus',
    'Stage III': 'Spread to nearby lymph nodes',
    'Stage IVA': 'Invaded nearby organs',
    'Stage IVB': 'Metastasis to distant organs'
  };
  return descriptions[stage] || stage;
}

function getBreastStageDescription(stage: string): string {
  const descriptions: Record<string, string> = {
    'Stage I': 'Early stage, small tumor, no lymph node spread',
    'Stage II': 'Moderate-sized tumor or limited lymph node involvement',
    'Stage III': 'Large tumor or extensive lymph node involvement',
    'Stage IV': 'Metastasis to distant organs'
  };
  return descriptions[stage] || 'Staging information not available';
}

function getLungStageDescription(stage: string): string {
  const descriptions: Record<string, string> = {
    'Stage I': 'Early stage confined to lung only',
    'Stage II': 'Large tumor or spread to nearby lymph nodes',
    'Stage III': 'Locally advanced, spread within chest',
    'Stage IV': 'Metastasis to distant organs'
  };
  return descriptions[stage] || 'Staging information not available';
}

function getColorectalStageDescription(stage: string): string {
  const descriptions: Record<string, string> = {
    'Stage I': 'Early stage confined to bowel wall',
    'Stage II': 'Penetrated bowel wall but no lymph node spread',
    'Stage III': 'Spread to nearby lymph nodes',
    'Stage IV': 'Metastasis to distant organs'
  };
  return descriptions[stage] || 'Staging information not available';
}

function getHeadNeckStageDescription(stage: string): string {
  const descriptions: Record<string, string> = {
    'Stage I': 'Small tumor, locally confined',
    'Stage II': 'Large tumor but no lymph node spread',
    'Stage III': 'Spread to nearby lymph nodes',
    'Stage IVA': 'Locally advanced disease',
    'Stage IVC': 'Distant metastasis'
  };
  return descriptions[stage] || stage;
}

export function getTreatmentGuidelines(cancerType: string, stage: string): string {
  const treatmentDict: Record<string, Record<string, string>> = {
    gallbladder: {
      I: 'Surgical resection (simple cholecystectomy or wedge resection).',
      II: 'Extended cholecystectomy with lymph node dissection.',
      III: 'Surgical resection ± adjuvant chemoradiotherapy.',
      IV: 'Systemic chemotherapy (e.g., gemcitabine + cisplatin).'
    },
    esophageal: {
      I: 'Endoscopic mucosal resection or esophagectomy.',
      II: 'Neoadjuvant chemoradiotherapy followed by surgery.',
      III: 'Definitive chemoradiation or surgery after neoadjuvant therapy.',
      IV: 'Systemic therapy or palliative RT/stent placement.'
    },
    breast: {
      I: 'Surgery (BCS or mastectomy) ± adjuvant RT.',
      II: 'Surgery + chemo/hormonal therapy + radiation.',
      III: 'Neoadjuvant chemotherapy → surgery + adjuvant therapy.',
      IV: 'Systemic therapy based on biomarkers.'
    },
    lung: {
      I: 'Surgical resection ± adjuvant chemo.',
      II: 'Surgery + chemo ± radiation.',
      III: 'Concurrent chemoradiotherapy ± immunotherapy.',
      IV: 'Targeted therapy, immunotherapy, or chemo.'
    },
    colorectal: {
      I: 'Surgical resection (segmental colectomy).',
      II: 'Surgery ± adjuvant chemo (if high-risk).',
      III: 'Surgery + adjuvant FOLFOX or CAPOX.',
      IV: 'Systemic therapy ± targeted therapy.'
    },
    'head and neck': {
      I: 'Surgery or radiation alone.',
      II: 'Surgery ± adjuvant RT.',
      III: 'Surgery + RT/chemo or concurrent chemoradiation.',
      IV: 'Systemic therapy ± RT. Consider immunotherapy.'
    }
  };

  // Determine stage group
  let stageGroup = 'Unknown';
  if (stage.includes('I') && !stage.includes('V')) {
    stageGroup = 'I';
  } else if (stage.includes('II')) {
    stageGroup = 'II';
  } else if (stage.includes('III')) {
    stageGroup = 'III';
  } else if (stage.includes('IV')) {
    stageGroup = 'IV';
  }

  return treatmentDict[cancerType]?.[stageGroup] || 'Treatment information not available.';
}