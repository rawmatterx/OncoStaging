import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, Circle, Clock } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface Step {
  id: number;
  title: string;
  description: string;
  icon: string;
}

interface ProcessingStepsProps {
  currentStep: number;
  completedSteps: number[];
}

const steps: Step[] = [
  {
    id: 1,
    title: 'Document Upload',
    description: 'Upload and validate your PET/CT report',
    icon: '📄'
  },
  {
    id: 2,
    title: 'OCR Processing',
    description: 'Extract text using advanced OCR technology',
    icon: '🔍'
  },
  {
    id: 3,
    title: 'Feature Extraction',
    description: 'Identify medical features and staging information',
    icon: '🧠'
  },
  {
    id: 4,
    title: 'TNM Staging',
    description: 'Calculate TNM staging based on extracted features',
    icon: '📊'
  },
  {
    id: 5,
    title: 'AI Analysis',
    description: 'Generate AI-powered clinical insights',
    icon: '🤖'
  }
];

export function ProcessingSteps({ currentStep, completedSteps }: ProcessingStepsProps) {
  const getStepStatus = (stepId: number) => {
    if (completedSteps.includes(stepId)) return 'completed';
    if (stepId === currentStep) return 'current';
    return 'pending';
  };

  const getStepIcon = (stepId: number, status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'current':
        return <Clock className="w-5 h-5 text-blue-600 animate-pulse" />;
      default:
        return <Circle className="w-5 h-5 text-gray-400" />;
    }
  };

  return (
    <Card className="w-full">
      <CardContent className="p-6">
        <h3 className="text-lg font-semibold mb-6">Processing Pipeline</h3>
        
        <div className="space-y-4">
          {steps.map((step, index) => {
            const status = getStepStatus(step.id);
            const isLast = index === steps.length - 1;

            return (
              <div key={step.id} className="relative">
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center space-x-4"
                >
                  <div className="flex-shrink-0">
                    {getStepIcon(step.id, status)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <h4 className={`font-medium ${
                        status === 'completed' ? 'text-green-700' :
                        status === 'current' ? 'text-blue-700' :
                        'text-gray-500'
                      }`}>
                        {step.icon} {step.title}
                      </h4>
                      
                      <Badge 
                        variant={
                          status === 'completed' ? 'success' :
                          status === 'current' ? 'default' :
                          'secondary'
                        }
                      >
                        {status === 'completed' ? 'Done' :
                         status === 'current' ? 'Processing' :
                         'Pending'}
                      </Badge>
                    </div>
                    
                    <p className="text-sm text-muted-foreground mt-1">
                      {step.description}
                    </p>
                  </div>
                </motion.div>

                {!isLast && (
                  <div className="ml-2.5 mt-2 mb-2">
                    <div className={`w-0.5 h-6 ${
                      completedSteps.includes(step.id) ? 'bg-green-300' : 'bg-gray-200'
                    }`} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}