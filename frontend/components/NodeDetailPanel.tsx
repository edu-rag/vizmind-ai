'use client';

import { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Send, ExternalLink, Loader2 } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { askQuestion, getNodeDetails } from '@/lib/api';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

export function NodeDetailPanel() {
  const {
    selectedNodeData,
    isDetailPanelOpen,
    setDetailPanelOpen,
    currentMindMap,
    jwt,
  } = useAppStore();

  console.log('🏪 Store state:', {
    selectedNodeData,
    isDetailPanelOpen,
    hasCurrentMindMap: !!currentMindMap,
    hasJwt: !!jwt,
    mindMapId: currentMindMap?.mongodb_doc_id,
    nodeLabel: selectedNodeData?.data.label
  });

  const [isLoading, setIsLoading] = useState(false);
  const [initialAnswer, setInitialAnswer] = useState<string | null>(null);
  const [initialCitedSources, setInitialCitedSources] = useState<any[]>([]);
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(null);

  // Debug effect to track state changes
  useEffect(() => {
    console.log('💾 State update:', {
      isLoading,
      hasInitialAnswer: !!initialAnswer,
      initialAnswerLength: initialAnswer?.length || 0,
      citedSourcesCount: initialCitedSources.length,
      currentNodeId
    });
  }, [isLoading, initialAnswer, initialCitedSources, currentNodeId]);
  const [conversation, setConversation] = useState<Array<{
    id: string;
    type: 'question' | 'answer';
    content: string;
    citedSources?: any[];
    timestamp: Date;
    nodeId: string; // Track which node this message is for
  }>>([]);
  const [question, setQuestion] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [sessionHistory, setSessionHistory] = useState<{
    [nodeId: string]: Array<{
      id: string;
      type: 'question' | 'answer';
      content: string;
      citedSources?: any[];
      timestamp: Date;
      nodeId: string;
    }>
  }>({});
  const conversationEndRef = useRef<HTMLDivElement>(null);
  const questionInputRef = useRef<HTMLInputElement>(null);
  const isLoadingRef = useRef(false);

  // Helper function to find a node in the hierarchical structure
  const findNodeInHierarchy = useCallback((hierarchy: any, nodeId: string): { id: string; data: { label: string } } | null => {
    if (!hierarchy) return null;

    if (hierarchy.id === nodeId) {
      return { id: hierarchy.id, data: { label: hierarchy.data.label } };
    }

    if (hierarchy.children) {
      for (const child of hierarchy.children) {
        const found = findNodeInHierarchy(child, nodeId);
        if (found) return found;
      }
    }

    return null;
  }, []);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleGetNodeDetails = useCallback(async () => {
    console.log('🔍 handleGetNodeDetails called:', {
      hasCurrentMindMap: !!currentMindMap,
      hasJwt: !!jwt,
      selectedNodeData,
      isLoadingRefCurrent: isLoadingRef.current,
      mapId: currentMindMap?.mongodb_doc_id
    });

    if (!currentMindMap || !jwt || !selectedNodeData) {
      console.log('❌ Early return from handleGetNodeDetails:', {
        missingCurrentMindMap: !currentMindMap,
        missingJwt: !jwt,
        missingSelectedNodeData: !selectedNodeData
      });
      return;
    }

    // Prevent multiple concurrent calls
    if (isLoadingRef.current) {
      console.log('⏭️ Already loading, skipping duplicate call');
      return;
    }

    // Use the node label for the query
    const nodeQuery = selectedNodeData.data.label;
    console.log('🔎 Using nodeQuery:', nodeQuery);

    isLoadingRef.current = true;
    setIsLoading(true);

    try {
      console.log('🚀 Making API call to getNodeDetails...');
      const result = await getNodeDetails(
        currentMindMap.mongodb_doc_id,
        nodeQuery,
        jwt
      );

      console.log('✅ API result:', result);

      if (result.data) {
        console.log('🔍 API result.data:', JSON.stringify(result.data, null, 2));
        setInitialAnswer(result.data.answer);
        setInitialCitedSources(result.data.cited_sources || []);
        console.log('📝 Node details set successfully - answer length:', result.data.answer?.length);
      } else {
        console.log('❌ No data in API result');
        toast.error('Failed to get node details');
      }
    } catch (error) {
      toast.error('Failed to fetch node details');
      console.error('💥 Node details error:', error);
    } finally {
      isLoadingRef.current = false;
      setIsLoading(false);
      console.log('🏁 Finished API call');
    }
  }, [currentMindMap, jwt, selectedNodeData]);

  useEffect(() => {
    console.log('🎯 Effect triggered for API call:', {
      selectedNodeData,
      hasCurrentMindMap: !!currentMindMap,
      hasJwt: !!jwt,
      mapId: currentMindMap?.mongodb_doc_id
    });

    if (selectedNodeData && currentMindMap && jwt) {
      console.log('✅ Conditions met, calling handleGetNodeDetails');
      handleGetNodeDetails();
    } else {
      console.log('❌ Conditions not met for API call');
    }
  }, [selectedNodeData, currentMindMap, jwt, handleGetNodeDetails]);

  // Reset loading state and clear previous data when node changes or panel opens
  useEffect(() => {
    if (isDetailPanelOpen && selectedNodeData) {
      console.log('🔄 Reset effect triggered:', { selectedNodeId: selectedNodeData.id, currentNodeId });

      // Only clear data when switching nodes, don't manage loading state here
      if (currentNodeId !== selectedNodeData.id) {
        console.log('🗑️ Clearing data for node switch from', currentNodeId, 'to', selectedNodeData.id);
        setInitialAnswer(null);
        setInitialCitedSources([]);
        setCurrentNodeId(selectedNodeData.id);
      }
    }
  }, [isDetailPanelOpen, selectedNodeData, currentNodeId]);

  // Separate effect for loading conversation history
  useEffect(() => {
    if (selectedNodeData) {
      if (sessionHistory[selectedNodeData.id]) {
        setConversation(sessionHistory[selectedNodeData.id]);
      } else {
        setConversation([]);
      }
    }
  }, [selectedNodeData, sessionHistory]);

  // Separate effect for focusing input when panel opens
  useEffect(() => {
    if (isDetailPanelOpen && !isLoading && questionInputRef.current) {
      const timer = setTimeout(() => {
        questionInputRef.current?.focus();
      }, 500); // Small delay to ensure the panel is fully open

      return () => clearTimeout(timer);
    }
  }, [isDetailPanelOpen, isLoading]);

  // Auto-scroll to bottom when conversation updates
  useEffect(() => {
    if (conversationEndRef.current) {
      conversationEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversation, isAsking]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isDetailPanelOpen) {
        handleClose();
      }
    };

    if (isDetailPanelOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isDetailPanelOpen]);

  const handleAskQuestion = useCallback(async (questionText: string) => {
    if (!currentMindMap || !jwt || !selectedNodeData) return;

    // Add the question to conversation immediately
    const questionId = Date.now().toString();
    const questionMessage = {
      id: questionId,
      type: 'question' as const,
      content: questionText,
      timestamp: new Date(),
      nodeId: selectedNodeData.id
    };

    const newConversation = [...conversation, questionMessage];
    setConversation(newConversation);

    setIsAsking(true);

    try {
      const result = await askQuestion(
        currentMindMap.mongodb_doc_id,
        questionText,
        jwt,
        selectedNodeData.data.label
      );

      if (result.data) {
        // Add the answer to conversation
        const answerId = (Date.now() + 1).toString();
        const responseData = result.data;
        const answerMessage = {
          id: answerId,
          type: 'answer' as const,
          content: responseData.answer,
          citedSources: responseData.cited_sources || [],
          timestamp: new Date(),
          nodeId: selectedNodeData.id
        };

        const updatedConversation = [...newConversation, answerMessage];
        setConversation(updatedConversation);

        // Save to session history
        setSessionHistory(prev => ({
          ...prev,
          [selectedNodeData.id]: updatedConversation
        }));

        toast.success('Question answered successfully');
      } else {
        toast.error('Failed to get an answer');
      }
    } catch (error) {
      toast.error('Failed to ask question');
      console.error('Question error:', error);
    } finally {
      setIsAsking(false);
    }
  }, [currentMindMap, jwt, selectedNodeData, conversation]);

  const handleSubmitQuestion = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    await handleAskQuestion(question);
    setQuestion('');
  }, [question, handleAskQuestion]);

  const handleOpenChange = useCallback((open: boolean) => {
    if (!open) {
      // Save current conversation to session history before closing
      if (selectedNodeData && conversation.length > 0) {
        setSessionHistory(prev => ({
          ...prev,
          [selectedNodeData.id]: conversation
        }));
      }

      setDetailPanelOpen(false);
      // Reset state when closing
      setTimeout(() => {
        setInitialAnswer(null);
        setInitialCitedSources([]);
        setConversation([]);
        setQuestion('');
        setCurrentNodeId(null);
        isLoadingRef.current = false;
        setIsLoading(false);
      }, 300);
    } else {
      setDetailPanelOpen(true);
    }
  }, [setDetailPanelOpen, selectedNodeData, conversation]);

  const handleClose = useCallback(() => {
    handleOpenChange(false);
  }, [handleOpenChange]);

  return (
    <Sheet open={isDetailPanelOpen} onOpenChange={handleOpenChange}>
      <SheetContent
        className={cn(
          'p-0 flex flex-col',
          isMobile ? 'w-full max-w-full' : 'w-[400px] sm:w-[500px]'
        )}
        side={isMobile ? 'bottom' : 'right'}
      >
        <div className="h-full flex flex-col py-4">
          <SheetHeader className="spacing-mobile pb-4 safe-area-top">
            <SheetTitle className="text-left text-responsive-lg">
              Details for: {selectedNodeData?.data.label}
            </SheetTitle>
            <SheetDescription className="text-left text-responsive-sm">
              Explore this concept with AI-powered insights
            </SheetDescription>
          </SheetHeader>

          <Separator />

          <ScrollArea className="flex-1 spacing-mobile">
            <div className="space-y-6">
              {/* Initial Node Details Section */}
              <div>
                <h3 className="text-responsive-sm font-semibold text-foreground mb-3">
                  Node Details
                </h3>

                {isLoading ? (
                  <Card className="spacing-mobile-sm">
                    <div className="space-y-3">
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-3/4" />
                    </div>
                  </Card>
                ) : initialAnswer ? (
                  <Card className="spacing-mobile-sm">
                    <div className="text-responsive-sm text-foreground leading-relaxed prose prose-sm max-w-none">
                      <ReactMarkdown
                        components={{
                          h1: ({ children }) => <h1 className="text-lg font-bold mb-3 text-foreground">{children}</h1>,
                          h2: ({ children }) => <h2 className="text-base font-semibold mb-2 text-foreground">{children}</h2>,
                          h3: ({ children }) => <h3 className="text-sm font-medium mb-2 text-foreground">{children}</h3>,
                          p: ({ children }) => <p className="mb-2 text-foreground leading-relaxed">{children}</p>,
                          ul: ({ children }) => <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol>,
                          li: ({ children }) => <li className="text-foreground">{children}</li>,
                          strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
                          em: ({ children }) => <em className="italic text-foreground">{children}</em>,
                          code: ({ children }) => <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono">{children}</code>,
                          blockquote: ({ children }) => <blockquote className="border-l-4 border-muted-foreground pl-4 italic text-muted-foreground mb-2">{children}</blockquote>,
                        }}
                      >
                        {initialAnswer}
                      </ReactMarkdown>
                    </div>
                  </Card>
                ) : (
                  <Card className="spacing-mobile-sm">
                    <p className="text-responsive-sm text-muted-foreground">
                      No details available yet.
                    </p>
                  </Card>
                )}
              </div>

              {/* Initial Cited Sources Section */}
              {initialCitedSources.length > 0 && (
                <div>
                  <h3 className="text-responsive-sm font-semibold text-foreground mb-3">
                    Sources
                  </h3>
                  <div className="space-y-3">
                    {initialCitedSources.map((source, index) => (
                      <Card key={index} className="spacing-mobile-sm">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <h4 className="text-responsive-sm font-medium text-foreground flex-1">
                              {source.title}
                            </h4>
                            {source.identifier && (
                              <Button
                                variant="ghost"
                                size="icon"
                                className="touch-target flex-shrink-0"
                                asChild
                              >
                                <a
                                  href={source.identifier}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  aria-label="Open source link"
                                >
                                  <ExternalLink className="h-4 w-4" />
                                </a>
                              </Button>
                            )}
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Conversation Section */}
              {conversation.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-responsive-sm font-semibold text-foreground">
                      Conversation History
                    </h3>
                    <div className="flex items-center space-x-2">
                      <span className="text-responsive-xs text-muted-foreground">
                        {conversation.filter(m => m.type === 'question').length} questions
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          if (selectedNodeData) {
                            setConversation([]);
                            setSessionHistory(prev => {
                              const newHistory = { ...prev };
                              delete newHistory[selectedNodeData.id];
                              return newHistory;
                            });
                          }
                        }}
                        className="h-6 px-2 text-xs"
                      >
                        Clear
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-4">
                    {conversation.map((message) => (
                      <div key={message.id} className="space-y-2">
                        {message.type === 'question' ? (
                          <Card className="spacing-mobile-sm bg-muted/50 border-muted">
                            <div className="flex items-start space-x-2">
                              <div className="w-2 h-2 rounded-full bg-primary mt-2 flex-shrink-0" />
                              <div className="flex-1">
                                <p className="text-responsive-sm font-medium text-foreground mb-1">
                                  Your Question:
                                </p>
                                <p className="text-responsive-sm text-foreground">
                                  {message.content}
                                </p>
                              </div>
                            </div>
                          </Card>
                        ) : (
                          <div className="space-y-3">
                            <Card className="spacing-mobile-sm">
                              <div className="text-responsive-sm text-foreground leading-relaxed prose prose-sm max-w-none">
                                <ReactMarkdown
                                  components={{
                                    h1: ({ children }) => <h1 className="text-lg font-bold mb-3 text-foreground">{children}</h1>,
                                    h2: ({ children }) => <h2 className="text-base font-semibold mb-2 text-foreground">{children}</h2>,
                                    h3: ({ children }) => <h3 className="text-sm font-medium mb-2 text-foreground">{children}</h3>,
                                    p: ({ children }) => <p className="mb-2 text-foreground leading-relaxed">{children}</p>,
                                    ul: ({ children }) => <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul>,
                                    ol: ({ children }) => <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol>,
                                    li: ({ children }) => <li className="text-foreground">{children}</li>,
                                    strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
                                    em: ({ children }) => <em className="italic text-foreground">{children}</em>,
                                    code: ({ children }) => <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono">{children}</code>,
                                    blockquote: ({ children }) => <blockquote className="border-l-4 border-muted-foreground pl-4 italic text-muted-foreground mb-2">{children}</blockquote>,
                                  }}
                                >
                                  {message.content}
                                </ReactMarkdown>
                              </div>
                            </Card>

                            {/* Cited Sources for this answer */}
                            {message.citedSources && message.citedSources.length > 0 && (
                              <div className="ml-4">
                                <h4 className="text-responsive-xs font-medium text-muted-foreground mb-2">
                                  Sources for this answer:
                                </h4>
                                <div className="space-y-2">
                                  {message.citedSources.map((source, index) => (
                                    <Card key={index} className="spacing-mobile-sm border-muted">
                                      <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                          <h5 className="text-responsive-xs font-medium text-foreground flex-1">
                                            {source.title}
                                          </h5>
                                          {source.identifier && (
                                            <Button
                                              variant="ghost"
                                              size="icon"
                                              className="touch-target flex-shrink-0 h-6 w-6"
                                              asChild
                                            >
                                              <a
                                                href={source.identifier}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                aria-label="Open source link"
                                              >
                                                <ExternalLink className="h-3 w-3" />
                                              </a>
                                            </Button>
                                          )}
                                        </div>
                                      </div>
                                    </Card>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}

                    {/* Loading indicator for current question */}
                    {isAsking && (
                      <Card className="spacing-mobile-sm">
                        <div className="flex items-center space-x-3">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <p className="text-responsive-sm text-muted-foreground">
                            Generating answer...
                          </p>
                        </div>
                      </Card>
                    )}

                    {/* Scroll anchor */}
                    <div ref={conversationEndRef} />
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          <Separator />

          {/* Ask Follow-up Question */}
          <div className="spacing-mobile pt-4 safe-area-bottom">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-responsive-sm font-semibold text-foreground">
                  Ask a Question
                </h3>
                <div className="flex items-center space-x-2">
                  {conversation.length > 0 && (
                    <span className="text-responsive-xs text-muted-foreground">
                      {conversation.filter(m => m.type === 'question').length} questions asked
                    </span>
                  )}
                  {selectedNodeData && sessionHistory[selectedNodeData.id] && sessionHistory[selectedNodeData.id].length > 0 && (
                    <span className="text-responsive-xs text-green-600 dark:text-green-400">
                      History saved
                    </span>
                  )}
                </div>
              </div>

              <div className="text-responsive-xs text-muted-foreground mb-2">
                Your conversation history is preserved for each concept node during this session.
              </div>

              <form onSubmit={handleSubmitQuestion} className="relative">
                <Input
                  ref={questionInputRef}
                  placeholder="Ask anything about this concept..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      if (question.trim() && !isAsking && !isLoading) {
                        handleSubmitQuestion(e as any);
                      }
                    }
                  }}
                  disabled={isAsking || isLoading}
                  className="form-mobile text-responsive-sm pr-12"
                  autoComplete="off"
                />
                <Button
                  type="submit"
                  size="icon"
                  variant="ghost"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 hover:bg-muted"
                  disabled={!question.trim() || isAsking || isLoading}
                >
                  {isAsking ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </form>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}