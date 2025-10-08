'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle, DrawerDescription } from '@/components/ui/drawer';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Send,
  ExternalLink,
  Loader2,
  Sparkles,
  MessageSquare,
  BookOpen,
  Trash2,
  Bot,
  User as UserIcon,
  X
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { askQuestionWithHistory, deleteChatHistory } from '@/lib/api';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

export function NodeDetailPanel() {
  const {
    selectedNodeData,
    isDetailPanelOpen,
    setDetailPanelOpen,
    currentMindMap,
    jwt,
  } = useAppStore();

  const [isLoading, setIsLoading] = useState(false);
  const [initialAnswer, setInitialAnswer] = useState<string | null>(null);
  const [initialCitedSources, setInitialCitedSources] = useState<any[]>([]);
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(null);
  const [lastQuestionAnswer, setLastQuestionAnswer] = useState<{
    question: string;
    answer: string;
    citedSources: any[];
  } | null>(null);
  const [question, setQuestion] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState<string>('');
  const [isMobile, setIsMobile] = useState(false);
  const [activeTab, setActiveTab] = useState('details');
  const conversationEndRef = useRef<HTMLDivElement>(null);
  const questionInputRef = useRef<HTMLInputElement>(null);
  const isLoadingRef = useRef(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleGetNodeDetails = useCallback(async () => {
    if (!currentMindMap || !jwt || !selectedNodeData || isLoadingRef.current) return;

    const nodeQuery = `What is ${selectedNodeData.data.label}? Provide detailed information about this concept.`;

    isLoadingRef.current = true;
    setIsLoading(true);

    try {
      const result = await askQuestionWithHistory(
        currentMindMap.mongodb_doc_id,
        nodeQuery,
        jwt,
        selectedNodeData.id,
        selectedNodeData.data.label
      );

      if (result.data) {
        setInitialAnswer(result.data.answer);
        setInitialCitedSources(result.data.cited_sources || []);
      } else {
        toast.error('Failed to get node details');
      }
    } catch (error) {
      toast.error('Failed to fetch node details');
      console.error('Node details error:', error);
    } finally {
      isLoadingRef.current = false;
      setIsLoading(false);
    }
  }, [currentMindMap, jwt, selectedNodeData]);

  useEffect(() => {
    if (selectedNodeData && currentMindMap && jwt) {
      handleGetNodeDetails();
    }
  }, [selectedNodeData, currentMindMap, jwt, handleGetNodeDetails]);

  useEffect(() => {
    if (isDetailPanelOpen && selectedNodeData) {
      if (currentNodeId !== selectedNodeData.id) {
        setInitialAnswer(null);
        setInitialCitedSources([]);
        setLastQuestionAnswer(null);
        setCurrentQuestion('');
        setCurrentNodeId(selectedNodeData.id);
        setActiveTab('details');
      }
    }
  }, [isDetailPanelOpen, selectedNodeData, currentNodeId]);

  useEffect(() => {
    if (!selectedNodeData) {
      setInitialAnswer(null);
      setInitialCitedSources([]);
      setLastQuestionAnswer(null);
      setCurrentQuestion('');
      setQuestion('');
      setCurrentNodeId(null);
      isLoadingRef.current = false;
      setIsLoading(false);
    }
  }, [selectedNodeData]);

  const handleClearConversation = useCallback(async () => {
    if (!currentMindMap || !jwt || !selectedNodeData) return;

    try {
      const result = await deleteChatHistory(
        currentMindMap.mongodb_doc_id,
        selectedNodeData.id,
        jwt
      );

      if (result.data?.success) {
        setLastQuestionAnswer(null);
        setCurrentQuestion('');
        toast.success('Conversation cleared successfully');
      } else {
        toast.error('Failed to clear conversation');
      }
    } catch (error) {
      toast.error('Failed to clear conversation');
      console.error('Error clearing conversation:', error);
    }
  }, [currentMindMap, jwt, selectedNodeData]);

  useEffect(() => {
    if (isDetailPanelOpen && !isLoading && questionInputRef.current && activeTab === 'chat') {
      const timer = setTimeout(() => {
        questionInputRef.current?.focus();
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isDetailPanelOpen, isLoading, activeTab]);

  useEffect(() => {
    if (conversationEndRef.current) {
      conversationEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [lastQuestionAnswer, isAsking, currentQuestion]);

  const handleAskQuestion = useCallback(async (questionText: string) => {
    if (!currentMindMap || !jwt || !selectedNodeData) return;

    // Set the current question immediately and start loading
    setCurrentQuestion(questionText);
    setIsAsking(true);

    try {
      const result = await askQuestionWithHistory(
        currentMindMap.mongodb_doc_id,
        questionText,
        jwt,
        selectedNodeData.id,
        selectedNodeData.data.label
      );

      if (result.data) {
        setLastQuestionAnswer({
          question: questionText,
          answer: result.data.answer,
          citedSources: result.data.cited_sources || []
        });
        setCurrentQuestion(''); // Clear current question after successful response
        toast.success('Question answered successfully');
      } else {
        setCurrentQuestion(''); // Clear on error too
        toast.error('Failed to get an answer');
      }
    } catch (error) {
      setCurrentQuestion(''); // Clear on error
      toast.error('Failed to ask question');
      console.error('Question error:', error);
    } finally {
      setIsAsking(false);
    }
  }, [currentMindMap, jwt, selectedNodeData]);

  const handleSubmitQuestion = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    const questionToAsk = question;
    setQuestion(''); // Clear input immediately
    await handleAskQuestion(questionToAsk);
  }, [question, handleAskQuestion]);

  const handleOpenChange = useCallback((open: boolean) => {
    if (!open) {
      setDetailPanelOpen(false);
      setTimeout(() => {
        setQuestion('');
        isLoadingRef.current = false;
        setIsLoading(false);
      }, 300);
    } else {
      setDetailPanelOpen(true);
    }
  }, [setDetailPanelOpen]);

  return (
    <Drawer handleOnly={false} open={isDetailPanelOpen} onOpenChange={handleOpenChange}>
      <DrawerContent className={cn(
        'h-[95vh] max-h-[95vh]',
        isMobile && 'h-[95vh] max-h-[95vh]'
      )}>
        <div className="mx-auto w-full max-w-4xl h-full flex flex-col">

          <DrawerHeader className="px-6 pt-2 pb-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <DrawerTitle className="text-2xl font-bold flex items-center gap-3 mb-2">
                  <motion.div
                    className="w-10 h-10 gradient-ai rounded-xl flex items-center justify-center shadow-lg"
                    animate={{ rotate: [0, 5, -5, 0] }}
                    transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
                  >
                    <Sparkles className="h-5 w-5 text-white" />
                  </motion.div>
                  <span className="gradient-text truncate">
                    {selectedNodeData?.data.label}
                  </span>
                </DrawerTitle>
                <DrawerDescription className="text-base">
                  Explore this concept with AI-powered insights
                </DrawerDescription>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => handleOpenChange(false)}
                className="flex-shrink-0"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
          </DrawerHeader>


          <div className="flex-1 overflow-hidden px-6 pb-8">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
              <TabsList className="grid w-full grid-cols-2 mb-4 sticky top-0 z-10 bg-background">
                <TabsTrigger value="details" className="gap-2">
                  <BookOpen className="h-4 w-4" />
                  Details
                </TabsTrigger>
                <TabsTrigger value="chat" className="gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Chat
                  {lastQuestionAnswer && (
                    <Badge variant="secondary" className="ml-2 text-xs">1</Badge>
                  )}
                </TabsTrigger>
              </TabsList>

              <div className="flex-1 overflow-hidden">
                <TabsContent value="details" className="h-full mt-0">
                  <ScrollArea className="h-full pr-4">
                    <div className="space-y-6 pb-6">
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        {isLoading ? (
                          <Card className="p-6 gradient-ai-subtle border-2">
                            <div className="space-y-3">
                              <Skeleton className="h-4 w-full" />
                              <Skeleton className="h-4 w-full" />
                              <Skeleton className="h-4 w-3/4" />
                            </div>
                          </Card>
                        ) : initialAnswer ? (
                          <Card className="p-6 border-2 hover:border-primary/30 transition-colors">
                            <div className="prose prose-sm max-w-none dark:prose-invert">
                              <ReactMarkdown
                                components={{
                                  h1: ({ children }) => <h1 className="text-xl font-bold mb-3 gradient-text">{children}</h1>,
                                  h2: ({ children }) => <h2 className="text-lg font-semibold mb-2 text-foreground">{children}</h2>,
                                  h3: ({ children }) => <h3 className="text-base font-medium mb-2 text-foreground">{children}</h3>,
                                  p: ({ children }) => <p className="mb-3 text-foreground leading-relaxed">{children}</p>,
                                  ul: ({ children }) => <ul className="list-disc ml-5 mb-3 space-y-1">{children}</ul>,
                                  ol: ({ children }) => <ol className="list-decimal ml-5 mb-3 space-y-1">{children}</ol>,
                                  li: ({ children }) => <li className="text-foreground">{children}</li>,
                                  strong: ({ children }) => <strong className="font-semibold text-primary">{children}</strong>,
                                  em: ({ children }) => <em className="italic text-foreground">{children}</em>,
                                  code: ({ children }) => <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>,
                                  blockquote: ({ children }) => <blockquote className="border-l-4 border-primary pl-4 italic text-muted-foreground mb-3">{children}</blockquote>,
                                }}
                              >
                                {initialAnswer}
                              </ReactMarkdown>
                            </div>
                          </Card>
                        ) : (
                          <Card className="p-6 text-center gradient-ai-subtle border-2">
                            <Sparkles className="h-12 w-12 mx-auto mb-3 text-primary" />
                            <p className="text-muted-foreground">
                              No details available yet. Switch to Chat to ask questions!
                            </p>
                          </Card>
                        )}
                      </motion.div>

                      {initialCitedSources.length > 0 && (
                        <motion.div
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.3, delay: 0.1 }}
                        >
                          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                            <BookOpen className="h-5 w-5 text-primary" />
                            Sources
                          </h3>
                          <div className="space-y-3">
                            {initialCitedSources.map((source, index) => (
                              <motion.div
                                key={index}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ duration: 0.2, delay: index * 0.05 }}
                              >
                                <Card className="p-4 hover:shadow-lg hover:border-primary/30 transition-all">
                                  <div className="flex items-start justify-between gap-3">
                                    <div className="flex-1">
                                      <h4 className="font-medium text-foreground mb-1">
                                        {source.title}
                                      </h4>
                                      {source.identifier && (
                                        <p className="text-xs text-muted-foreground truncate">
                                          {source.identifier}
                                        </p>
                                      )}
                                    </div>
                                    {source.identifier && (
                                      <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8 flex-shrink-0"
                                        asChild
                                      >
                                        <a
                                          href={source.identifier}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          aria-label="Open source"
                                        >
                                          <ExternalLink className="h-4 w-4" />
                                        </a>
                                      </Button>
                                    )}
                                  </div>
                                </Card>
                              </motion.div>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </div>
                  </ScrollArea>
                </TabsContent>

                <TabsContent value="chat" className="h-full mt-0">
                  <div className="h-full flex flex-col">
                    <ScrollArea className="flex-1 pr-4">
                      <div className="space-y-4 pb-4">
                        {(lastQuestionAnswer || currentQuestion) ? (
                          <AnimatePresence>
                            <motion.div
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              className="space-y-4"
                            >
                              {/* Show last Q&A if exists */}
                              {lastQuestionAnswer && (
                                <>
                                  {/* User Question */}
                                  <div className="flex items-start gap-3">
                                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-1">
                                      <UserIcon className="h-4 w-4 text-primary" />
                                    </div>
                                    <Card className="flex-1 p-4 bg-primary/5 border-primary/20">
                                      <p className="text-sm font-medium text-foreground">
                                        {lastQuestionAnswer.question}
                                      </p>
                                    </Card>
                                  </div>

                                  {/* AI Answer */}
                                  <div className="flex items-start gap-3">
                                    <div className="w-8 h-8 rounded-full gradient-ai flex items-center justify-center flex-shrink-0 mt-1">
                                      <Bot className="h-4 w-4 text-white" />
                                    </div>
                                    <Card className="flex-1 p-4">
                                      <div className="prose prose-sm max-w-none dark:prose-invert">
                                        <ReactMarkdown
                                          components={{
                                            p: ({ children }) => <p className="mb-2 text-foreground leading-relaxed">{children}</p>,
                                            ul: ({ children }) => <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul>,
                                            ol: ({ children }) => <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol>,
                                            strong: ({ children }) => <strong className="font-semibold text-primary">{children}</strong>,
                                            code: ({ children }) => <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">{children}</code>,
                                          }}
                                        >
                                          {lastQuestionAnswer.answer}
                                        </ReactMarkdown>
                                      </div>

                                      {lastQuestionAnswer.citedSources && lastQuestionAnswer.citedSources.length > 0 && (
                                        <div className="mt-4 pt-4 border-t border-border">
                                          <p className="text-xs font-medium text-muted-foreground mb-2">Sources:</p>
                                          <div className="space-y-2">
                                            {lastQuestionAnswer.citedSources.map((source: any, index: number) => (
                                              <div key={index} className="flex items-center gap-2 text-xs">
                                                <span className="text-muted-foreground">{source.title}</span>
                                                {source.identifier && (
                                                  <a
                                                    href={source.identifier}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-primary hover:underline"
                                                  >
                                                    <ExternalLink className="h-3 w-3" />
                                                  </a>
                                                )}
                                              </div>
                                            ))}
                                          </div>
                                        </div>
                                      )}
                                    </Card>
                                  </div>

                                  <div className="flex justify-end">
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={handleClearConversation}
                                      className="gap-2 text-muted-foreground hover:text-destructive"
                                    >
                                      <Trash2 className="h-4 w-4" />
                                      Clear conversation
                                    </Button>
                                  </div>
                                </>
                              )}

                              {/* Show current question being asked */}
                              {currentQuestion && isAsking && (
                                <div className="flex items-start gap-3">
                                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-1">
                                    <UserIcon className="h-4 w-4 text-primary" />
                                  </div>
                                  <Card className="flex-1 p-4 bg-primary/5 border-primary/20">
                                    <p className="text-sm font-medium text-foreground">
                                      {currentQuestion}
                                    </p>
                                  </Card>
                                </div>
                              )}
                            </motion.div>
                          </AnimatePresence>
                        ) : (
                          <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="text-center py-12"
                          >
                            <MessageSquare className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
                            <h3 className="text-lg font-semibold mb-2">No messages yet</h3>
                            <p className="text-sm text-muted-foreground mb-4">
                              Start a conversation about this concept
                            </p>
                          </motion.div>
                        )}

                        {isAsking && (
                          <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex items-start gap-3"
                          >
                            <div className="w-8 h-8 rounded-full gradient-ai flex items-center justify-center flex-shrink-0 mt-1">
                              <Loader2 className="h-4 w-4 text-white animate-spin" />
                            </div>
                            <Card className="flex-1 p-4">
                              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <div className="flex gap-1">
                                  <span className="w-2 h-2 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: '0ms' }} />
                                  <span className="w-2 h-2 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: '150ms' }} />
                                  <span className="w-2 h-2 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: '300ms' }} />
                                </div>
                                Thinking...
                              </div>
                            </Card>
                          </motion.div>
                        )}

                        <div ref={conversationEndRef} />
                      </div>
                    </ScrollArea>

                    <div className="pt-4 px-2 border-t border-border shrink-0">
                      <form onSubmit={handleSubmitQuestion} className="relative w-full">
                        <Input
                          ref={questionInputRef}
                          placeholder="Ask anything about this concept..."
                          value={question}
                          onChange={(e) => setQuestion(e.target.value)}
                          disabled={isAsking || isLoading}
                          className="pr-12 h-12 w-full focus:ring-2 focus:ring-primary/20"
                          autoComplete="off"
                        />
                        <Button
                          type="submit"
                          size="icon"
                          className="absolute right-1 top-1/2 -translate-y-1/2 h-10 w-10 gradient-ai text-white hover:opacity-90 transition-opacity"
                          disabled={!question.trim() || isAsking || isLoading}
                        >
                          {isAsking ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Send className="h-4 w-4" />
                          )}
                        </Button>
                      </form>
                      <p className="text-xs text-muted-foreground mt-2">
                        Press Enter to send • Your conversation is automatically saved
                      </p>
                    </div>
                  </div>
                </TabsContent>
              </div>
            </Tabs>
          </div>
        </div>
      </DrawerContent>
    </Drawer>
  );
}
