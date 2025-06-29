'use client';

import { useCallback, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useDropzone } from 'react-dropzone';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
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
  File
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { generateConceptMap } from '@/lib/api';
import { toast } from 'sonner';
import { AuthDialog } from './AuthDialog';
import { cn } from '@/lib/utils';

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
    setCurrentMap,
    addToHistory,
  } = useAppStore();

  const [showAuthDialog, setShowAuthDialog] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [dragDepth, setDragDepth] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);

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
        description: 'Creating unified concept map',
      });

      const result = await generateConceptMap(files, jwt);

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
        const mapData = result.data;

        if (mapData.status === 'success') {
          setUploadedFiles(prev => prev.map(f =>
            newFiles.some(nf => nf.id === f.id)
              ? { ...f, status: 'completed', progress: 100 }
              : f
          ));

          // Create title from attachments
          const attachmentNames = mapData.attachments?.map((att: any) => att.filename) || [];
          const title = attachmentNames.length > 1
            ? `${attachmentNames[0]} + ${attachmentNames.length - 1} more`
            : attachmentNames[0] || 'Unified Concept Map';

          const newMap = {
            mongodb_doc_id: mapData.mongodb_doc_id,
            react_flow_data: mapData.react_flow_data,
            source_filename: title,
            attachments: mapData.attachments,
          };

          setCurrentMap(newMap);

          addToHistory({
            map_id: mapData.mongodb_doc_id,
            source_filename: title,
            created_at: new Date().toISOString(),
            attachments: mapData.attachments,
          });

          if (mapData.mongodb_doc_id) {
            router.push(`/maps/${mapData.mongodb_doc_id}`);
            toast.success('Concept map created successfully!');
          }
        } else {
          setUploadedFiles(prev => prev.map(f =>
            newFiles.some(nf => nf.id === f.id)
              ? { ...f, status: 'error', progress: 0, error: mapData.error_message || 'Processing failed' }
              : f
          ));
          toast.error('Failed to create concept map', {
            description: mapData.error_message,
          });
        }
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
        description: 'Creating interactive concept map',
      });

      const result = await generateConceptMap([file], jwt);

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

      if (result.data?.results?.[0]) {
        const mapData = result.data.results[0];

        if (mapData.status === 'success') {
          setUploadedFiles(prev => prev.map(f =>
            f.id === fileId
              ? { ...f, status: 'completed', progress: 100 }
              : f
          ));

          const newMap = {
            mongodb_doc_id: mapData.mongodb_doc_id,
            react_flow_data: mapData.react_flow_data,
            source_filename: mapData.filename,
          };

          setCurrentMap(newMap);

          addToHistory({
            map_id: mapData.mongodb_doc_id,
            source_filename: mapData.filename,
            created_at: new Date().toISOString(),
          });

          toast.success('Concept map created!', {
            description: 'Click to view your interactive map',
            action: {
              label: 'View Map',
              onClick: () => router.push(`/maps/${mapData.mongodb_doc_id}`),
            },
          });
        } else {
          setUploadedFiles(prev => prev.map(f =>
            f.id === fileId
              ? { ...f, status: 'error', progress: 0, error: 'Processing failed' }
              : f
          ));
          toast.error('Failed to process PDF');
        }
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

      {/* Authentication Notice */}
      {!isAuthenticated && (
        <Card className="p-4 mb-4 md:p-6 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/20 border-amber-200 dark:border-amber-800">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-amber-100 dark:bg-amber-900/30 rounded-full flex items-center justify-center flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-amber-900 dark:text-amber-100">
                Sign in to unlock all features
              </h4>
              <p className="text-xs text-amber-700 dark:text-amber-200 mt-1">
                Create concept maps, save your work, and access advanced PDF tools
              </p>
            </div>
            <Button
              onClick={() => setShowAuthDialog(true)}
              size="sm"
              className="bg-amber-600 hover:bg-amber-700 text-white"
            >
              Sign In
            </Button>
          </div>
        </Card>
      )}
      <div className="space-y-6">
        {/* Main Drop Zone */}
        <Card
          {...getRootProps()}
          className={cn(
            'relative overflow-hidden border-2 border-dashed transition-all duration-300 cursor-pointer group',
            'focus-visible-ring min-h-[200px] md:min-h-[300px]',
            // Base styles
            'bg-gradient-to-br from-background via-background to-muted/10',
            // Drag states
            isDragActive && !isDragReject && 'border-primary bg-primary/5 shadow-lg scale-[1.02]',
            isDragReject && 'border-destructive bg-destructive/5',
            // Hover states
            !isDragActive && 'border-muted-foreground/25 hover:border-primary/50 hover:bg-accent/30 hover:shadow-md'
          )}
          role="button"
          tabIndex={0}
          aria-label="Upload PDF files"
        >
          <div className="relative p-6 md:p-8">
            <div className="text-center space-y-6">
              {/* Upload Icon */}
              <div className="relative">
                <div className={cn(
                  'w-16 h-16 md:w-20 md:h-20 mx-auto rounded-full flex items-center justify-center transition-all duration-500',
                  isDragActive && !isDragReject
                    ? 'bg-primary/20 text-primary scale-110'
                    : isDragReject
                      ? 'bg-destructive/20 text-destructive'
                      : 'bg-primary/10 text-primary hover:bg-primary/15 hover:scale-105'
                )}>
                  {isDragActive && !isDragReject && (
                    <div className="absolute inset-0 rounded-full border-2 border-primary/30 animate-ping" />
                  )}
                  <Upload className={cn(
                    'transition-all duration-300',
                    isDragActive && !isDragReject ? 'h-10 w-10 md:h-12 md:w-12' : 'h-8 w-8 md:h-10 md:w-10'
                  )} />
                </div>
              </div>

              {/* Content */}
              <div className="space-y-8">
                <div className="space-y-4">
                  <h3 className="text-xl md:text-2xl font-bold text-foreground">
                    {isDragActive && !isDragReject ? (
                      <span className="text-primary">Drop your PDFs here</span>
                    ) : isDragReject ? (
                      <span className="text-destructive">Invalid files</span>
                    ) : (
                      'Upload PDF Documents'
                    )}
                  </h3>
                  <p className="text-sm md:text-base text-muted-foreground max-w-md mx-auto">
                    {isDragReject
                      ? 'Only PDF files up to 10MB are supported'
                      : 'Upload multiple PDFs to create a unified concept map. All documents will be analyzed together to find connections and relationships across your content.'
                    }
                  </p>
                </div>

                <Button
                  size="lg"
                  className="px-6 md:px-8 py-3 font-medium bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  <Plus className="mr-2 h-4 w-4 md:h-5 md:w-5" />
                  Choose PDF Files
                </Button>

                <div className="flex items-center justify-center space-x-4 text-xs md:text-sm mt text-muted-foreground">
                  <span>PDF only</span>
                  <span>•</span>
                  <span>Max 10MB each</span>
                  <span>•</span>
                  <span>Multiple files</span>
                </div>
              </div>
            </div>
          </div>

          <input {...getInputProps()} />
        </Card>

        {/* Uploaded Files List */}
        {uploadedFiles.length > 0 && (
          <Card className="p-4 md:p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-lg font-semibold text-foreground">
                  Uploaded Files ({uploadedFiles.length})
                </h4>
                <div className="flex gap-2">
                  {uploadedFiles.some(f => f.status === 'pending') && (
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
                      className="bg-primary text-primary-foreground hover:bg-primary/90"
                    >
                      Process All ({uploadedFiles.filter(f => f.status === 'pending').length})
                    </Button>
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

              <ScrollArea className="max-h-64">
                <div className="space-y-3">
                  {uploadedFiles.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center space-x-3 p-3 bg-muted/30 rounded-lg border border-border"
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
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </Card>
        )}

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