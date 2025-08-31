'use client';

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { FileUploader } from '@/components/FileUploader';
import { ProcessingSteps } from '@/components/ProcessingSteps';
import { ResultsDisplay } from '@/components/ResultsDisplay';
import { QASection } from '@/components/QASection';
import { FeedbackSection } from '@/components/FeedbackSection';
import { DocumentProcessor } from '@/lib/document-processor';
import { determineTNMStage } from '@/lib/staging';
import { AppState, ProcessingResult, OCRResult } from '@/types/medical';
import { Activity, Brain, FileText, HelpCircle, Stethoscope } from 'lucide-react';

export default function OncoStagingApp() {
  const [appState, setAppState] = useState<AppState>({
    current_step: 1,
    ocr_result: null,
    extraction_result: null,
    clinical_recommendations: null,
    processing_results: null
  });

  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [showHelp, setShowHelp] = useState(false);

  const documentProcessor = new DocumentProcessor();

  const handleFileSelect = useCallback(async (file: File) => {
    setIsProcessing(true);
    setProcessingProgress(0);

    try {
      // Step 1: OCR Processing
      setProcessingProgress(20);
      setAppState(prev => ({ ...prev, current_step: 2 }));
      
      const ocrResult = await documentProcessor.processDocument(file);
      setAppState(prev => ({ ...prev, ocr_result: ocrResult }));
      
      // Step 2: Feature Extraction
      setProcessingProgress(50);
      setAppState(prev => ({ ...prev, current_step: 3 }));
      
      const features = await documentProcessor.extractFeatures(ocrResult.text);
      
      // Step 3: TNM Staging
      setProcessingProgress(70);
      setAppState(prev => ({ ...prev, current_step: 4 }));
      
      const staging = determineTNMStage(features.cancer_type, features);
      
      // Step 4: Complete Processing
      setProcessingProgress(90);
      setAppState(prev => ({ ...prev, current_step: 5 }));
      
      const processingResult: ProcessingResult = {
        success: true,
        document: {
          text: ocrResult.text,
          file_name: file.name,
          file_type: file.type,
          file_size: file.size,
          text_length: ocrResult.text.length,
          processing_time: ocrResult.processing_time
        },
        features,
        staging,
        ai_analysis: features.cancer_type ? 
          `Based on the analysis, this appears to be ${staging.stage} ${features.cancer_type} cancer. ${staging.description}` : 
          undefined
      };

      setProcessingProgress(100);
      setAppState(prev => ({ 
        ...prev, 
        processing_results: processingResult,
        current_step: 5
      }));

    } catch (error) {
      const errorResult: ProcessingResult = {
        success: false,
        error: error instanceof Error ? error.message : 'Processing failed'
      };
      
      setAppState(prev => ({ 
        ...prev, 
        processing_results: errorResult 
      }));
    } finally {
      setIsProcessing(false);
      setTimeout(() => setProcessingProgress(0), 1000);
    }
  }, []);

  const handleDownload = () => {
    if (!appState.processing_results?.success) return;

    const { features, staging } = appState.processing_results;
    const summary = `OncoStaging Report Summary
========================

Generated: ${new Date().toLocaleString()}

Cancer Type: ${features?.cancer_type || 'Not identified'}
Tumor Size: ${features?.tumor_size_cm || 0} cm
Lymph Nodes: ${features?.lymph_nodes_involved || 0}
Metastasis: ${features?.distant_metastasis ? 'Yes' : 'No'}

TNM Staging:
- T: ${staging?.T || 'Unknown'}
- N: ${staging?.N || 'Unknown'}
- M: ${staging?.M || 'Unknown'}
- Overall Stage: ${staging?.stage || 'Unknown'}

Description: ${staging?.description || 'Not available'}

⚠️ This is for informational purposes only. Please consult your oncologist for treatment decisions.
`;

    const blob = new Blob([summary], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `oncostaging_report_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleFeedbackSubmit = (feedback: any) => {
    console.log('Feedback submitted:', feedback);
    // In a real app, this would send feedback to your backend
  };

  const completedSteps = [
    ...(appState.ocr_result ? [1, 2] : []),
    ...(appState.processing_results?.features ? [3] : []),
    ...(appState.processing_results?.staging ? [4] : []),
    ...(appState.processing_results?.success ? [5] : [])
  ];

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center space-x-3"
            >
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Stethoscope className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  OncoStaging
                </h1>
                <p className="text-sm text-muted-foreground">Cancer Staging Assistant</p>
              </div>
            </motion.div>

            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="hidden sm:flex">
                AI-Powered Analysis
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowHelp(!showHelp)}
              >
                <HelpCircle className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Upload and Steps */}
          <div className="lg:col-span-1 space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <FileText className="w-5 h-5 text-blue-600" />
                    <span>Upload Report</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <FileUploader
                    onFileSelect={handleFileSelect}
                    isProcessing={isProcessing}
                    processingProgress={processingProgress}
                  />
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <ProcessingSteps
                currentStep={appState.current_step}
                completedSteps={completedSteps}
              />
            </motion.div>
          </div>

          {/* Right Column - Results and Interaction */}
          <div className="lg:col-span-2 space-y-6">
            <AnimatePresence mode="wait">
              {!appState.processing_results ? (
                <motion.div
                  key="welcome"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                >
                  <WelcomeCard />
                </motion.div>
              ) : (
                <motion.div
                  key="results"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-6"
                >
                  <ResultsDisplay
                    results={appState.processing_results}
                    onDownload={handleDownload}
                  />

                  {appState.processing_results.success && (
                    <>
                      <QASection results={appState.processing_results} />
                      <FeedbackSection onFeedbackSubmit={handleFeedbackSubmit} />
                    </>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Help Modal */}
        <AnimatePresence>
          {showHelp && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
              onClick={() => setShowHelp(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
                className="bg-white rounded-lg p-6 max-w-md w-full"
              >
                <h3 className="text-lg font-semibold mb-4">How to Use OncoStaging</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex items-start space-x-2">
                    <span className="text-blue-600 font-semibold">1.</span>
                    <span>Upload your PET/CT report (PDF, DOCX, or image)</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <span className="text-blue-600 font-semibold">2.</span>
                    <span>System automatically analyzes the report</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <span className="text-blue-600 font-semibold">3.</span>
                    <span>View TNM staging and detailed information</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <span className="text-blue-600 font-semibold">4.</span>
                    <span>Ask questions and get AI-powered answers</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <span className="text-blue-600 font-semibold">5.</span>
                    <span>Download your analysis report</span>
                  </div>
                </div>
                <div className="mt-6 p-3 bg-yellow-50 rounded-lg">
                  <p className="text-xs text-yellow-800">
                    <strong>Important:</strong> This is for informational purposes only. 
                    Always consult your doctor for medical decisions.
                  </p>
                </div>
                <Button onClick={() => setShowHelp(false)} className="w-full mt-4">
                  Got it
                </Button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="bg-white/80 backdrop-blur-sm border-t mt-16">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center text-sm text-muted-foreground">
            <p>OncoStaging v1.0.0 - AI-powered cancer staging analysis</p>
            <p className="mt-1">For informational purposes only. Consult healthcare professionals for medical decisions.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

function WelcomeCard() {
  return (
    <Card className="text-center">
      <CardContent className="p-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          <div className="w-20 h-20 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto">
            <Activity className="w-10 h-10 text-white" />
          </div>
          
          <div>
            <h2 className="text-3xl font-bold mb-4">Welcome to OncoStaging</h2>
            <p className="text-lg text-muted-foreground mb-6">
              Advanced AI-powered cancer staging analysis from your PET/CT reports
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
            <div className="space-y-2">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <FileText className="w-4 h-4 text-blue-600" />
              </div>
              <h3 className="font-semibold">Smart Analysis</h3>
              <p className="text-sm text-muted-foreground">
                Advanced OCR and AI extract key medical information automatically
              </p>
            </div>
            
            <div className="space-y-2">
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                <Activity className="w-4 h-4 text-green-600" />
              </div>
              <h3 className="font-semibold">TNM Staging</h3>
              <p className="text-sm text-muted-foreground">
                Accurate TNM staging calculation following clinical guidelines
              </p>
            </div>
            
            <div className="space-y-2">
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                <Brain className="w-4 h-4 text-purple-600" />
              </div>
              <h3 className="font-semibold">AI Insights</h3>
              <p className="text-sm text-muted-foreground">
                Get AI-powered explanations and answer your questions
              </p>
            </div>
          </div>

          <div className="pt-4">
            <p className="text-sm text-muted-foreground">
              Upload your PET/CT report above to get started
            </p>
          </div>
        </motion.div>
      </CardContent>
    </Card>
  );
}