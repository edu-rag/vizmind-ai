'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ArrowRight,
  BookOpen,
  Brain,
  Network,
  ExternalLink,
  ArrowLeft,
  Upload,
  MessageSquare,
  Sparkles,
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { getHierarchicalMindMap } from '@/lib/api';
import { FileDropZone } from '@/components/FileDropZone';
import { HierarchicalMindMapDisplay } from '@/components/HierarchicalMindMapDisplay';
import { NodeDetailPanel } from '@/components/NodeDetailPanel';
import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

export default function Home() {
  const { isAuthenticated, mapHistory, currentMindMap } = useAppStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  // Animation variants
  const fadeIn = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
  };

  const stagger = {
    visible: { transition: { staggerChildren: 0.1 } }
  };

  // Map View - when a map is loaded
  if (currentMindMap) {
    return (
      <div className="h-screen flex flex-col">
        {/* Header */}
        <div className="border-b border-border bg-background/95 backdrop-blur-sm p-4 shrink-0">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => useAppStore.getState().setCurrentMindMap(null)}
                className="touch-target"
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div>
                <h1 className="text-lg font-semibold truncate">
                  {currentMindMap.title || 'Mind Map'}
                </h1>
                <p className="text-sm text-muted-foreground">
                  Interactive visualization
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(`/maps/${currentMindMap.mongodb_doc_id}`, '_blank')}
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              New Tab
            </Button>
          </div>
        </div>

        {/* Map Content */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full p-4">
            <HierarchicalMindMapDisplay />
          </div>
        </div>

        <NodeDetailPanel />
      </div>
    );
  }

  // Home View
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-12 max-w-6xl">

        {/* Hero Section */}
        <motion.section
          className="text-center space-y-8 mb-20 min-h-[80vh] flex flex-col justify-center"
          initial="hidden"
          animate="visible"
          variants={stagger}
        >
          <motion.div variants={fadeIn} className="space-y-6">
            {/* Logo */}
            <motion.div
              className="w-24 h-24 mx-auto gradient-ai rounded-3xl flex items-center justify-center shadow-2xl glow-ai"
              whileHover={{ scale: 1.05, rotate: 5 }}
            >
              <Brain className="h-12 w-12 text-white" />
            </motion.div>

            {/* Title with Badge */}
            <div className="space-y-4">
              <div className="flex items-center justify-center gap-3 flex-wrap">
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold">
                  Transform Your
                </h1>
                <Badge className="text-2xl md:text-3xl lg:text-4xl px-4 py-2 gradient-ai text-white font-bold">
                  DOCS
                </Badge>
              </div>
              <p className="text-base md:text-lg lg:text-xl text-muted-foreground max-w-2xl mx-auto">
                into intelligent mind maps with AI-powered insights and interactive Q&A
              </p>
            </div>
          </motion.div>

          {/* Upload */}
          <motion.div variants={fadeIn} className="max-w-3xl mx-auto w-full">
            <FileDropZone />
          </motion.div>

          {/* Quick Actions */}
          {isAuthenticated && mapHistory.length > 0 && (
            <motion.div variants={fadeIn} className="flex gap-3 justify-center">
              <Button size="lg" className="gap-2 gradient-ai text-white shadow-xl hover:shadow-2xl transition-all" asChild>
                <a href={`/maps/${mapHistory[0].map_id}`}>
                  <BookOpen className="h-5 w-5" />
                  Open Latest Map
                </a>
              </Button>
            </motion.div>
          )}

          {/* Trust Badges */}
          <motion.div variants={fadeIn} className="pt-8">
            <p className="text-sm text-muted-foreground mb-4">Trusted by teams at</p>
            <div className="flex items-center justify-center gap-8 flex-wrap opacity-60">
              <div className="text-xs font-semibold tracking-wider">HARVARD</div>
              <div className="text-xs font-semibold tracking-wider">STANFORD</div>
              <div className="text-xs font-semibold tracking-wider">MIT</div>
              <div className="text-xs font-semibold tracking-wider">YALE</div>
            </div>
          </motion.div>
        </motion.section>

        {/* Features - Simple 3 column */}
        <motion.section
          className="mb-24"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={stagger}
        >
          <motion.div variants={fadeIn} className="text-center mb-16">
            <Badge className="mb-4 text-sm px-4 py-1.5 bg-primary/10 text-primary border-primary/20">
              How It Works
            </Badge>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4">
              Simple & Fast
            </h2>
            <p className="text-base md:text-lg text-muted-foreground max-w-2xl mx-auto">
              Transform your documents in three easy steps
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <motion.div variants={fadeIn}>
              <Card className="p-8 text-center hover:shadow-2xl transition-all group h-full border-2 hover:border-primary/30 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative">
                  <div className="w-16 h-16 gradient-ai rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform shadow-lg">
                    <Upload className="h-8 w-8 text-white" />
                  </div>
                  <div className="w-10 h-10 rounded-full bg-primary text-white font-bold mx-auto mb-4 flex items-center justify-center text-lg shadow-lg">
                    1
                  </div>
                  <h3 className="text-xl font-bold mb-3">Upload Document</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Drop a single PDF document and let our AI analyze it
                  </p>
                </div>
              </Card>
            </motion.div>

            <motion.div variants={fadeIn}>
              <Card className="p-8 text-center hover:shadow-2xl transition-all group h-full border-2 hover:border-primary/30 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative">
                  <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform shadow-lg">
                    <Sparkles className="h-8 w-8 text-white" />
                  </div>
                  <div className="w-10 h-10 rounded-full bg-purple-600 text-white font-bold mx-auto mb-4 flex items-center justify-center text-lg shadow-lg">
                    2
                  </div>
                  <h3 className="text-xl font-bold mb-3">AI Processing</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Advanced AI extracts key concepts automatically
                  </p>
                </div>
              </Card>
            </motion.div>

            <motion.div variants={fadeIn}>
              <Card className="p-8 text-center hover:shadow-2xl transition-all group h-full border-2 hover:border-primary/30 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative">
                  <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-teal-500 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform shadow-lg">
                    <Network className="h-8 w-8 text-white" />
                  </div>
                  <div className="w-10 h-10 rounded-full bg-green-600 text-white font-bold mx-auto mb-4 flex items-center justify-center text-lg shadow-lg">
                    3
                  </div>
                  <h3 className="text-xl font-bold mb-3">Explore & Chat</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Navigate mind maps and ask intelligent questions
                  </p>
                </div>
              </Card>
            </motion.div>
          </div>
        </motion.section>

        {/* Key Features - 3 most important */}
        <motion.section
          className="mb-24"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={stagger}
        >
          <motion.div variants={fadeIn} className="text-center mb-16">
            <Badge className="mb-4 text-sm px-4 py-1.5 bg-primary/10 text-primary border-primary/20">
              Features
            </Badge>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4">
              Everything you need
            </h2>
            <p className="text-base md:text-lg text-muted-foreground max-w-2xl mx-auto">
              Powerful AI features to enhance your document workflow
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <motion.div variants={fadeIn}>
              <Card className="p-8 hover:shadow-2xl transition-all group h-full border-2 hover:border-primary/30">
                <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Brain className="h-7 w-7 text-primary" />
                </div>
                <h3 className="text-xl font-bold mb-3">AI-Powered Analysis</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Automatically extract and organize key concepts from your documents with advanced AI
                </p>
              </Card>
            </motion.div>

            <motion.div variants={fadeIn}>
              <Card className="p-8 hover:shadow-2xl transition-all group h-full border-2 hover:border-primary/30">
                <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <MessageSquare className="h-7 w-7 text-primary" />
                </div>
                <h3 className="text-xl font-bold mb-3">Interactive Q&A</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Ask questions and get instant AI-powered answers with accurate source references
                </p>
              </Card>
            </motion.div>

            <motion.div variants={fadeIn}>
              <Card className="p-8 hover:shadow-2xl transition-all group h-full border-2 hover:border-primary/30">
                <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Network className="h-7 w-7 text-primary" />
                </div>
                <h3 className="text-xl font-bold mb-3">Visual Mind Maps</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Navigate hierarchical relationships with beautiful, interactive mind maps
                </p>
              </Card>
            </motion.div>
          </div>
        </motion.section>

        {/* Recent Maps */}
        {isAuthenticated && mapHistory.length > 0 && (
          <motion.section
            className="mb-24"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={stagger}
          >
            <motion.div variants={fadeIn} className="text-center mb-16">
              <Badge className="mb-4 text-sm px-4 py-1.5 bg-primary/10 text-primary border-primary/20">
                Your Maps
              </Badge>
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4">
                Recent Mind Maps
              </h2>
              <p className="text-base md:text-lg text-muted-foreground">
                Quick access to your latest documents
              </p>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-6">
              {mapHistory.slice(0, 6).map((item) => (
                <motion.div
                  key={item.map_id}
                  variants={fadeIn}
                  whileHover={{ y: -5 }}
                  className="relative group"
                >
                  <Card
                    className="overflow-hidden hover:shadow-2xl transition-all cursor-pointer border-2 hover:border-primary/50"
                    onClick={async () => {
                      const { jwt } = useAppStore.getState();
                      if (!jwt) return;

                      try {
                        const result = await getHierarchicalMindMap(item.map_id, jwt);
                        if (result.data) {
                          useAppStore.getState().setCurrentMindMap(result.data);
                          toast.success('Mind map loaded');
                        }
                      } catch (error) {
                        toast.error('Failed to load mind map');
                      }
                    }}
                  >
                    {/* Preview */}
                    <div className="aspect-video gradient-ai-subtle flex items-center justify-center relative overflow-hidden">
                      <div className="absolute inset-0 gradient-animated opacity-20" />
                      <Network className="h-12 w-12 text-primary/60 relative z-10 group-hover:scale-110 transition-transform" />
                    </div>

                    {/* Info */}
                    <div className="p-4">
                      <div className="flex items-center justify-between mb-2">
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
                      <h3 className="font-semibold group-hover:text-primary transition-colors line-clamp-2">
                        {item.original_filename.replace('.pdf', '')}
                      </h3>
                    </div>
                  </Card>

                  {/* Open in New Tab */}
                  <Button
                    variant="secondary"
                    size="icon"
                    className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity shadow-xl z-10"
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(`/maps/${item.map_id}`, '_blank');
                    }}
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                </motion.div>
              ))}
            </div>

            {mapHistory.length > 6 && (
              <motion.div variants={fadeIn} className="text-center mt-8">
                <p className="text-muted-foreground">
                  and {mapHistory.length - 6} more maps...
                </p>
              </motion.div>
            )}
          </motion.section>
        )}

        {/* CTA */}
        <motion.section
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={fadeIn}
        >
          <Card className="max-w-4xl mx-auto p-12 md:p-16 text-center relative overflow-hidden border-2 shadow-2xl">
            <div className="absolute inset-0 gradient-ai opacity-5" />
            <div className="relative space-y-8">
              <div className="space-y-4">
                <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold">
                  Ready to get started?
                </h2>
                <p className="text-base md:text-lg text-muted-foreground max-w-2xl mx-auto">
                  Transform your documents into intelligent mind maps today. Upload your first PDF and experience the power of AI.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button
                  size="lg"
                  className="gap-2 gradient-ai text-white shadow-xl hover:shadow-2xl transition-all text-base"
                  onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                >
                  <Upload className="h-5 w-5" />
                  Upload Your First Document
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="gap-2 text-base"
                >
                  <BookOpen className="h-5 w-5" />
                  Learn More
                </Button>
              </div>
            </div>
          </Card>
        </motion.section>

      </div>
    </div>
  );
}
