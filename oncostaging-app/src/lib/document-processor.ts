import { createWorker } from 'tesseract.js';
import * as pdfjsLib from 'pdfjs-dist';
import mammoth from 'mammoth';
import { OCRResult, ExtractedMedicalData, MedicalFeatures } from '@/types/medical';
import { extractCancerType, extractTumorSize, extractLymphNodes, extractMetastasis } from './utils';

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

export class DocumentProcessor {
  private tesseractWorker: any = null;

  async initializeTesseract() {
    if (!this.tesseractWorker) {
      this.tesseractWorker = await createWorker('eng');
    }
  }

  async processDocument(file: File): Promise<OCRResult> {
    const startTime = Date.now();
    
    try {
      let text = '';
      let confidence = 0;
      let method = '';
      let pageCount = 1;

      const fileType = file.type;
      
      if (fileType === 'application/pdf') {
        const result = await this.processPDF(file);
        text = result.text;
        confidence = result.confidence;
        method = result.method;
        pageCount = result.pageCount;
      } else if (fileType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
        const result = await this.processDOCX(file);
        text = result.text;
        confidence = 0.95; // High confidence for direct text extraction
        method = 'docx_extraction';
      } else if (fileType.startsWith('image/')) {
        const result = await this.processImage(file);
        text = result.text;
        confidence = result.confidence;
        method = 'tesseract_ocr';
      } else {
        throw new Error('Unsupported file type');
      }

      const processingTime = (Date.now() - startTime) / 1000;

      return {
        text,
        confidence,
        method,
        processing_time: processingTime,
        page_count: pageCount,
        file_info: {
          name: file.name,
          size: file.size,
          type: file.type
        }
      };
    } catch (error) {
      throw new Error(`Document processing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async processPDF(file: File): Promise<{ text: string; confidence: number; method: string; pageCount: number }> {
    try {
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      
      let text = '';
      const pageCount = pdf.numPages;

      // Try standard text extraction first
      for (let i = 1; i <= pageCount; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        const pageText = textContent.items
          .map((item: any) => item.str)
          .join(' ');
        text += pageText + '\n';
      }

      // If sufficient text extracted, use it
      if (text.trim().length > 100) {
        return {
          text: text.trim(),
          confidence: 0.95,
          method: 'standard_extraction',
          pageCount
        };
      }

      // Otherwise, use OCR on first page
      const page = await pdf.getPage(1);
      const viewport = page.getViewport({ scale: 2.0 });
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d')!;
      canvas.height = viewport.height;
      canvas.width = viewport.width;

      await page.render({ canvasContext: context, viewport }).promise;
      
      // Convert canvas to blob and process with OCR
      const blob = await new Promise<Blob>((resolve) => {
        canvas.toBlob((blob) => resolve(blob!), 'image/png');
      });

      const ocrResult = await this.processImageBlob(blob);
      
      return {
        text: ocrResult.text,
        confidence: ocrResult.confidence,
        method: 'pdf_ocr',
        pageCount
      };

    } catch (error) {
      throw new Error(`PDF processing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async processDOCX(file: File): Promise<{ text: string }> {
    try {
      const arrayBuffer = await file.arrayBuffer();
      const result = await mammoth.extractRawText({ arrayBuffer });
      
      if (!result.value.trim()) {
        throw new Error('No text could be extracted from DOCX file');
      }

      return { text: result.value };
    } catch (error) {
      throw new Error(`DOCX processing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async processImage(file: File): Promise<{ text: string; confidence: number }> {
    return this.processImageBlob(file);
  }

  private async processImageBlob(blob: Blob): Promise<{ text: string; confidence: number }> {
    try {
      await this.initializeTesseract();
      
      const { data: { text, confidence } } = await this.tesseractWorker.recognize(blob);
      
      return {
        text: text.trim(),
        confidence: confidence / 100
      };
    } catch (error) {
      throw new Error(`OCR processing failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async extractFeatures(text: string): Promise<MedicalFeatures> {
    try {
      const cancerResult = extractCancerType(text);
      const sizeResult = extractTumorSize(text);
      const nodesResult = extractLymphNodes(text);
      const metastasisResult = extractMetastasis(text);

      // Extract liver invasion
      const liverInvasionPattern = /(?:liver|hepatic)\s*(?:invasion|involvement|infiltration|extension|involvement)|involving\s*(?:liver|segments?)/gi;
      const liverInvasion = liverInvasionPattern.test(text);

      // Extract tumor depth
      const depthKeywords = ['mucosa', 'submucosa', 'muscularis', 'subserosa', 'serosa', 'adventitia'];
      let tumorDepth = '';
      for (const depth of depthKeywords) {
        if (text.toLowerCase().includes(depth)) {
          tumorDepth = depth;
          break;
        }
      }

      return {
        cancer_type: cancerResult.type,
        tumor_size_cm: sizeResult.size,
        lymph_nodes_involved: nodesResult.count,
        distant_metastasis: metastasisResult.hasMetastasis,
        liver_invasion: liverInvasion,
        tumor_depth: tumorDepth,
        confidence_scores: {
          cancer_type: cancerResult.confidence,
          tumor_size: sizeResult.confidence,
          lymph_nodes: nodesResult.confidence,
          metastasis: metastasisResult.confidence,
          liver_invasion: liverInvasion ? 0.8 : 0.7,
          tumor_depth: tumorDepth ? 0.8 : 0.0
        },
        extracted_values: {}
      };
    } catch (error) {
      throw new Error(`Feature extraction failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async cleanup() {
    if (this.tesseractWorker) {
      await this.tesseractWorker.terminate();
      this.tesseractWorker = null;
    }
  }
}