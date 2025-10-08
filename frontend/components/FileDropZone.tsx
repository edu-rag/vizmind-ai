'use client';

import { useCallback, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useDropzone } from 'react-dropzone';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress-simple';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Upload,
  FileText,
  AlertCircle,
  CheckCircle2,
  X,
  RotateCw,
  Scissors,
  Merge,
  Download,
  Eye,
  Trash2,
  Plus,
  File,
  Sparkles
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { generateHierarchicalMindMap } from '@/lib/api';
import { toast } from 'sonner';
import { AuthDialog } from './AuthDialog';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import Confetti from 'react-confetti';

interface UploadedFile {
  id: string;
  file: File;
  preview?: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  error?: string;
}

interface PDFTransformation {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
  action: () => void;
}

export function FileDropZone() {
  const router = useRouter();
  const {
    isAuthenticated,
    jwt,
    setCurrentMindMap,
    addToHistory,
  } = useAppStore();

  const [showAuthDialog, setShowAuthDialog] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [dragDepth, setDragDepth] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    // Set window size for confetti
    setWindowSize({
      width: window.innerWidth,
      height: window.innerHeight
    });

    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const transformations: PDFTransformation[] = [
    {
      id: 'merge',
      name: 'Merge PDFs',
      icon: <Merge className="h-4 w-4" />,
      description: 'Combine multiple PDFs into one',
      action: () => handleMergePDFs(),
    },
    {
      id: 'split',
      name: 'Split PDF',
      icon: <Scissors className="h-4 w-4" />,
      description: 'Split PDF into separate pages',
      action: () => handleSplitPDF(),
    },
    {
      id: 'rotate',
      name: 'Rotate Pages',
      icon: <RotateCw className="h-4 w-4" />,
      description: 'Rotate PDF pages 90°, 180°, or 270°',
      action: () => handleRotatePDF(),
    },
  ];

  const addFilesAsPending = (files: File[]) => {
    const newFiles: UploadedFile[] = files.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      status: 'pending' as const,
      progress: 0,
    }));
    setUploadedFiles(prev => [...prev, ...newFiles]);
  };

  const processBatchFiles = async (files: File[]) => {
    if (!jwt) return;

    // Create uploadedFile entries for all files
    const newFiles: UploadedFile[] = files.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      status: 'processing' as const,
      progress: 0,
    }));

    setUploadedFiles(prev => [...prev, ...newFiles]);
    setIsProcessing(true);

    // Simulate upload progress for all files
    const progressInterval = setInterval(() => {
      setUploadedFiles(prev => prev.map(f =>
        newFiles.some(nf => nf.id === f.id)
          ? { ...f, progress: Math.min(f.progress + Math.random() * 15 + 5, 90) }
          : f
      ));
    }, 500);

    try {
      toast.success(`Processing ${files.length} PDF${files.length > 1 ? 's' : ''}...`, {
        description: files.length > 1 ? 'Creating mind map from first file' : 'Creating hierarchical mind map',
      });

      const result = await generateHierarchicalMindMap(files[0], jwt);

      clearInterval(progressInterval);

      if (result.error) {
        setUploadedFiles(prev => prev.map(f =>
          newFiles.some(nf => nf.id === f.id)
            ? { ...f, status: 'error', progress: 0, error: 'Processing failed' }
            : f
        ));
        toast.error('Failed to process PDFs');
        return;
      }

      if (result.data) {
        const mindMapData = result.data;

        setUploadedFiles(prev => prev.map(f =>
          newFiles.some(nf => nf.id === f.id)
            ? { ...f, status: 'completed', progress: 100 }
            : f
        ));

        // Set the hierarchical mind map
        setCurrentMindMap(mindMapData);

        // Show confetti celebration
        setShowConfetti(true);
        setTimeout(() => setShowConfetti(false), 5000);

        toast.success('Hierarchical mind map created!', {
          description: files.length > 1
            ? `Processed ${files[0].name}. Multiple file support coming soon.`
            : 'Your document has been transformed into an interactive mind map',
        });

        // Navigate to view the map
        router.push('/');
      }
    } catch (error) {
      clearInterval(progressInterval);
      setUploadedFiles(prev => prev.map(f =>
        newFiles.some(nf => nf.id === f.id)
          ? { ...f, status: 'error', progress: 0, error: 'Network error' }
          : f
      ));
      toast.error('Network error occurred');
      console.error('Error processing files:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const processFile = async (file: File) => {
    if (!jwt) return;

    const fileId = Math.random().toString(36).substr(2, 9);

    // Add file to uploaded files list
    const newFile: UploadedFile = {
      id: fileId,
      file,
      status: 'processing',
      progress: 0,
    };

    setUploadedFiles(prev => [...prev, newFile]);
    setIsProcessing(true);

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadedFiles(prev => prev.map(f =>
        f.id === fileId
          ? { ...f, progress: Math.min(f.progress + Math.random() * 15 + 5, 90) }
          : f
      ));
    }, 500);

    try {
      toast.success('Processing your PDF...', {
        description: 'Creating hierarchical mind map',
      });

      const result = await generateHierarchicalMindMap(file, jwt);

      clearInterval(progressInterval);

      if (result.error) {
        setUploadedFiles(prev => prev.map(f =>
          f.id === fileId
            ? { ...f, status: 'error', progress: 0, error: 'Processing failed' }
            : f
        ));
        toast.error('Failed to process PDF');
        return;
      }

      if (result.data) {
        const mindMapData = result.data;

        setUploadedFiles(prev => prev.map(f =>
          f.id === fileId
            ? { ...f, status: 'completed', progress: 100 }
            : f
        ));

        // Set the hierarchical mind map
        setCurrentMindMap(mindMapData);

        // Show confetti celebration
        setShowConfetti(true);
        setTimeout(() => setShowConfetti(false), 5000);

        toast.success('Hierarchical mind map created!', {
          description: 'Your document has been transformed into an interactive mind map',
        });

        // Navigate to view the map
        router.push('/');
      }
    } catch (error) {
      clearInterval(progressInterval);
      setUploadedFiles(prev => prev.map(f =>
        f.id === fileId
          ? { ...f, status: 'error', progress: 0, error: 'Upload failed' }
          : f
      ));
      toast.error('Upload failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    // Handle rejected files
    rejectedFiles.forEach(({ file, errors }) => {
      errors.forEach((error: any) => {
        if (error.code === 'file-too-large') {
          toast.error(`File "${file.name}" is too large`, {
            description: 'Maximum file size is 10MB',
          });
        } else if (error.code === 'file-invalid-type') {
          toast.error(`File "${file.name}" is not a PDF`, {
            description: 'Only PDF files are supported',
          });
        }
      });
    });

    // Add accepted files as pending, let user decide when to process
    if (acceptedFiles.length > 0) {
      if (!isAuthenticated) {
        setShowAuthDialog(true);
        return;
      }
      addFilesAsPending(acceptedFiles);
      toast.success(`Added ${acceptedFiles.length} file${acceptedFiles.length > 1 ? 's' : ''} to queue`, {
        description: 'Click "Process All" to create your concept map',
      });
    }
  }, [isAuthenticated]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    onDragEnter: () => setDragDepth(prev => prev + 1),
    onDragLeave: () => setDragDepth(prev => prev - 1),
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: true,
    maxSize: 10 * 1024 * 1024, // 10MB
    disabled: false,
  });

  const handleAuthSuccess = () => {
    // Process any pending files after authentication
    toast.success('Signed in successfully!', {
      description: 'You can now upload and transform PDFs',
    });
  };

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const retryFile = (fileId: string) => {
    const file = uploadedFiles.find(f => f.id === fileId);
    if (file) {
      removeFile(fileId);
      processFile(file.file);
    }
  };

  const previewFile = (file: UploadedFile) => {
    // Create a blob URL for PDF preview
    const url = URL.createObjectURL(file.file);
    window.open(url, '_blank');
  };

  const downloadFile = (file: UploadedFile) => {
    const url = URL.createObjectURL(file.file);
    const a = document.createElement('a');
    a.href = url;
    a.download = file.file.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleMergePDFs = () => {
    const pdfFiles = uploadedFiles.filter(f => f.status === 'completed');
    if (pdfFiles.length < 2) {
      toast.error('Select at least 2 PDFs to merge');
      return;
    }
    toast.info('PDF merge feature coming soon!');
  };

  const handleSplitPDF = () => {
    const pdfFiles = uploadedFiles.filter(f => f.status === 'completed');
    if (pdfFiles.length === 0) {
      toast.error('Select a PDF to split');
      return;
    }
    toast.info('PDF split feature coming soon!');
  };

  const handleRotatePDF = () => {
    const pdfFiles = uploadedFiles.filter(f => f.status === 'completed');
    if (pdfFiles.length === 0) {
      toast.error('Select a PDF to rotate');
      return;
    }
    toast.info('PDF rotation feature coming soon!');
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <>
      {/* Confetti for success celebration */}
      {showConfetti && (
        <Confetti
          width={windowSize.width}
          height={windowSize.height}
          recycle={false}
          numberOfPieces={500}
          gravity={0.3}
        />
      )}

      {/* Authentication Notice */}
      {!isAuthenticated && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card className="p-4 mb-4 md:p-6 gradient-ai-subtle border-primary/30 shadow-lg">
            <div className="flex items-center space-x-4">
              <motion.div
                className="w-10 h-10 gradient-ai rounded-full flex items-center justify-center flex-shrink-0"
                animate={{ rotate: [0, 5, -5, 0] }}
                transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
              >
                <Sparkles className="h-5 w-5 text-white" />
              </motion.div>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-foreground">
                  Sign in to unlock VizMind AI
                </h4>
                <p className="text-xs text-muted-foreground mt-1">
                  Create mind maps, save your work, and access AI-powered insights
                </p>
              </div>
              <Button
                onClick={() => setShowAuthDialog(true)}
                size="sm"
                className="gradient-ai text-white hover:opacity-90 shadow-md"
              >
                Sign In
              </Button>
            </div>
          </Card>
        </motion.div>
      )}
      <div className="space-y-6">
        {/* Main Drop Zone */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Card
            {...getRootProps()}
            className={cn(
              'relative overflow-hidden border-2 border-dashed transition-all duration-300 cursor-pointer group',
              'focus-visible-ring min-h-[200px] md:min-h-[280px]',
              // Base styles
              'bg-gradient-to-br from-background via-background to-muted/10',
              // Drag states
              isDragActive && !isDragReject && 'border-primary bg-primary/5 shadow-2xl scale-[1.02] glow-ai',
              isDragReject && 'border-destructive bg-destructive/5 shadow-xl',
              // Hover states
              !isDragActive && 'border-muted-foreground/25 hover:border-primary/50 hover:bg-accent/30 hover:shadow-lg'
            )}
            role="button"
            tabIndex={0}
            aria-label="Upload PDF files"
          >
            {/* Animated background effect */}
            {isDragActive && !isDragReject && (
              <motion.div
                className="absolute inset-0 gradient-ai opacity-10"
                animate={{
                  scale: [1, 1.1, 1],
                  opacity: [0.1, 0.2, 0.1]
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              />
            )}

            <div className="relative p-6 md:p-8">
              <div className="text-center space-y-6">
                {/* Upload Icon */}
                <div className="relative">
                  <motion.div
                    className={cn(
                      'w-20 h-20 md:w-24 md:h-24 mx-auto rounded-3xl flex items-center justify-center transition-all duration-300 shadow-xl',
                      isDragActive && !isDragReject
                        ? 'gradient-ai text-white'
                        : isDragReject
                          ? 'bg-destructive/20 text-destructive'
                          : 'gradient-ai-subtle text-primary group-hover:shadow-2xl'
                    )}
                    animate={isDragActive && !isDragReject ? {
                      y: [0, -10, 0],
                      rotate: [0, 5, -5, 0]
                    } : {}}
                    transition={{
                      duration: 1.5,
                      repeat: isDragActive ? Infinity : 0,
                      ease: "easeInOut"
                    }}
                  >
                    {isDragActive && !isDragReject && (
                      <motion.div
                        className="absolute inset-0 rounded-3xl border-4 border-primary/30"
                        animate={{
                          scale: [1, 1.2, 1],
                          opacity: [0.5, 0, 0.5]
                        }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          ease: "easeInOut"
                        }}
                      />
                    )}
                    <Upload
                      className={cn(
                        'transition-all duration-300',
                        isDragActive && !isDragReject ? 'h-12 w-12 md:h-14 md:w-14' : 'h-10 w-10 md:h-12 md:w-12'
                      )}
                    />
                  </motion.div>
                </div>

                {/* Content */}
                <motion.div
                  className="space-y-4"
                  animate={isDragActive ? { scale: 1.02 } : { scale: 1 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="space-y-3">
                    <h3 className="text-xl md:text-2xl font-bold text-foreground">
                      {isDragActive && !isDragReject ? (
                        <motion.span
                          className="gradient-text inline-block"
                          animate={{ scale: [1, 1.05, 1] }}
                          transition={{ duration: 1, repeat: Infinity }}
                        >
                          Drop your PDFs here
                        </motion.span>
                      ) : isDragReject ? (
                        <span className="text-destructive">Invalid files</span>
                      ) : (
                        'Upload PDF Documents'
                      )}
                    </h3>
                    <p className="text-sm md:text-base text-muted-foreground max-w-md mx-auto leading-relaxed">
                      {isDragReject
                        ? 'Only PDF files up to 10MB are supported'
                        : 'Upload multiple PDFs to create a unified concept map. All documents will be analyzed together to find connections and relationships across your content.'
                      }
                    </p>
                  </div>

                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Button
                      size="lg"
                      className="px-6 md:px-8 py-3 font-medium gradient-ai text-white hover:opacity-90 shadow-lg transition-all"
                    >
                      <Plus className="mr-2 h-4 w-4 md:h-5 md:w-5" />
                      Choose PDF Files
                    </Button>
                  </motion.div>

                  <div className="flex items-center justify-center space-x-3 text-xs md:text-sm text-muted-foreground">
                    <Badge variant="secondary" className="text-xs">PDF only</Badge>
                    <Badge variant="secondary" className="text-xs">Max 10MB</Badge>
                    <Badge variant="secondary" className="text-xs">Multiple files</Badge>
                  </div>
                </motion.div>
              </div>
            </div>

            <input {...getInputProps()} />
          </Card>
        </motion.div>

        {/* Uploaded Files List */}
        <AnimatePresence>
          {uploadedFiles.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Card className="p-4 md:p-6 border-2">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-lg font-semibold text-foreground flex items-center gap-2">
                      <FileText className="h-5 w-5 text-primary" />
                      Uploaded Files ({uploadedFiles.length})
                    </h4>
                    <div className="flex gap-2">
                      {uploadedFiles.some(f => f.status === 'pending') && (
                        <motion.div
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          <Button
                            variant="default"
                            size="sm"
                            onClick={() => {
                              const pendingFiles = uploadedFiles
                                .filter(f => f.status === 'pending');
                              if (pendingFiles.length > 0) {
                                // Remove pending files before processing
                                setUploadedFiles(prev =>
                                  prev.filter(f => f.status !== 'pending')
                                );
                                processBatchFiles(pendingFiles.map(f => f.file));
                              }
                            }}
                            disabled={isProcessing}
                            className="gradient-ai text-white hover:opacity-90 shadow-md"
                          >
                            <Sparkles className="mr-2 h-4 w-4" />
                            Process All ({uploadedFiles.filter(f => f.status === 'pending').length})
                          </Button>
                        </motion.div>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setUploadedFiles([])}
                        className="text-muted-foreground hover:text-foreground"
                      >
                        Clear All
                      </Button>
                    </div>
                  </div>

                  <ScrollArea className="max-h-96">
                    <div className="space-y-3">
                      <AnimatePresence>
                        {uploadedFiles.map((file, index) => (
                          <motion.div
                            key={file.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            transition={{ duration: 0.2, delay: index * 0.05 }}
                            className="flex items-center space-x-3 p-4 bg-muted/30 rounded-xl border border-border hover:border-primary/30 transition-colors"
                          >
                            {/* File Icon */}
                            <div className={cn(
                              'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
                              file.status === 'completed' && 'bg-green-100 dark:bg-green-900/30',
                              file.status === 'processing' && 'bg-blue-100 dark:bg-blue-900/30',
                              file.status === 'error' && 'bg-red-100 dark:bg-red-900/30',
                              file.status === 'pending' && 'bg-gray-100 dark:bg-gray-900/30'
                            )}>
                              <FileText className={cn(
                                'h-5 w-5',
                                file.status === 'completed' && 'text-green-600 dark:text-green-400',
                                file.status === 'processing' && 'text-blue-600 dark:text-blue-400',
                                file.status === 'error' && 'text-red-600 dark:text-red-400',
                                file.status === 'pending' && 'text-gray-600 dark:text-gray-400'
                              )} />
                            </div>

                            {/* File Info */}
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-foreground truncate text-start">
                                {file.file.name}
                              </p>
                              <div className="flex items-center space-x-2 mt-1">
                                <p className="text-xs text-muted-foreground">
                                  {formatFileSize(file.file.size)}
                                </p>
                                <Badge
                                  variant={
                                    file.status === 'completed' ? 'default' :
                                      file.status === 'processing' ? 'secondary' :
                                        file.status === 'error' ? 'destructive' : 'outline'
                                  }
                                  className="text-xs"
                                >
                                  {file.status === 'completed' && 'Ready'}
                                  {file.status === 'processing' && 'Processing...'}
                                  {file.status === 'error' && 'Failed'}
                                  {file.status === 'pending' && 'Pending'}
                                </Badge>
                              </div>

                              {/* Progress Bar */}
                              {file.status === 'processing' && (
                                <Progress value={file.progress} className="mt-2 h-1" />
                              )}

                              {/* Error Message */}
                              {file.status === 'error' && file.error && (
                                <p className="text-xs text-destructive mt-1">{file.error}</p>
                              )}
                            </div>

                            {/* Actions */}
                            <div className="flex items-center space-x-1 flex-shrink-0">
                              {file.status === 'completed' && (
                                <>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => previewFile(file)}
                                    className="h-8 w-8"
                                    aria-label="Preview file"
                                  >
                                    <Eye className="h-4 w-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => downloadFile(file)}
                                    className="h-8 w-8"
                                    aria-label="Download file"
                                  >
                                    <Download className="h-4 w-4" />
                                  </Button>
                                </>
                              )}

                              {file.status === 'error' && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => retryFile(file.id)}
                                  className="h-8 w-8 text-blue-600 hover:text-blue-700"
                                  aria-label="Retry upload"
                                >
                                  <RotateCw className="h-4 w-4" />
                                </Button>
                              )}

                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => removeFile(file.id)}
                                className="h-8 w-8 text-destructive hover:text-destructive/80"
                                aria-label="Remove file"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </motion.div>
                        ))}
                      </AnimatePresence>
                    </div>
                  </ScrollArea>
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* PDF Transformations */}
        {uploadedFiles.some(f => f.status === 'completed') && (
          <Card className="p-4 md:p-6">
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-foreground">
                PDF Tools & Transformations
              </h4>
              <p className="text-sm text-muted-foreground">
                Transform your uploaded PDFs with these handy tools
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {transformations.map((transform) => (
                  <Button
                    key={transform.id}
                    variant="outline"
                    className="h-auto p-4 flex flex-col items-center space-y-2 hover:bg-accent/50"
                    onClick={transform.action}
                  >
                    <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
                      {transform.icon}
                    </div>
                    <div className="text-center">
                      <p className="font-medium text-sm">{transform.name}</p>
                      <p className="text-xs text-muted-foreground">{transform.description}</p>
                    </div>
                  </Button>
                ))}
              </div>
            </div>
          </Card>
        )}
      </div>

      <AuthDialog
        open={showAuthDialog}
        onOpenChange={setShowAuthDialog}
        onSuccess={handleAuthSuccess}
      />
    </>
  );
}