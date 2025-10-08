'use client';

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Canvas, Node as ReaflowNode, Edge as ReaflowEdge, NodeData, EdgeData, CanvasRef } from 'reaflow';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Maximize2, Minimize2, RotateCcw, ZoomIn, ZoomOut, Sparkles, Brain } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Types for the hierarchical data structure
interface HierarchicalNode {
  id: string;
  data: { label: string };
  children: HierarchicalNode[];
}

// Custom Node Component with beautiful gradients
const CustomNode = ({ id, width = 200, height = 40, nodeMapping, ...nodeProps }: any) => {
  const { selectedNodeData, setSelectedNodeData, setDetailPanelOpen } = useAppStore();
  const [isHovered, setIsHovered] = useState(false);

  const handleClick = useCallback((event: React.MouseEvent) => {
    event.stopPropagation();
    console.log('Node clicked:', id);
    console.log('Available node mappings:', Array.from(nodeMapping.keys()));

    let fullNodeData = nodeMapping.get(id);

    if (!fullNodeData) {
      let originalId = id;

      if (id.startsWith('ref-')) {
        const parts = id.split('-');
        if (parts.length >= 4 && parts[2] === 'node') {
          originalId = parts.slice(3).join('-');
        }
      }

      console.log('Trying to find original ID:', originalId, 'from reaflow ID:', id);
      fullNodeData = nodeMapping.get(originalId);

      if (!fullNodeData) {
        for (const [mappingId, nodeData] of nodeMapping.entries()) {
          if (id.endsWith(mappingId) || mappingId === originalId || id.includes(mappingId)) {
            fullNodeData = nodeData;
            console.log('Found node via flexible match:', mappingId, '->', id);
            break;
          }
        }
      }
    }

    console.log('Found node data:', fullNodeData);

    if (fullNodeData) {
      console.log('Setting selected node data and opening panel');
      setSelectedNodeData(fullNodeData);
      setTimeout(() => {
        setDetailPanelOpen(true);
      }, 0);
    } else {
      console.warn('Could not find node data for id:', id);
      console.warn('Available IDs:', Array.from(nodeMapping.keys()));
    }
  }, [id, setSelectedNodeData, setDetailPanelOpen, nodeMapping]);

  const isSelected = useMemo(() => {
    if (!selectedNodeData) return false;

    if (selectedNodeData.id === id) return true;

    if (id.startsWith('ref-')) {
      const parts = id.split('-');
      if (parts.length >= 4 && parts[2] === 'node') {
        const originalId = parts.slice(3).join('-');
        return selectedNodeData.id === originalId;
      }
    }

    return false;
  }, [selectedNodeData, id]);

  return (
    <ReaflowNode
      {...nodeProps}
      id={id}
      width={width}
      height={height}
      onClick={handleClick}
      draggable={false}
    >
      <motion.div
        className={cn(
          'w-full h-full rounded-xl transition-all duration-300 cursor-pointer relative overflow-hidden',
          'flex items-center justify-center text-center shadow-lg',
          isSelected
            ? 'gradient-ai shadow-xl ring-4 ring-primary/30'
            : 'bg-background border-2 border-border shadow-md',
          'hover:shadow-2xl hover:scale-105'
        )}
        style={{ width, height }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.98 }}
      >
        {/* Gradient overlay on hover */}
        <AnimatePresence>
          {isHovered && !isSelected && (
            <motion.div
              className="absolute inset-0 bg-gradient-to-br from-primary/10 to-purple-500/10"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            />
          )}
        </AnimatePresence>

        {/* Sparkle icon for selected nodes */}
        {isSelected && (
          <motion.div
            className="absolute top-1 right-1"
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: 'spring' as const, stiffness: 200 }}
          >
            <Sparkles className="h-3 w-3 text-white drop-shadow-lg" />
          </motion.div>
        )}

        <div
          className={cn(
            'font-semibold text-xs truncate leading-tight px-3 relative z-10',
            isSelected ? 'text-white' : 'text-foreground'
          )}
        >
          {nodeProps.text || id}
        </div>
      </motion.div>
    </ReaflowNode>
  );
};

// Custom Edge Component with gradient
const CustomEdge = (edgeProps: any) => {
  return (
    <ReaflowEdge
      {...edgeProps}
      className="transition-colors duration-200"
      style={{
        stroke: 'hsl(var(--primary))',
        strokeWidth: 2.5,
        strokeOpacity: 0.4,
        markerEnd: 'url(#arrowhead-gradient)',
      }}
    />
  );
};

/**
 * Convert hierarchical JSON to reaflow format
 */
