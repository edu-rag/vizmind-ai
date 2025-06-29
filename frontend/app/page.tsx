'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ArrowRight,
  BookOpen,
  Sparkles,
  Brain,
  Network,
  ExternalLink,
  ArrowLeft,
  Share2,
  MessageCircle
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { FileDropZone } from '@/components/FileDropZone';
import { ConceptMapDisplay } from '@/components/ConceptMapDisplay';
import { ChatSidebar } from '@/components/ChatSidebar';
import { NodeDetailPanel } from '@/components/NodeDetailPanel';
import { useScrollBehavior } from '@/hooks/use-scroll-behavior';
import { BackToTopButton } from '@/components/BackToTopButton';

export default function Home() {
  const { isAuthenticated, mapHistory, currentMap, setChatSidebarOpen, isChatSidebarOpen } = useAppStore();

  // Initialize scroll behavior
  useScrollBehavior();

  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      {currentMap ? (
        // Map View - when a map is loaded from sidebar
        <div className="h-screen flex flex-col">
          {/* Map Header */}
          <div className="border-b border-border bg-background/95 backdrop-blur-sm p-4">
            <div className="flex items-center justify-between max-w-7xl mx-auto">
              <div className="flex items-center space-x-4">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    // Clear current map to go back to home view
                    const { setCurrentMap } = useAppStore.getState();
                    setCurrentMap(null);
                  }}
                  className="touch-target"
                  aria-label="Back to home"
                >
                  <ArrowLeft className="h-5 w-5" />
                </Button>

                <div className="min-w-0">
                  <h1 className="text-lg font-semibold text-foreground truncate">
                    {currentMap.source_filename?.replace('.pdf', '') || 'Concept Map'}
                  </h1>
                  <p className="text-sm text-muted-foreground">
                    Interactive concept map
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setChatSidebarOpen(!isChatSidebarOpen)}
                  className="touch-target"
                >
                  <MessageCircle className="mr-2 h-4 w-4" />
                  {isChatSidebarOpen ? 'Close Chat' : 'Chat'}
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(`/maps/${currentMap.mongodb_doc_id}`, '_blank')}
                  className="touch-target"
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Open in New Tab
                </Button>
              </div>
            </div>
          </div>

          {/* Map Content */}
          <div className="flex-1 overflow-hidden flex">
            <div className="flex-1 max-w-7xl mx-auto p-4">
              <ConceptMapDisplay />
            </div>
            <ChatSidebar />
          </div>

          {/* Node Detail Panel */}
          <NodeDetailPanel />
        </div>
      ) : (
        // Home View - default landing page
        <div className="container mx-auto px-4 py-8 md:py-12 max-w-7xl">
          {/* Hero Section */}
          <section id="hero" className="text-center space-y-8 mb-16 min-h-[80vh] flex flex-col justify-center">
            <div className="space-y-6 mb-4">
              <div className="w-20 h-20 bg-gradient-to-br from-primary to-primary/60 rounded-full flex items-center justify-center mx-auto">
                <Network className="h-10 w-10 text-white" />
              </div>
              <h1 className="text-3xl md:text-4xl font-bold text-foreground tracking-tight">
                PDF to{' '}
                <span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                  Knowledge Maps
                </span>
              </h1>
              <p className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
                Upload a PDF and let AI turn it into an interactive concept map for easy exploration and insights.
              </p>
            </div>

            {/* Upload Section */}
            <div className="max-w-3xl mx-auto">
              <FileDropZone />
            </div>

            <div className="flex justify-center">
              {isAuthenticated && mapHistory.length > 0 && (
                <Button variant="outline" size="lg" className="gap-2" asChild>
                  <Link href={`/maps/${mapHistory[0].map_id}`}>
                    <BookOpen className="h-4 w-4" />
                    Latest Map
                  </Link>
                </Button>
              )}
            </div>
          </section>

          {/* Features Section */}
          <section id="features" className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 md:mb-16 scroll-mt-20">
            <Card className="p-6 text-center hover:shadow-lg transition-shadow duration-200">
              <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Brain className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-bold text-foreground mb-2">AI-Powered Analysis</h3>
              <p className="text-muted-foreground">
                Advanced AI extracts key concepts and relationships from your documents automatically
              </p>
            </Card>

            <Card className="p-6 text-center hover:shadow-lg transition-shadow duration-200">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Network className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-xl font-bold text-foreground mb-2">Interactive Exploration</h3>
              <p className="text-muted-foreground">
                Navigate through concepts, zoom in on details, and discover hidden connections
              </p>
            </Card>

            <Card className="p-6 text-center hover:shadow-lg transition-shadow duration-200">
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Sparkles className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-xl font-bold text-foreground mb-2">Smart Insights</h3>
              <p className="text-muted-foreground">
                Ask questions about any concept and get AI-powered answers with cited sources
              </p>
            </Card>
          </section>

          {/* Recent Maps Section */}
          {isAuthenticated && mapHistory.length > 0 && (
            <section id="recent-maps" className="space-y-6 scroll-mt-20">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-foreground">Recent Maps</h2>
              </div>

              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 max-w-5xl mx-auto">
                {mapHistory.slice(0, 6).map((item) => (
                  <div key={item.map_id} className="relative group">
                    <Link href={`/maps/${item.map_id}`}>
                      <Card className="group hover:shadow-lg transition-all duration-200 cursor-pointer">
                        <div className="aspect-video bg-gradient-to-br from-primary/10 to-primary/5 flex items-center justify-center">
                          <Network className="h-8 w-8 text-primary/60" />
                        </div>

                        <div className="p-4 space-y-2">
                          <div className="flex items-center justify-between">
                            <Badge variant="secondary" className="text-xs">
                              PDF
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {new Date(item.created_at).toLocaleDateString()}
                            </span>
                          </div>

                          <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-1">
                            {item.source_filename.replace('.pdf', '')}
                          </h3>
                        </div>
                      </Card>
                    </Link>

                    {/* Open in New Tab Button */}
                    <Button
                      variant="secondary"
                      size="icon"
                      className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 shadow-lg h-8 w-8"
                      onClick={(e) => {
                        e.preventDefault();
                        window.open(`/maps/${item.map_id}`, '_blank');
                      }}
                      title="Open in new tab"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>

              {mapHistory.length > 6 && (
                <div className="text-center">
                  <Button variant="outline" className="gap-2">
                    View All ({mapHistory.length})
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </section>
          )}

          {/* Back to Top Button for home view */}
          <BackToTopButton />
        </div>
      )}
    </div>
  );
}