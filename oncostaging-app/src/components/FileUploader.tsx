import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Image, AlertCircle, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { formatFileSize } from '@/lib/utils';

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
  isProcessing: boolean;
  processingProgress?: number;
}

export function FileUploader({ onFileSelect, isProcessing, processingProgress = 0 }: FileUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string>('');

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    setError('');
    
    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.errors[0]?.code === 'file-too-large') {
        setError('File is too large. Maximum size is 50MB.');
      } else if (rejection.errors[0]?.code === 'file-invalid-type') {
        setError('Invalid file type. Please upload PDF, DOCX, or image files.');
      } else {
        setError('File upload failed. Please try again.');
      }
      return;
    }

    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setSelectedFile(file);
      setError('');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'image/*': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: false
  });

  const handleProcess = () => {
    if (selectedFile) {
      onFileSelect(selectedFile);
    }
  };

  const getFileIcon = (file: File) => {
    if (file.type === 'application/pdf' || file.type.includes('document')) {
      return <FileText className="w-8 h-8 text-blue-500" />;
    }
    return <Image className="w-8 h-8 text-green-500" />;
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      <Card className="border-2 border-dashed transition-colors duration-200 hover:border-primary/50">
        <CardContent className="p-8">
          <div
            {...getRootProps()}
            className={`cursor-pointer transition-all duration-200 ${
              isDragActive ? 'scale-105' : ''
            }`}
          >
            <input {...getInputProps()} />
            
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center space-y-4"
            >
              <div className="flex justify-center">
                <motion.div
                  animate={isDragActive ? { scale: 1.1, rotate: 5 } : { scale: 1, rotate: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <Upload className={`w-12 h-12 ${isDragActive ? 'text-primary' : 'text-muted-foreground'}`} />
                </motion.div>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold mb-2">
                  {isDragActive ? 'Drop your file here' : 'Upload PET/CT Report'}
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Drag and drop your file here, or click to browse
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  <Badge variant="outline">PDF</Badge>
                  <Badge variant="outline">DOCX</Badge>
                  <Badge variant="outline">Images</Badge>
                </div>
              </div>
            </motion.div>
          </div>
        </CardContent>
      </Card>

      <AnimatePresence>
        {selectedFile && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getFileIcon(selectedFile)}
                    <div>
                      <p className="font-medium">{selectedFile.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatFileSize(selectedFile.size)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {!isProcessing && (
                      <Button onClick={handleProcess} className="bg-blue-600 hover:bg-blue-700">
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Process Document
                      </Button>
                    )}
                  </div>
                </div>

                {isProcessing && (
                  <div className="mt-4 space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Processing document...</span>
                      <span>{processingProgress}%</span>
                    </div>
                    <Progress value={processingProgress} className="w-full" />
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Card className="border-red-200 bg-red-50">
              <CardContent className="p-4">
                <div className="flex items-center space-x-2 text-red-700">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-sm">{error}</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}