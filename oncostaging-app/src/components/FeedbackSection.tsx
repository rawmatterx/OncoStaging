import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ThumbsUp, ThumbsDown, TrendingUp, TrendingDown, Minus, MessageSquare } from 'lucide-react';

interface FeedbackSectionProps {
  onFeedbackSubmit: (feedback: FeedbackData) => void;
}

interface FeedbackData {
  helpful: 'yes' | 'no';
  anxiety: 'increased' | 'decreased' | 'same';
  timestamp: string;
}

export function FeedbackSection({ onFeedbackSubmit }: FeedbackSectionProps) {
  const [helpful, setHelpful] = useState<'yes' | 'no' | null>(null);
  const [anxiety, setAnxiety] = useState<'increased' | 'decreased' | 'same' | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    if (helpful && anxiety) {
      const feedback: FeedbackData = {
        helpful,
        anxiety,
        timestamp: new Date().toISOString()
      };
      
      onFeedbackSubmit(feedback);
      setSubmitted(true);
      
      // Reset after 3 seconds
      setTimeout(() => {
        setSubmitted(false);
        setHelpful(null);
        setAnxiety(null);
      }, 3000);
    }
  };

  if (submitted) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <Card className="border-green-200 bg-green-50">
          <CardContent className="p-6 text-center">
            <div className="text-green-700">
              <MessageSquare className="w-8 h-8 mx-auto mb-2" />
              <h3 className="font-semibold">Thank you for your feedback!</h3>
              <p className="text-sm mt-1">Your input helps us improve the system.</p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <MessageSquare className="w-5 h-5 text-blue-600" />
          <span>Feedback</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Helpfulness */}
        <div className="space-y-3">
          <h4 className="font-medium">Was this analysis helpful?</h4>
          <div className="flex space-x-3">
            <Button
              variant={helpful === 'yes' ? 'default' : 'outline'}
              onClick={() => setHelpful('yes')}
              className="flex items-center space-x-2"
            >
              <ThumbsUp className="w-4 h-4" />
              <span>Yes</span>
            </Button>
            <Button
              variant={helpful === 'no' ? 'default' : 'outline'}
              onClick={() => setHelpful('no')}
              className="flex items-center space-x-2"
            >
              <ThumbsDown className="w-4 h-4" />
              <span>No</span>
            </Button>
          </div>
        </div>

        {/* Anxiety Level */}
        <div className="space-y-3">
          <h4 className="font-medium">After reading this information, your anxiety:</h4>
          <div className="flex space-x-3">
            <Button
              variant={anxiety === 'increased' ? 'destructive' : 'outline'}
              onClick={() => setAnxiety('increased')}
              className="flex items-center space-x-2"
            >
              <TrendingUp className="w-4 h-4" />
              <span>Increased</span>
            </Button>
            <Button
              variant={anxiety === 'decreased' ? 'default' : 'outline'}
              onClick={() => setAnxiety('decreased')}
              className="flex items-center space-x-2 bg-green-600 hover:bg-green-700"
            >
              <TrendingDown className="w-4 h-4" />
              <span>Decreased</span>
            </Button>
            <Button
              variant={anxiety === 'same' ? 'secondary' : 'outline'}
              onClick={() => setAnxiety('same')}
              className="flex items-center space-x-2"
            >
              <Minus className="w-4 h-4" />
              <span>Same</span>
            </Button>
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-4">
          <Button
            onClick={handleSubmit}
            disabled={!helpful || !anxiety}
            className="w-full"
          >
            Submit Feedback
          </Button>
        </div>

        {/* Privacy Notice */}
        <div className="text-xs text-muted-foreground text-center">
          Your feedback is anonymous and helps improve our system.
        </div>
      </CardContent>
    </Card>
  );
}