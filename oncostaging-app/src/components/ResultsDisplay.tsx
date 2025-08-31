import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Download, Brain, Activity, Target, FileText } from 'lucide-react';
import { ProcessingResult, MedicalFeatures, TNMStaging } from '@/types/medical';
import { formatConfidence } from '@/lib/utils';

interface ResultsDisplayProps {
  results: ProcessingResult;
  onDownload: () => void;
}

export function ResultsDisplay({ results, onDownload }: ResultsDisplayProps) {
  if (!results.success) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2 text-red-700">
              <AlertCircle className="w-5 h-5" />
              <span>Processing failed: {results.error}</span>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  const { features, staging, ai_analysis } = results;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Success Header */}
      <Card className="border-green-200 bg-green-50">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-green-700">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">Report analyzed successfully!</span>
            </div>
            <Button onClick={onDownload} variant="outline" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Download Report
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Main Results */}
      <Tabs defaultValue="staging" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="staging" className="flex items-center space-x-2">
            <Target className="w-4 h-4" />
            <span>TNM Staging</span>
          </TabsTrigger>
          <TabsTrigger value="features" className="flex items-center space-x-2">
            <Activity className="w-4 h-4" />
            <span>Features</span>
          </TabsTrigger>
          <TabsTrigger value="ai-analysis" className="flex items-center space-x-2">
            <Brain className="w-4 h-4" />
            <span>AI Analysis</span>
          </TabsTrigger>
          <TabsTrigger value="summary" className="flex items-center space-x-2">
            <FileText className="w-4 h-4" />
            <span>Summary</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="staging" className="mt-6">
          <StagingResults staging={staging!} />
        </TabsContent>

        <TabsContent value="features" className="mt-6">
          <FeaturesResults features={features!} />
        </TabsContent>

        <TabsContent value="ai-analysis" className="mt-6">
          <AIAnalysisResults analysis={ai_analysis} />
        </TabsContent>

        <TabsContent value="summary" className="mt-6">
          <SummaryResults results={results} />
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}

function StagingResults({ staging }: { staging: TNMStaging }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="text-center">
          <CardContent className="p-6">
            <div className="text-3xl font-bold text-blue-600 mb-2">{staging.T}</div>
            <div className="text-sm text-muted-foreground">Tumor</div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="text-center">
          <CardContent className="p-6">
            <div className="text-3xl font-bold text-green-600 mb-2">{staging.N}</div>
            <div className="text-sm text-muted-foreground">Nodes</div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="text-center">
          <CardContent className="p-6">
            <div className="text-3xl font-bold text-purple-600 mb-2">{staging.M}</div>
            <div className="text-sm text-muted-foreground">Metastasis</div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="text-center">
          <CardContent className="p-6">
            <div className="text-2xl font-bold text-orange-600 mb-2">{staging.stage}</div>
            <div className="text-sm text-muted-foreground">Overall Stage</div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="col-span-full">
        <Card>
          <CardContent className="p-6">
            <h4 className="font-semibold mb-2">Stage Description</h4>
            <p className="text-muted-foreground">{staging.description}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function FeaturesResults({ features }: { features: MedicalFeatures }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Medical Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="font-medium">Cancer Type:</span>
            <Badge variant={features.cancer_type ? 'success' : 'secondary'}>
              {features.cancer_type || 'Not identified'}
            </Badge>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="font-medium">Tumor Size:</span>
            <span className="text-muted-foreground">{features.tumor_size_cm} cm</span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="font-medium">Lymph Nodes:</span>
            <span className="text-muted-foreground">{features.lymph_nodes_involved}</span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="font-medium">Metastasis:</span>
            <Badge variant={features.distant_metastasis ? 'destructive' : 'success'}>
              {features.distant_metastasis ? 'Yes' : 'No'}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Confidence Scores</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {Object.entries(features.confidence_scores).map(([feature, score]) => (
            <div key={feature} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="capitalize">{feature.replace('_', ' ')}</span>
                <span>{formatConfidence(score)}</span>
              </div>
              <Progress value={score * 100} className="h-2" />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function AIAnalysisResults({ analysis }: { analysis?: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Brain className="w-5 h-5 text-purple-600" />
          <span>AI Clinical Analysis</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {analysis ? (
          <div className="prose prose-sm max-w-none">
            <p className="text-muted-foreground whitespace-pre-wrap">{analysis}</p>
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>AI analysis not available</p>
            <p className="text-sm">Set up API key to enable AI-powered insights</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function SummaryResults({ results }: { results: ProcessingResult }) {
  const { features, staging, document } = results;
  
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Report Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{features?.cancer_type || 'Unknown'}</div>
              <div className="text-sm text-muted-foreground">Cancer Type</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{features?.tumor_size_cm || 0} cm</div>
              <div className="text-sm text-muted-foreground">Tumor Size</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{staging?.stage || 'Unknown'}</div>
              <div className="text-sm text-muted-foreground">Stage</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{document?.text_length || 0}</div>
              <div className="text-sm text-muted-foreground">Characters</div>
            </div>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <pre className="text-sm whitespace-pre-wrap font-mono">{summary}</pre>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}