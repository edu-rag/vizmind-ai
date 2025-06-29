'use client';

import { useEffect, useState } from 'react';
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
    selectedNode,
    isDetailPanelOpen,
    setDetailPanelOpen,
    currentMap,
    jwt,
  } = useAppStore();

  const [isLoading, setIsLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [citedSources, setCitedSources] = useState<any[]>([]);
  const [question, setQuestion] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  const selectedNodeData = currentMap?.react_flow_data.nodes.find(
    (node) => node.id === selectedNode
  );

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    if (selectedNode && selectedNodeData && currentMap && jwt) {
      // Auto-fetch node details using the /details endpoint
      handleGetNodeDetails();
    }
  }, [selectedNode, selectedNodeData, currentMap, jwt]);

  const handleGetNodeDetails = async () => {
    if (!currentMap || !jwt || !selectedNodeData) return;

    setIsLoading(true);

    try {
      const result = await getNodeDetails(
        currentMap.mongodb_doc_id,
        selectedNodeData.data.label,
        jwt
      );

      if (result.data) {
        setAnswer(result.data.answer);
        setCitedSources(result.data.cited_sources || []);
      } else {
        toast.error('Failed to get node details');
      }
    } catch (error) {
      toast.error('Failed to fetch node details');
      console.error('Node details error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAskQuestion = async (questionText: string) => {
    if (!currentMap || !jwt || !selectedNodeData) return;

    setIsAsking(true);

    try {
      const result = await askQuestion(
        currentMap.mongodb_doc_id,
        questionText,
        jwt,
        selectedNodeData.data.label
      );

      if (result.data) {
        setAnswer(result.data.answer);
        setCitedSources(result.data.cited_sources || []);
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
  };

  const handleSubmitQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    await handleAskQuestion(question);
    setQuestion('');
  };

  const handleClose = () => {
    setDetailPanelOpen(false);
    // Reset state when closing
    setTimeout(() => {
      setAnswer(null);
      setCitedSources([]);
      setQuestion('');
    }, 300);
  };

  return (
    <Sheet open={isDetailPanelOpen} onOpenChange={handleClose}>
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
              {/* Generated Answer Section */}
              <div>
                <h3 className="text-responsive-sm font-semibold text-foreground mb-3">
                  Generated Answer
                </h3>

                {isLoading ? (
                  <Card className="spacing-mobile-sm">
                    <div className="space-y-3">
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-3/4" />
                    </div>
                  </Card>
                ) : answer ? (
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
                        {answer}
                      </ReactMarkdown>
                    </div>
                  </Card>
                ) : (
                  <Card className="spacing-mobile-sm">
                    <p className="text-responsive-sm text-muted-foreground">
                      No answer available yet.
                    </p>
                  </Card>
                )}
              </div>

              {/* Cited Sources Section */}
              {citedSources.length > 0 && (
                <div>
                  <h3 className="text-responsive-sm font-semibold text-foreground mb-3">
                    Cited Sources
                  </h3>
                  <div className="space-y-3">
                    {citedSources.map((source, index) => (
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
                          {/* {source.snippet && (
                            <p className="text-responsive-xs text-muted-foreground">
                              {source.snippet}
                            </p>
                          )}
                          <span className="text-responsive-xs text-muted-foreground">
                            Type: {source.type}
                          </span> */}
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          <Separator />

          {/* Ask Follow-up Question */}
          <div className="spacing-mobile pt-4 safe-area-bottom">
            <h3 className="text-responsive-sm font-semibold text-foreground mb-3">
              Ask a Follow-up Question
            </h3>
            <form onSubmit={handleSubmitQuestion} className="space-y-3">
              <Input
                placeholder="Ask anything about this concept..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={isAsking}
                className="form-mobile text-responsive-sm"
              />
              <Button
                type="submit"
                className="w-full touch-target text-responsive-sm"
                disabled={!question.trim() || isAsking}
              >
                {isAsking ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Asking...
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    Ask Question
                  </>
                )}
              </Button>
            </form>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}