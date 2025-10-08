'use client';

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Canvas, Node as ReaflowNode, Edge as ReaflowEdge, NodeData, EdgeData, CanvasRef } from 'reaflow';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Maximize2, Minimize2, RotateCcw, ZoomIn, ZoomOut, Sparkles, Brain, ChevronRight, ChevronDown, Maximize, Minimize } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Types for the hierarchical data structure
interface HierarchicalNode {
  id: string;
  data: { label: string };
  children: HierarchicalNode[];
}

interface NodeMetadata {
  hasChildren: boolean;
  parentId: string | null;
  depth: number;
}

// Custom Node Component with beautiful gradients
const CustomNode = ({
  id,
  width = 200,
  height = 40,
  nodeMapping,
  nodeMetadata,
  expandedNodes,
  onToggleExpand,
  text,
  ...nodeProps
}: any) => {
  const { selectedNodeData, setSelectedNodeData, setDetailPanelOpen } = useAppStore();
  const [isHovered, setIsHovered] = useState(false);

  // Extract the actual node ID from reaflow's generated ID
  // Reaflow adds "ref-XXX-node-" prefix, we need to extract the original ID
  const actualNodeId = useMemo(() => {
    if (id.startsWith('ref-') && id.includes('-node-')) {
      const parts = id.split('-node-');
      return parts.length > 1 ? parts[1] : id;
    }
    return id;
  }, [id]);

  const metadata = nodeMetadata.get(actualNodeId);
  const isExpanded = expandedNodes.has(actualNodeId);
  const hasChildren = metadata?.hasChildren || false;

  const handleNodeClick = useCallback((event: React.MouseEvent) => {
    event.stopPropagation();

    let fullNodeData = nodeMapping.get(id);

    if (!fullNodeData) {
      let originalId = id;

      if (id.startsWith('ref-')) {
        const parts = id.split('-');
        if (parts.length >= 4 && parts[2] === 'node') {
          originalId = parts.slice(3).join('-');
        }
      }

      fullNodeData = nodeMapping.get(originalId);

      if (!fullNodeData) {
        for (const [mappingId, nodeData] of nodeMapping.entries()) {
          if (id.endsWith(mappingId) || mappingId === originalId || id.includes(mappingId)) {
            fullNodeData = nodeData;
            break;
          }
        }
      }
    }


    if (fullNodeData) {
      setSelectedNodeData(fullNodeData);
      setTimeout(() => {
        setDetailPanelOpen(true);
      }, 0);
    } else {
      console.warn('Could not find node data for id:', id);
      console.warn('Available IDs:', Array.from(nodeMapping.keys()));
    }
  }, [id, setSelectedNodeData, setDetailPanelOpen, nodeMapping]);

  const handleChevronClick = useCallback((event: React.MouseEvent) => {
    event.stopPropagation();
    if (hasChildren) {
      onToggleExpand(actualNodeId);
    }
  }, [actualNodeId, hasChildren, onToggleExpand]);

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
      draggable={false}
      style={{
        fill: 'transparent',
        stroke: 'transparent',
        strokeWidth: 0
      }}
      port={null}
      label={null}
    >
      {(event) => (
        <foreignObject
          height={event.height}
          width={event.width}
          x={0}
          y={0}
          style={{ overflow: 'visible' }}
        >
          <div
            style={{
              width: '100%',
              height: '100%',
              position: 'fixed',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <motion.div
              className={cn(
                'w-full h-full rounded-xl transition-all duration-300 cursor-pointer relative overflow-visible',
                'flex items-center justify-center text-center shadow-lg',
                isSelected
                  ? 'gradient-ai shadow-xl ring-4 ring-primary/30'
                  : 'bg-background border-2 border-border shadow-md',
                'hover:shadow-2xl'
              )}
              style={{ width: event.width, height: event.height }}
              onMouseEnter={() => setIsHovered(true)}
              onMouseLeave={() => setIsHovered(false)}
              onClick={handleNodeClick}
              whileTap={{ scale: 0.98 }}
            >
              {/* Gradient overlay on hover */}
              <AnimatePresence>
                {isHovered && !isSelected && (
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-br from-primary/10 to-purple-500/10 rounded-xl"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  />
                )}
              </AnimatePresence>

              {/* Chevron icon for expandable nodes */}
              {hasChildren && (
                <div
                  className="absolute right-1 top-1/2 -translate-y-1/2 cursor-pointer"
                  onClick={handleChevronClick}
                  style={{ pointerEvents: 'auto', zIndex: 1000 }}
                >
                  <motion.div
                    className={cn(
                      "rounded-full p-1 transition-colors flex items-center justify-center shadow-lg",
                      isSelected ? "bg-white/90 hover:bg-white" : "bg-background hover:bg-primary/10 border border-border"
                    )}
                    whileHover={{ scale: 1.15 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {isExpanded ? (
                      <ChevronDown className={cn(
                        "h-3.5 w-3.5 transition-colors",
                        isSelected ? "text-primary" : "text-primary"
                      )} />
                    ) : (
                      <ChevronRight className={cn(
                        "h-3.5 w-3.5 transition-colors",
                        isSelected ? "text-primary" : "text-primary"
                      )} />
                    )}
                  </motion.div>
                </div>
              )}

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
                  'font-semibold text-xs leading-tight relative z-10',
                  isSelected ? 'text-white' : 'text-foreground',
                  hasChildren ? 'px-3 pr-6' : 'px-3'
                )}
                style={{
                  overflow: 'visible',
                  whiteSpace: 'normal',
                  wordBreak: 'break-word',
                  textAlign: 'center'
                }}
              >
                {text || id}
              </div>
            </motion.div>
          </div>
        </foreignObject>
      )}
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
  nodeMapping: Map<string, HierarchicalNode>,
  nodeMetadata: Map<string, NodeMetadata>
} {
  const nodes: NodeData[] = [];
  const edges: EdgeData[] = [];
  const nodeMapping = new Map<string, HierarchicalNode>();
  const nodeMetadata = new Map<string, NodeMetadata>();

  function traverse(node: HierarchicalNode, parentId: string | null = null, depth: number = 0) {
    const textWidth = Math.max(120, Math.min(220, node.data.label.length * 7 + 30));

    nodes.push({
      id: node.id,
      text: node.data.label,
      width: textWidth,
      height: 50,
    });

    nodeMapping.set(node.id, node);
    nodeMetadata.set(node.id, {
      hasChildren: node.children && node.children.length > 0,
      parentId,
      depth
    });

    if (parentId) {
      edges.push({
        id: `${parentId}-${node.id}`,
        from: parentId,
        to: node.id,
      });
    }

    if (node.children && node.children.length > 0) {
      node.children.forEach(child => traverse(child, node.id, depth + 1));
    }
  }

  traverse(hierarchy);

  return { nodes, edges, nodeMapping, nodeMetadata };
}

export function HierarchicalMindMapDisplay() {
  const { currentMindMap, selectedNodeData, setSelectedNodeData, setDetailPanelOpen } = useAppStore();
  const [nodes, setNodes] = useState<NodeData[]>([]);
  const [edges, setEdges] = useState<EdgeData[]>([]);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [nodeMapping, setNodeMapping] = useState<Map<string, HierarchicalNode>>(new Map());
  const [nodeMetadata, setNodeMetadata] = useState<Map<string, NodeMetadata>>(new Map());
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [shouldFit, setShouldFit] = useState(false);
  const [zoom, setZoom] = useState(1);
  const canvasRef = useRef<CanvasRef>(null);
  const canvasKey = useRef(0);

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

  const { convertedNodes, convertedEdges, convertedNodeMapping, convertedNodeMetadata } = useMemo(() => {
    if (!currentMindMap?.hierarchical_data) {
      return {
        convertedNodes: [],
        convertedEdges: [],
        convertedNodeMapping: new Map(),
        convertedNodeMetadata: new Map()
      };
    }

    try {
      const { nodes: reaflowNodes, edges: reaflowEdges, nodeMapping, nodeMetadata } = convertHierarchyToReaflow(
        currentMindMap.hierarchical_data
      );

      return {
        convertedNodes: reaflowNodes,
        convertedEdges: reaflowEdges,
        convertedNodeMapping: nodeMapping,
        convertedNodeMetadata: nodeMetadata
      };
    } catch (error) {
      console.error('HierarchicalMindMapDisplay: Error converting hierarchy:', error);
      return {
        convertedNodes: [],
        convertedEdges: [],
        convertedNodeMapping: new Map(),
        convertedNodeMetadata: new Map()
      };
    }
  }, [currentMindMap?.hierarchical_data]);

  // Initialize expanded nodes (expand root and first level by default)
  useEffect(() => {
    if (convertedNodeMetadata.size > 0 && expandedNodes.size === 0) {
      const initialExpanded = new Set<string>();

      // Find root node (node with no parent) and expand it
      convertedNodeMetadata.forEach((metadata, nodeId) => {
        if (metadata.depth === 0) {
          initialExpanded.add(nodeId);
        }
        // Also expand first level nodes
        if (metadata.depth === 1) {
          initialExpanded.add(nodeId);
        }
      });

      setExpandedNodes(initialExpanded);
    }
  }, [convertedNodeMetadata]);

  // Filter visible nodes and edges based on expanded state
  const { visibleNodes, visibleEdges } = useMemo(() => {

    if (expandedNodes.size === 0) {
      // Show all nodes if nothing is explicitly expanded yet
      return { visibleNodes: convertedNodes, visibleEdges: convertedEdges };
    }

    const visibleNodeIds = new Set<string>();

    // Helper function to get all descendants of a node
    const getDescendants = (nodeId: string): Set<string> => {
      const descendants = new Set<string>();
      convertedNodeMetadata.forEach((metadata, id) => {
        if (metadata.parentId === nodeId) {
          descendants.add(id);
          if (expandedNodes.has(id)) {
            // Recursively get descendants if this child is also expanded
            const childDescendants = getDescendants(id);
            childDescendants.forEach(d => descendants.add(d));
          }
        }
      });
      return descendants;
    };

    // Add root nodes (nodes with no parent)
    convertedNodeMetadata.forEach((metadata, nodeId) => {
      if (metadata.parentId === null) {
        visibleNodeIds.add(nodeId);
        // Add children if root is expanded
        if (expandedNodes.has(nodeId)) {
          const descendants = getDescendants(nodeId);
          descendants.forEach(d => visibleNodeIds.add(d));
        }
      }
    });


    const filteredNodes = convertedNodes.filter(node => visibleNodeIds.has(node.id));
    const filteredEdges = convertedEdges.filter(edge =>
      edge.from && edge.to && visibleNodeIds.has(edge.from) && visibleNodeIds.has(edge.to)
    );


    return { visibleNodes: filteredNodes, visibleEdges: filteredEdges };
  }, [convertedNodes, convertedEdges, convertedNodeMetadata, expandedNodes]);

  const handleToggleExpand = useCallback((nodeId: string) => {

    setExpandedNodes(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }

      // Increment key to prevent Canvas from resetting position
      canvasKey.current += 1;

      return next;
    });
  }, []);

  useEffect(() => {
    setNodes(visibleNodes);
    setEdges(visibleEdges);
    setNodeMapping(convertedNodeMapping);
    setNodeMetadata(convertedNodeMetadata);
  }, [visibleNodes, visibleEdges, convertedNodeMapping, convertedNodeMetadata, dimensions, currentMindMap]);

  const handleReset = useCallback(() => {
    if (currentMindMap?.hierarchical_data) {

      const { nodes: reaflowNodes, edges: reaflowEdges, nodeMapping: newNodeMapping, nodeMetadata: newNodeMetadata } = convertHierarchyToReaflow(
        currentMindMap.hierarchical_data
      );
      setNodes(reaflowNodes);
      setEdges(reaflowEdges);
      setNodeMapping(newNodeMapping);
      setNodeMetadata(newNodeMetadata);
      setZoom(1);

      // Reset expanded nodes to initial state (root and first level)
      const initialExpanded = new Set<string>();
      newNodeMetadata.forEach((metadata, nodeId) => {
        if (metadata.depth === 0 || metadata.depth === 1) {
          initialExpanded.add(nodeId);
        }
      });
      setExpandedNodes(initialExpanded);

      setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
      }, 200);
    }
  }, [currentMindMap]);

  const handleZoomIn = useCallback(() => {
    if (canvasRef.current?.zoomIn) {
      canvasRef.current.zoomIn();
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (canvasRef.current?.zoomOut) {
      canvasRef.current.zoomOut();
    }
  }, []);

  const handleExpandAll = useCallback(() => {
    const allNodeIds = new Set<string>();
    nodeMetadata.forEach((_, nodeId) => {
      allNodeIds.add(nodeId);
    });
    setExpandedNodes(allNodeIds);
  }, [nodeMetadata]);

  const handleCollapseAll = useCallback(() => {
    const rootNodes = new Set<string>();
    nodeMetadata.forEach((metadata, nodeId) => {
      if (metadata.depth === 0) {
        rootNodes.add(nodeId);
      }
    });
    setExpandedNodes(rootNodes);
  }, [nodeMetadata]);

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
            onClick={handleExpandAll}
            className="h-10 w-10 hover:bg-primary/10 transition-colors"
            title="Expand All Nodes"
          >
            <Maximize className="h-5 w-5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleCollapseAll}
            className="h-10 w-10 hover:bg-primary/10 transition-colors"
            title="Collapse All Nodes"
          >
            <Minimize className="h-5 w-5" />
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
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm">
            <Brain className="h-4 w-4 text-primary" />
            <span className="font-semibold">{convertedNodes.length}</span>
            <span className="text-muted-foreground">concepts</span>
          </div>
          <div className="h-4 w-px bg-border" />
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">Zoom:</span>
            <span className="font-semibold">{Math.round(zoom * 100)}%</span>
          </div>
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
          zoom={zoom}
          width={dimensions.width}
          height={dimensions.height}
          onZoomChange={(z) => setZoom(z)}
          node={(nodeProps) => (
            <CustomNode
              {...nodeProps}
              nodeMapping={nodeMapping}
              nodeMetadata={nodeMetadata}
              expandedNodes={expandedNodes}
              onToggleExpand={handleToggleExpand}
              text={nodes.find(n => n.id === nodeProps.id)?.text || 'Node'}
            />
          )}
          edge={(edgeProps) => <CustomEdge {...edgeProps} />}
        />
      </div>
    </div>
  );
}
