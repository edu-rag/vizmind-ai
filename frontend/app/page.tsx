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
              className="w-20 h-20 mx-auto gradient-ai rounded-2xl flex items-center justify-center shadow-2xl"
              whileHover={{ scale: 1.05, rotate: 5 }}
            >
              <Brain className="h-10 w-10 text-white" />
            </motion.div>

            {/* Title */}
            <div className="space-y-4">
              <h1 className="text-5xl md:text-6xl font-bold">
                <span className="gradient-text">VizMind AI</span>
              </h1>
              <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto">
                Transform documents into intelligent mind maps with AI
              </p>
            </div>
          </motion.div>

          {/* Upload */}
          <motion.div variants={fadeIn} className="max-w-3xl mx-auto w-full">
            <FileDropZone />
          </motion.div>

          {/* Quick Actions */}
          {isAuthenticated && mapHistory.length > 0 && (
            <motion.div variants={fadeIn}>
              <Button size="lg" className="gap-2 gradient-ai text-white" asChild>
                <a href={`/maps/${mapHistory[0].map_id}`}>
                  <BookOpen className="h-5 w-5" />
                  Open Latest Map
                </a>
              </Button>
            </motion.div>
          )}
        </motion.section>

        {/* Features - Simple 3 column */}
        <motion.section
          className="mb-20"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={stagger}
        >
          <motion.div variants={fadeIn} className="text-center mb-12">
            <Badge className="mb-4 gradient-ai text-white">How It Works</Badge>
            <h2 className="text-3xl md:text-4xl font-bold">
              <span className="gradient-text">Simple & Fast</span>
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            <motion.div variants={fadeIn}>
              <Card className="p-8 text-center hover:shadow-xl transition-all group h-full">
                <div className="w-14 h-14 gradient-ai rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <Upload className="h-7 w-7 text-white" />
                </div>
                <div className="w-8 h-8 rounded-full bg-primary text-white font-bold mx-auto mb-3 flex items-center justify-center">
                  1
                </div>
                <h3 className="text-lg font-bold mb-2">Upload</h3>
                <p className="text-sm text-muted-foreground">
                  Drop your PDF document
                </p>
              </Card>
            </motion.div>

            <motion.div variants={fadeIn}>
              <Card className="p-8 text-center hover:shadow-xl transition-all group h-full">
                <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <Sparkles className="h-7 w-7 text-white" />
                </div>
                <div className="w-8 h-8 rounded-full bg-purple-600 text-white font-bold mx-auto mb-3 flex items-center justify-center">
                  2
                </div>
                <h3 className="text-lg font-bold mb-2">AI Processing</h3>
                <p className="text-sm text-muted-foreground">
                  AI extracts concepts automatically
                </p>
              </Card>
            </motion.div>

            <motion.div variants={fadeIn}>
              <Card className="p-8 text-center hover:shadow-xl transition-all group h-full">
                <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-teal-500 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <Network className="h-7 w-7 text-white" />
                </div>
                <div className="w-8 h-8 rounded-full bg-green-600 text-white font-bold mx-auto mb-3 flex items-center justify-center">
                  3
                </div>
                <h3 className="text-lg font-bold mb-2">Explore</h3>
                <p className="text-sm text-muted-foreground">
                  Navigate and ask questions
                </p>
              </Card>
            </motion.div>
          </div>
        </motion.section>

        {/* Key Features - 3 most important */}
        <motion.section
          className="mb-20"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={stagger}
        >
          <motion.div variants={fadeIn} className="text-center mb-12">
            <Badge className="mb-4 gradient-ai text-white">Features</Badge>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything you need
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            <motion.div variants={fadeIn}>
              <Card className="p-6 hover:shadow-xl transition-all group h-full">
                <Brain className="h-10 w-10 text-primary mb-4" />
                <h3 className="text-xl font-bold mb-2">AI-Powered</h3>
                <p className="text-muted-foreground">
                  Automatically extract and organize concepts from your documents
                </p>
              </Card>
            </motion.div>

            <motion.div variants={fadeIn}>
              <Card className="p-6 hover:shadow-xl transition-all group h-full">
                <MessageSquare className="h-10 w-10 text-primary mb-4" />
                <h3 className="text-xl font-bold mb-2">Interactive Q&A</h3>
                <p className="text-muted-foreground">
                  Ask questions and get instant AI-powered answers with sources
                </p>
              </Card>
            </motion.div>

            <motion.div variants={fadeIn}>
              <Card className="p-6 hover:shadow-xl transition-all group h-full">
                <Network className="h-10 w-10 text-primary mb-4" />
                <h3 className="text-xl font-bold mb-2">Visual Mapping</h3>
                <p className="text-muted-foreground">
                  Navigate hierarchical relationships with beautiful mind maps
                </p>
              </Card>
            </motion.div>
          </div>
        </motion.section>

        {/* Recent Maps */}
        {isAuthenticated && mapHistory.length > 0 && (
          <motion.section
            className="mb-20"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={stagger}
          >
            <motion.div variants={fadeIn} className="text-center mb-12">
              <Badge className="mb-4 gradient-ai text-white">Your Maps</Badge>
              <h2 className="text-3xl md:text-4xl font-bold">Recent Mind Maps</h2>
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
          <Card className="max-w-3xl mx-auto p-12 text-center relative overflow-hidden border-2">
            <div className="absolute inset-0 gradient-ai-subtle opacity-50" />
            <div className="relative space-y-6">
              <h2 className="text-3xl md:text-4xl font-bold">
                Ready to get started?
              </h2>
              <p className="text-lg text-muted-foreground">
                Transform your documents into intelligent mind maps today
              </p>
              <Button
                size="lg"
                className="gap-2 gradient-ai text-white"
                onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
              >
                <Upload className="h-5 w-5" />
                Upload Your First Document
              </Button>
            </div>
          </Card>
        </motion.section>

      </div>
    </div>
  );
}
