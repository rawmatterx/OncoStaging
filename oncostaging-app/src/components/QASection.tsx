import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { MessageCircle, Send, Bot, User } from 'lucide-react';
import { ProcessingResult } from '@/types/medical';

interface QASectionProps {
  results: ProcessingResult;
}

interface QAMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const predefinedQuestions = [
  "🧾 What is my cancer stage?",
  "💊 What treatment is usually given?",
  "🧠 What does this mean in simple terms?",
  "📋 What are the next steps?",
];

export function QASection({ results }: QASectionProps) {
  const [messages, setMessages] = useState<QAMessage[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleQuestionSelect = (question: string) => {
    setCurrentQuestion(question.replace(/^[🧾💊🧠📋]\s/, ''));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentQuestion.trim() || isLoading) return;

    const userMessage: QAMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: currentQuestion,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Simulate AI response (in real app, this would call your AI service)
    setTimeout(() => {
      const answer = generateAnswer(currentQuestion, results);
      const assistantMessage: QAMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: answer,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
      setCurrentQuestion('');
    }, 1500);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <MessageCircle className="w-5 h-5 text-blue-600" />
          <span>Ask Questions</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Predefined Questions */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground">Quick Questions:</h4>
          <div className="flex flex-wrap gap-2">
            {predefinedQuestions.map((question, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => handleQuestionSelect(question)}
                className="text-left justify-start"
              >
                {question}
              </Button>
            ))}
          </div>
        </div>

        {/* Chat Messages */}
        <div className="space-y-4 max-h-96 overflow-y-auto">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex items-start space-x-2 max-w-[80%] ${
                  message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                }`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    message.type === 'user' ? 'bg-blue-100' : 'bg-green-100'
                  }`}>
                    {message.type === 'user' ? (
                      <User className="w-4 h-4 text-blue-600" />
                    ) : (
                      <Bot className="w-4 h-4 text-green-600" />
                    )}
                  </div>
                  
                  <div className={`rounded-lg p-3 ${
                    message.type === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-900'
                  }`}>
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    <p className="text-xs opacity-70 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="flex items-start space-x-2">
                <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-green-600" />
                </div>
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>

        {/* Question Input */}
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <Input
            value={currentQuestion}
            onChange={(e) => setCurrentQuestion(e.target.value)}
            placeholder="Ask a question about your report..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button type="submit" disabled={isLoading || !currentQuestion.trim()}>
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function generateAnswer(question: string, results: ProcessingResult): string {
  const { features, staging } = results;
  const questionLower = question.toLowerCase();

  if (questionLower.includes('stage')) {
    return `Your cancer is staged as **${staging?.stage || 'Unknown'}**. This means ${staging?.description || 'staging information is not available'}.`;
  } else if (questionLower.includes('treatment')) {
    return `Based on your ${features?.cancer_type || 'cancer'} diagnosis at ${staging?.stage || 'unknown stage'}, treatment typically involves a multidisciplinary approach. Please consult with your oncologist for specific treatment recommendations tailored to your case.`;
  } else if (questionLower.includes('mean') || questionLower.includes('simple')) {
    return `According to your report, this is **${staging?.stage || 'Unknown'} ${features?.cancer_type || 'cancer'}**.\n\n${staging?.description || 'More information needed for detailed explanation.'}\n\n⚠️ Please consult your oncologist for final medical decisions.`;
  } else if (questionLower.includes('next steps')) {
    return `Based on your staging results, typical next steps may include:\n\n• Consultation with oncology team\n• Additional imaging or tests if needed\n• Discussion of treatment options\n• Second opinion if desired\n\n⚠️ Your healthcare team will provide specific recommendations based on your complete medical history.`;
  } else {
    return `Thank you for your question. Based on your report showing ${features?.cancer_type || 'cancer'} at ${staging?.stage || 'unknown stage'}, I recommend discussing this specific question with your healthcare team who can provide personalized medical advice.\n\n⚠️ This system provides general information only and should not replace professional medical consultation.`;
  }
}