function convertHierarchyToReaflow(hierarchy: HierarchicalNode): {
  nodes: NodeData[],
  edges: EdgeData[],
  nodeMapping: Map<string, HierarchicalNode>
} {
  const nodes: NodeData[] = [];
  const edges: EdgeData[] = [];
  const nodeMapping = new Map<string, HierarchicalNode>();

  function traverse(node: HierarchicalNode, parentId: string | null = null) {
    const textWidth = Math.max(120, Math.min(220, node.data.label.length * 7 + 30));

    nodes.push({
      id: node.id,
      text: node.data.label,
      width: textWidth,
      height: 50,
    });

    nodeMapping.set(node.id, node);

    if (parentId) {
      edges.push({
        id: `${parentId}-${node.id}`,
        from: parentId,
        to: node.id,
      });
    }

    if (node.children && node.children.length > 0) {
      node.children.forEach(child => traverse(child, node.id));
    }
  }

  traverse(hierarchy);

  return { nodes, edges, nodeMapping };
}

export function HierarchicalMindMapDisplay() {
  const { currentMindMap, selectedNodeData, setSelectedNodeData, setDetailPanelOpen } = useAppStore();
  const [nodes, setNodes] = useState<NodeData[]>([]);
  const [edges, setEdges] = useState<EdgeData[]>([]);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [nodeMapping, setNodeMapping] = useState<Map<string, HierarchicalNode>>(new Map());
  const [shouldFit, setShouldFit] = useState(false);
  const [zoom, setZoom] = useState(1);
  const canvasRef = useRef<CanvasRef>(null);

  // Handle resizing and get dimensions
  useEffect(() => {
    const updateDimensions = () => {
      const container = document.querySelector('#mind-map-container');
      if (container) {
        const rect = container.getBoundingClientRect();
        setDimensions({
          width: (rect.width || 800) + 400,
          height: (rect.height || 600) + 400
        });
      }
      setIsMobile(window.innerWidth < 768);
    };

    setTimeout(updateDimensions, 100);
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  useEffect(() => {
    const container = document.querySelector('#mind-map-container');
    if (!container) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setDimensions({
          width: (width || 800) + 400,
          height: (height || 600) + 400
        });
      }
    });

    resizeObserver.observe(container);
    return () => resizeObserver.disconnect();
  }, []);

  const { convertedNodes, convertedEdges, convertedNodeMapping } = useMemo(() => {
    if (!currentMindMap?.hierarchical_data) {
      return { convertedNodes: [], convertedEdges: [], convertedNodeMapping: new Map() };
    }

    try {
      const { nodes: reaflowNodes, edges: reaflowEdges, nodeMapping } = convertHierarchyToReaflow(
        currentMindMap.hierarchical_data
      );

      console.log('HierarchicalMindMapDisplay: Converted to reaflow format:', {
        nodes: reaflowNodes.length,
        edges: reaflowEdges.length,
        nodesSample: reaflowNodes.slice(0, 3),
        edgesSample: reaflowEdges.slice(0, 3),
        mappingSize: nodeMapping.size
      });

      return { convertedNodes: reaflowNodes, convertedEdges: reaflowEdges, convertedNodeMapping: nodeMapping };
    } catch (error) {
      console.error('HierarchicalMindMapDisplay: Error converting hierarchy:', error);
      return { convertedNodes: [], convertedEdges: [], convertedNodeMapping: new Map() };
    }
  }, [currentMindMap?.hierarchical_data]);

  useEffect(() => {
    setNodes(convertedNodes);
    setEdges(convertedEdges);
    setNodeMapping(convertedNodeMapping);
  }, [convertedNodes, convertedEdges, convertedNodeMapping, dimensions, currentMindMap]);

  const handleReset = useCallback(() => {
    if (currentMindMap?.hierarchical_data) {
      console.log('HierarchicalMindMapDisplay: Resetting view');

      const { nodes: reaflowNodes, edges: reaflowEdges, nodeMapping: newNodeMapping } = convertHierarchyToReaflow(
        currentMindMap.hierarchical_data
      );
      setNodes(reaflowNodes);
      setEdges(reaflowEdges);
      setNodeMapping(newNodeMapping);
      setZoom(1);

      setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
      }, 200);
    }
  }, [currentMindMap]);

  const handleFitToView = useCallback(() => {
    setShouldFit(true);
    setTimeout(() => {
      setShouldFit(false);
    }, 100);
  }, []);

  const handleZoomIn = useCallback(() => {
    setZoom(prev => Math.min(prev + 0.2, 5));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom(prev => Math.max(prev - 0.2, 0.2));
  }, []);

  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen);

    if (!isFullscreen) {
      if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  }, [isFullscreen]);

  if (!currentMindMap) {
    return (
      <motion.div
        className="flex items-center justify-center h-full"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <Card className="text-center p-8 gradient-ai-subtle border-2">
          <Brain className="h-16 w-16 mx-auto mb-4 text-primary" />
          <p className="text-lg font-semibold mb-2">No mind map available</p>
          <p className="text-sm text-muted-foreground">Upload a document to generate a hierarchical mind map</p>
        </Card>
      </motion.div>
    );
  }

  if (nodes.length === 0) {
    return (
      <motion.div
        className="flex items-center justify-center h-full"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <Card className="text-center p-8 gradient-ai-subtle border-2">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          >
            <Brain className="h-16 w-16 mx-auto mb-4 text-primary" />
          </motion.div>
          <p className="text-lg font-semibold mb-2">Loading mind map...</p>
          <p className="text-sm text-muted-foreground">Processing hierarchical structure</p>
        </Card>
      </motion.div>
    );
  }

  return (
    <div
      id="mind-map-container"
      className={cn(
        'w-full h-full bg-gradient-to-br from-background via-background to-primary/5 rounded-lg relative min-h-0 min-w-0',
        'overflow-hidden shadow-2xl border-2 border-border',
        isFullscreen && 'fixed inset-0 z-50 rounded-none'
      )}
      style={{ width: '100%', height: '100%' }}
    >
      {/* Floating Control Panel */}
      <motion.div
        className="absolute top-4 right-4 z-10 glass-strong rounded-xl p-2 shadow-xl"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex flex-col gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleZoomIn}
            className="h-10 w-10 hover:bg-primary/10 transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="h-5 w-5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleZoomOut}
            className="h-10 w-10 hover:bg-primary/10 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="h-5 w-5" />
          </Button>
          <div className="h-px bg-border my-1" />
          <Button
            variant="ghost"
            size="icon"
            onClick={handleReset}
            className="h-10 w-10 hover:bg-primary/10 transition-colors"
            title="Reset View"
          >
            <RotateCcw className="h-5 w-5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleFullscreen}
            className="h-10 w-10 hover:bg-primary/10 transition-colors"
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? (
              <Minimize2 className="h-5 w-5" />
            ) : (
              <Maximize2 className="h-5 w-5" />
            )}
          </Button>
        </div>
      </motion.div>

      {/* Stats Badge */}
      <motion.div
        className="absolute top-4 left-4 z-10 glass rounded-lg px-4 py-2 shadow-lg"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex items-center gap-2 text-sm">
          <Brain className="h-4 w-4 text-primary" />
          <span className="font-semibold">{nodes.length}</span>
          <span className="text-muted-foreground">concepts</span>
        </div>
      </motion.div>

      {/* Mind Map Canvas */}
      <div className="absolute inset-0">
        {/* SVG definitions for gradient arrow markers */}
        <svg width="0" height="0" style={{ position: 'absolute' }}>
          <defs>
            <linearGradient id="edge-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0.3" />
              <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0.7" />
            </linearGradient>
            <marker
              id="arrowhead-gradient"
              markerWidth="12"
              markerHeight="8"
              refX="11"
              refY="4"
              orient="auto"
            >
              <polygon
                points="0 0, 12 4, 0 8"
                fill="hsl(var(--primary))"
                fillOpacity="0.6"
              />
            </marker>
          </defs>
        </svg>

        <Canvas
          ref={canvasRef}
          key={`mindmap-${nodes.length}-${edges.length}`}
          nodes={nodes}
          edges={edges}
          direction="RIGHT"
          readonly={true}
          panType="drag"
          layoutOptions={{
            'elk.algorithm': 'layered',
            'elk.direction': 'RIGHT',
            'elk.spacing.nodeNode': '60',
            'elk.layered.spacing.nodeNodeBetweenLayers': '100',
            'elk.spacing.edgeNode': '40',
            'elk.layered.nodePlacement.strategy': 'NETWORK_SIMPLEX',
            'elk.alignment': 'CENTER',
            'elk.contentAlignment': 'CENTER',
            'elk.padding': '[top=1000,left=1000,bottom=1000,right=1000]',
          }}
          pannable={true}
          zoomable={true}
          animated={true}
          fit={shouldFit}
          maxWidth={8000}
          maxHeight={8000}
          maxZoom={5}
          minZoom={-2}
          width={dimensions.width}
          height={dimensions.height}
          node={(nodeProps) => (
            <CustomNode
              {...nodeProps}
              nodeMapping={nodeMapping}
              text={nodes.find(n => n.id === nodeProps.id)?.text || 'Node'}
            />
          )}
          edge={(edgeProps) => <CustomEdge {...edgeProps} />}
        />
      </div>
    </div>
  );
}
