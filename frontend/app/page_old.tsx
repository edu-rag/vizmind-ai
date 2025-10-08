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
  Zap,
  Shield,
  Upload,
  MessageSquare,
  CheckCircle2,
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { getHierarchicalMindMap } from '@/lib/api';
import { FileDropZone } from '@/components/FileDropZone';
import { HierarchicalMindMapDisplay } from '@/components/HierarchicalMindMapDisplay';
import { NodeDetailPanel } from '@/components/NodeDetailPanel';
import { useScrollBehavior } from '@/hooks/use-scroll-behavior';
import { BackToTopButton } from '@/components/BackToTopButton';
import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

export default function Home() {
  const { isAuthenticated, mapHistory, currentMindMap } = useAppStore();
  const [mounted, setMounted] = useState(false);

  // Initialize scroll behavior
  useScrollBehavior();

  useEffect(() => {
    setMounted(true);
  }, []);

  // Check if we have an active hierarchical mind map
  const activeMap = currentMindMap;

  // Animation variants
  const fadeInUp = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  const staggerContainer = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const scaleIn = {
    hidden: { opacity: 0, scale: 0.8 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        type: "spring" as const,
        stiffness: 100,
        damping: 15
      }
    }
  };

  if (!mounted) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      {activeMap ? (
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
                    // Clear current mind map to go back to home view
                    const { setCurrentMindMap } = useAppStore.getState();
                    setCurrentMindMap(null);
                  }}
                  className="touch-target"
                  aria-label="Back to home"
                >
                  <ArrowLeft className="h-5 w-5" />
                </Button>

                <div className="min-w-0">
                  <h1 className="text-lg font-semibold text-foreground truncate">
                    {currentMindMap?.title || 'Hierarchical Mind Map'}
                  </h1>
                  <p className="text-sm text-muted-foreground">
                    Hierarchical mind map visualization
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const mapId = currentMindMap?.mongodb_doc_id;
                    if (mapId) {
                      window.open(`/maps/${mapId}`, '_blank');
                    }
                  }}
                  className="touch-target"
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Open in New Tab
                </Button>
              </div>
            </div>
          </div>

          {/* Map Content */}
          <div className="flex-1 overflow-hidden relative">
            <div className="absolute inset-0 p-4">
              <HierarchicalMindMapDisplay />
            </div>
          </div>

          {/* Node Detail Panel */}
          <NodeDetailPanel />
        </div>
      ) : (
        // Home View - default landing page
        <div className="container mx-auto px-4 py-8 md:py-12 max-w-7xl">
          {/* Hero Section */}
          <motion.section
            id="hero"
            className="text-center space-y-8 mb-20 md:mb-32 min-h-[85vh] flex flex-col justify-center"
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
          >
            <motion.div className="space-y-6" variants={fadeInUp}>
              <motion.div
                className="w-24 h-24 mx-auto relative"
                variants={scaleIn}
                whileHover={{ scale: 1.1, rotate: 5 }}
                transition={{ type: "spring" as const, stiffness: 300 }}
              >
                <div className="absolute inset-0 gradient-ai rounded-3xl blur-xl opacity-60 animate-pulse" />
                <div className="relative w-full h-full gradient-ai rounded-3xl flex items-center justify-center shadow-2xl">
                  <Brain className="h-12 w-12 text-white" />
                </div>
              </motion.div>

              <motion.div variants={fadeInUp} className="space-y-4">
                <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight">
                  <span className="gradient-text block">VizMind AI</span>
                  <span className="text-2xl md:text-3xl lg:text-4xl font-normal text-muted-foreground mt-2 block">
                    Intelligent Mind Mapping
                  </span>
                </h1>
                <p className="text-lg md:text-xl lg:text-2xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
                  Transform your documents into{' '}
                  <span className="text-primary font-semibold">intelligent</span>,{' '}
                  <span className="text-purple-600 dark:text-purple-400 font-semibold">interactive mind maps</span>.
                  <br className="hidden md:block" />
                  Ask questions and get AI-powered insights instantly.
                </p>
              </motion.div>

              <motion.div
                variants={fadeInUp}
                className="flex flex-wrap justify-center gap-3 text-sm text-muted-foreground"
              >
                <Badge variant="secondary" className="px-4 py-2 text-sm">
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  PDF Analysis
                </Badge>
                <Badge variant="secondary" className="px-4 py-2 text-sm">
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  AI-Powered
                </Badge>
                <Badge variant="secondary" className="px-4 py-2 text-sm">
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Real-time Q&A
                </Badge>
              </motion.div>
            </motion.div>

            {/* Upload Section */}
            <motion.div
              className="max-w-4xl mx-auto w-full"
              variants={fadeInUp}
            >
              <FileDropZone />
            </motion.div>

            {/* CTA Buttons */}
            <motion.div
              className="flex flex-wrap justify-center gap-4"
              variants={fadeInUp}
            >
              {isAuthenticated && mapHistory.length > 0 && (
                <Button
                  size="lg"
                  className="gap-2 shadow-lg hover:shadow-xl transition-all"
                  asChild
                >
                  <Link href={`/maps/${mapHistory[0].map_id}`}>
                    <BookOpen className="h-5 w-5" />
                    Open Latest Map
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
              )}
              <Button
                variant="outline"
                size="lg"
                className="gap-2 hover:border-primary/50"
                onClick={() => {
                  document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                Learn More
                <ArrowRight className="h-4 w-4" />
              </Button>
            </motion.div>
          </motion.section>

          {/* How It Works Section */}
          <motion.section
            id="how-it-works"
            className="mb-20 md:mb-32"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            variants={staggerContainer}
          >
            <motion.div className="text-center mb-12" variants={fadeInUp}>
              <Badge className="mb-4 gradient-ai text-white">How It Works</Badge>
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4">
                <span className="gradient-text">Simple. Fast. Intelligent.</span>
              </h2>
              <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">
                Transform your documents in three easy steps
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
              {/* Connection lines for desktop */}
              <div className="hidden md:block absolute top-1/3 left-0 right-0 h-0.5 bg-gradient-to-r from-primary/20 via-primary/40 to-primary/20 -translate-y-1/2" />

              <motion.div variants={fadeInUp} className="relative">
                <Card className="p-8 text-center hover:shadow-xl transition-all duration-300 border-2 hover:border-primary/50 relative overflow-hidden group">
                  <div className="absolute inset-0 gradient-ai-subtle opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="relative">
                    <div className="w-16 h-16 rounded-full gradient-ai flex items-center justify-center mx-auto mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300">
                      <Upload className="h-8 w-8 text-white" />
                    </div>
                    <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-primary text-white font-bold mb-4">
                      1
                    </div>
                    <h3 className="text-xl font-bold mb-3">Upload Document</h3>
                    <p className="text-muted-foreground">
                      Drop your PDF file or click to upload. We support multiple documents.
                    </p>
                  </div>
                </Card>
              </motion.div>

              <motion.div variants={fadeInUp} className="relative">
                <Card className="p-8 text-center hover:shadow-xl transition-all duration-300 border-2 hover:border-primary/50 relative overflow-hidden group">
                  <div className="absolute inset-0 gradient-ai-subtle opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="relative">
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center mx-auto mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300">
                      <Sparkles className="h-8 w-8 text-white" />
                    </div>
                    <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-purple-600 text-white font-bold mb-4">
                      2
                    </div>
                    <h3 className="text-xl font-bold mb-3">AI Processing</h3>
                    <p className="text-muted-foreground">
                      Our AI analyzes content, extracts concepts, and builds relationships.
                    </p>
                  </div>
                </Card>
              </motion.div>

              <motion.div variants={fadeInUp} className="relative">
                <Card className="p-8 text-center hover:shadow-xl transition-all duration-300 border-2 hover:border-primary/50 relative overflow-hidden group">
                  <div className="absolute inset-0 gradient-ai-subtle opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="relative">
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-green-500 to-teal-500 flex items-center justify-center mx-auto mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300">
                      <Network className="h-8 w-8 text-white" />
                    </div>
                    <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-green-600 text-white font-bold mb-4">
                      3
                    </div>
                    <h3 className="text-xl font-bold mb-3">Explore & Learn</h3>
                    <p className="text-muted-foreground">
                      Navigate your mind map, click nodes, and ask questions for deeper insights.
                    </p>
                  </div>
                </Card>
              </motion.div>
            </div>
          </motion.section>

          {/* Features Section */}
          <motion.section
            id="features"
            className="mb-20 md:mb-32 scroll-mt-20"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            variants={staggerContainer}
          >
            <motion.div className="text-center mb-12" variants={fadeInUp}>
              <Badge className="mb-4 gradient-ai text-white">Features</Badge>
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4">
                Everything you need for{' '}
                <span className="gradient-text">intelligent learning</span>
              </h2>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <motion.div variants={fadeInUp}>
                <Card className="p-6 hover:shadow-xl transition-all duration-300 border-2 hover:border-primary/50 group h-full">
                  <div className="w-12 h-12 gradient-ai rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                    <Brain className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold mb-2">AI-Powered Analysis</h3>
                  <p className="text-muted-foreground">
                    Advanced LangGraph workflows extract key concepts and relationships from your documents automatically.
                  </p>
                </Card>
              </motion.div>

              <motion.div variants={fadeInUp}>
                <Card className="p-6 hover:shadow-xl transition-all duration-300 border-2 hover:border-primary/50 group h-full">
                  <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-teal-500 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                    <Network className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold mb-2">Interactive Exploration</h3>
                  <p className="text-muted-foreground">
                    Navigate through hierarchical concepts, zoom in on details, and discover interconnected ideas.
                  </p>
                </Card>
              </motion.div>

              <motion.div variants={fadeInUp}>
                <Card className="p-6 hover:shadow-xl transition-all duration-300 border-2 hover:border-primary/50 group h-full">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                    <Sparkles className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold mb-2">Smart RAG Insights</h3>
                  <p className="text-muted-foreground">
                    Ask questions about any concept and get AI-powered answers with cited sources using intelligent retrieval.
                  </p>
                </Card>
              </motion.div>

              <motion.div variants={fadeInUp}>
                <Card className="p-6 hover:shadow-xl transition-all duration-300 border-2 hover:border-primary/50 group h-full">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                    <MessageSquare className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold mb-2">Real-time Q&A</h3>
                  <p className="text-muted-foreground">
                    Have a conversation with your documents. Get instant, context-aware answers to your questions.
                  </p>
                </Card>
              </motion.div>

              <motion.div variants={fadeInUp}>
                <Card className="p-6 hover:shadow-xl transition-all duration-300 border-2 hover:border-primary/50 group h-full">
                  <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                    <Zap className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold mb-2">Lightning Fast</h3>
                  <p className="text-muted-foreground">
                    Optimized processing pipeline generates comprehensive mind maps in seconds, not minutes.
                  </p>
                </Card>
              </motion.div>

              <motion.div variants={fadeInUp}>
                <Card className="p-6 hover:shadow-xl transition-all duration-300 border-2 hover:border-primary/50 group h-full">
                  <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                    <Shield className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold mb-2">Secure & Private</h3>
                  <p className="text-muted-foreground">
                    Your documents are processed securely. We prioritize your privacy and data protection.
                  </p>
                </Card>
              </motion.div>
            </div>
          </motion.section>

          {/* Recent Maps Section */}
          {isAuthenticated && mapHistory.length > 0 && (
            <motion.section
              id="recent-maps"
              className="mb-20 scroll-mt-20"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              variants={staggerContainer}
            >
              <motion.div className="text-center mb-12" variants={fadeInUp}>
                <Badge className="mb-4 gradient-ai text-white">Your Maps</Badge>
                <h2 className="text-3xl md:text-4xl font-bold mb-4">Recent Mind Maps</h2>
                <p className="text-lg text-muted-foreground">
                  Continue where you left off
                </p>
              </motion.div>

              <motion.div
                className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto"
                variants={staggerContainer}
              >
                {mapHistory.slice(0, 6).map((item, index) => (
                  <motion.div
                    key={item.map_id}
                    variants={fadeInUp}
                    className="relative group"
                    whileHover={{ y: -5 }}
                    transition={{ type: "spring" as const, stiffness: 300 }}
                  >
                    <Card
                      className="overflow-hidden hover:shadow-2xl transition-all duration-300 cursor-pointer border-2 hover:border-primary/50"
                      onClick={async () => {
                        const { useAppStore } = await import('@/lib/store');
                        const { jwt } = useAppStore.getState();
                        if (!jwt) return;

                        try {
                          const result = await getHierarchicalMindMap(item.map_id, jwt);
                          if (result.data) {
                            useAppStore.getState().setCurrentMindMap(result.data);
                            toast.success('Mind map loaded successfully');
                          } else {
                            toast.error('Failed to load hierarchical mind map');
                          }
                        } catch (error) {
                          console.error('Error loading mind map:', error);
                          toast.error('Failed to load hierarchical mind map');
                        }
                      }}
                    >
                      <div className="aspect-video relative gradient-ai-subtle flex items-center justify-center overflow-hidden">
                        <div className="absolute inset-0 gradient-animated opacity-20" />
                        <Network className="h-16 w-16 text-primary/60 relative z-10 group-hover:scale-110 transition-transform duration-300" />
                      </div>

                      <div className="p-5 space-y-3">
                        <div className="flex items-center justify-between">
                          <Badge variant="secondary" className="text-xs">
                            <BookOpen className="w-3 h-3 mr-1" />
                            PDF
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {new Date(item.created_at).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric'
                            })}
                          </span>
                        </div>

                        <h3 className="font-semibold text-lg group-hover:text-primary transition-colors line-clamp-2">
                          {item.original_filename.replace('.pdf', '')}
                        </h3>
                      </div>
                    </Card>

                    {/* Open in New Tab Button */}
                    <Button
                      variant="secondary"
                      size="icon"
                      className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200 shadow-xl h-10 w-10 z-10"
                      onClick={(e) => {
                        e.stopPropagation();
                        window.open(`/maps/${item.map_id}`, '_blank');
                      }}
                      title="Open in new tab"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </motion.div>
                ))}
              </motion.div>

              {mapHistory.length > 6 && (
                <motion.div className="text-center mt-8" variants={fadeInUp}>
                  <Button variant="outline" size="lg" className="gap-2 hover:border-primary/50">
                    View All Maps ({mapHistory.length})
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </motion.div>
              )}
            </motion.section>
          )}

          {/* CTA Section */}
          <motion.section
            className="text-center py-20 px-4"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={fadeInUp}
          >
            <Card className="max-w-4xl mx-auto p-12 relative overflow-hidden border-2">
              <div className="absolute inset-0 gradient-ai-subtle" />
              <div className="relative space-y-6">
                <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold">
                  Ready to transform your{' '}
                  <span className="gradient-text">learning experience</span>?
                </h2>
                <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">
                  Start creating intelligent mind maps from your documents today.
                </p>
                <div className="flex flex-wrap justify-center gap-4 pt-4">
                  <Button
                    size="lg"
                    className="gap-2 shadow-xl gradient-ai text-white hover:opacity-90"
                    onClick={() => {
                      document.getElementById('hero')?.scrollIntoView({ behavior: 'smooth' });
                    }}
                  >
                    <Upload className="h-5 w-5" />
                    Get Started Now
                  </Button>
                </div>
              </div>
            </Card>
          </motion.section>

          {/* Back to Top Button for home view */}
          <BackToTopButton />
        </div>
      )}
    </div>
  );
}
