import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function formatConfidence(confidence: number): string {
  return `${(confidence * 100).toFixed(1)}%`;
}

export function extractCancerType(text: string): { type: string; confidence: number } {
  const cancerKeywords = {
    gallbladder: ['gallbladder', 'gb carcinoma', 'cholangiocarcinoma'],
    esophageal: ['esophagus', 'esophageal', 'oesophageal'],
    breast: ['breast', 'mammary', 'ductal carcinoma', 'lobular carcinoma'],
    lung: ['lung', 'pulmonary', 'nsclc', 'sclc', 'bronchogenic'],
    colorectal: ['colon', 'rectum', 'colorectal', 'rectal', 'colonic'],
    'head and neck': ['oral cavity', 'oropharynx', 'larynx', 'pharynx', 'head and neck']
  };

  const textLower = text.toLowerCase();
  let bestMatch = '';
  let bestScore = 0;

  for (const [cancerType, keywords] of Object.entries(cancerKeywords)) {
    let score = 0;
    for (const keyword of keywords) {
      if (textLower.includes(keyword.toLowerCase())) {
        score += keyword.split(' ').length * 0.3;
      }
    }
    if (score > bestScore) {
      bestScore = score;
      bestMatch = cancerType;
    }
  }

  const confidence = Math.min(bestScore / 3.0, 1.0);
  return { type: bestMatch, confidence };
}

export function extractTumorSize(text: string): { size: number; confidence: number } {
  const sizePattern = /(?:tumor|mass|lesion|growth)[\s\w]*?(?:measuring|measures|size|sized?)\s*(?:approximately|approx\.?|about)?\s*(\d+(?:\.\d+)?)\s*(?:x\s*\d+(?:\.\d+)?)*\s*(cm|mm)/gi;
  
  const matches = Array.from(text.matchAll(sizePattern));
  const sizes: number[] = [];

  for (const match of matches) {
    let size = parseFloat(match[1]);
    const unit = match[2].toLowerCase();
    
    if (unit === 'mm') {
      size /= 10; // Convert to cm
    }
    
    sizes.push(size);
  }

  if (sizes.length > 0) {
    const maxSize = Math.max(...sizes);
    const confidence = sizes.length === 1 ? 0.9 : 0.7;
    return { size: maxSize, confidence };
  }

  return { size: 0, confidence: 0 };
}

export function extractLymphNodes(text: string): { count: number; confidence: number } {
  const nodePattern = /(?:(?<num>\d+)|multiple|several|numerous)\s*(?:positive|involved|metastatic|malignant|enlarged)?\s*(?:lymph\s*nodes?|nodes?|LN)/gi;
  
  const matches = Array.from(text.matchAll(nodePattern));
  const counts: number[] = [];

  for (const match of matches) {
    if (match.groups?.num) {
      counts.push(parseInt(match.groups.num));
    } else {
      const qualifier = match[0].toLowerCase();
      if (qualifier.includes('multiple') || qualifier.includes('numerous')) {
        counts.push(5);
      } else if (qualifier.includes('several')) {
        counts.push(3);
      }
    }
  }

  if (counts.length > 0) {
    const maxCount = Math.max(...counts);
    const confidence = 0.8;
    return { count: maxCount, confidence };
  }

  return { count: 0, confidence: 0.5 };
}

export function extractMetastasis(text: string): { hasMetastasis: boolean; confidence: number } {
  const metastasisPattern = /(?:distant\s*)?(?:metastas[ei]s|metastatic\s*disease|secondary\s*deposits?|disseminated)/gi;
  
  const matches = Array.from(text.matchAll(metastasisPattern));
  
  if (matches.length > 0) {
    // Check for negation
    let hasMetastasis = true;
    for (const match of matches) {
      const start = Math.max(0, match.index! - 50);
      const context = text.slice(start, match.index!).toLowerCase();
      
      if (['no ', 'without', 'negative', 'absent'].some(neg => context.includes(neg))) {
        hasMetastasis = false;
        break;
      }
    }
    
    const confidence = hasMetastasis ? 0.9 : 0.8;
    return { hasMetastasis, confidence };
  }

  return { hasMetastasis: false, confidence: 0.6 };
}