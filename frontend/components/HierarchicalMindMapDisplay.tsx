'use client';

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Canvas, Node as ReaflowNode, Edge as ReaflowEdge, NodeData, EdgeData, CanvasRef } from 'reaflow';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Maximize2, Minimize2, RotateCcw } from 'lucide-react';

// Types for the hierarchical data structure
interface HierarchicalNode {
  id: string;
  data: { label: string };
  children: HierarchicalNode[];
}

// Custom Node Component
const CustomNode = ({ id, width = 120, height = 40, ...nodeProps }: any) => {
  const { selectedNode, setSelectedNode, setDetailPanelOpen } = useAppStore();

  const handleClick = useCallback((event: React.MouseEvent) => {
    event.stopPropagation();
    console.log('Node clicked:', id);
    setSelectedNode(id);
    setDetailPanelOpen(true);
  }, [id, setSelectedNode, setDetailPanelOpen]);

  return (
    <ReaflowNode
      {...nodeProps}
      id={id}
      width={width}
      height={height}
      onClick={handleClick}
    >
      <div
        className={cn(
          'w-full h-full px-2 py-1 rounded-md border-2 bg-background transition-all duration-200 shadow-sm flex items-center justify-center text-center cursor-pointer',
          'hover:border-primary/50 hover:shadow-md hover:scale-105',
          selectedNode === id
            ? 'border-primary bg-primary/5 shadow-lg'
            : 'border-border'
        )}
        style={{ width, height }}
      >
        <div className="font-medium text-xs text-foreground truncate leading-tight">
          {nodeProps.text || id}
        </div>
      </div>
    </ReaflowNode>
  );
};

// Custom Edge Component  
const CustomEdge = (edgeProps: any) => {
  return (
    <ReaflowEdge
      {...edgeProps}
      className="stroke-muted-foreground"
      style={{
        stroke: 'currentColor',
        strokeWidth: 2,
        markerEnd: 'url(#arrowhead)',
      }}
    />
  );
};

/**
 * Convert hierarchical JSON to reaflow format
 * This is the core function that transforms any hierarchy into flat nodes and edges
 */
function convertHierarchyToReaflow(hierarchy: HierarchicalNode): { nodes: NodeData[], edges: EdgeData[] } {
  const nodes: NodeData[] = [];
  const edges: EdgeData[] = [];

  function traverse(node: HierarchicalNode, parentId: string | null = null) {
    // Calculate dynamic width based on text length - much smaller and more reasonable
    const textWidth = Math.max(100, Math.min(200, node.data.label.length * 6 + 20));

    // Add current node to nodes array
    nodes.push({
      id: node.id,
      text: node.data.label,
      width: textWidth,
      height: 40, // Reduced height
    });

    // If this node has a parent, create an edge
    if (parentId) {
      edges.push({
        id: `${parentId}-${node.id}`,
        from: parentId,
        to: node.id,
      });
    }

    // Recursively process children
    if (node.children && node.children.length > 0) {
      node.children.forEach(child => traverse(child, node.id));
    }
  }

  // Start the traversal
  traverse(hierarchy);

  return { nodes, edges };
}

export function HierarchicalMindMapDisplay() {
  const { currentMindMap, selectedNode, setSelectedNode, setDetailPanelOpen } = useAppStore();
  const [nodes, setNodes] = useState<NodeData[]>([]);
  const [edges, setEdges] = useState<EdgeData[]>([]);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const canvasRef = useRef<CanvasRef>(null);

  // Handle resizing and get dimensions
  useEffect(() => {
    const updateDimensions = () => {
      const container = document.querySelector('#mind-map-container');
      if (container) {
        const rect = container.getBoundingClientRect();
        setDimensions({
          width: rect.width || 800,
          height: rect.height || 600
        });
      }
      setIsMobile(window.innerWidth < 768);
    };

    // Initial dimension update with a slight delay to ensure container is rendered
    setTimeout(updateDimensions, 100);
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Additional resize observer for more precise container tracking
  useEffect(() => {
    const container = document.querySelector('#mind-map-container');
    if (!container) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setDimensions({
          width: width || 800,
          height: height || 600
        });
      }
    });

    resizeObserver.observe(container);
    return () => resizeObserver.disconnect();
  }, []);

  // Memoize the converted nodes and edges
  const { convertedNodes, convertedEdges } = useMemo(() => {
    if (!currentMindMap?.hierarchical_data) {
      return { convertedNodes: [], convertedEdges: [] };
    }

    try {
      const { nodes: reaflowNodes, edges: reaflowEdges } = convertHierarchyToReaflow(
        currentMindMap.hierarchical_data
      );

      console.log('HierarchicalMindMapDisplay: Converted to reaflow format:', {
        nodes: reaflowNodes.length,
        edges: reaflowEdges.length,
        nodesSample: reaflowNodes.slice(0, 3),
        edgesSample: reaflowEdges.slice(0, 3)
      });

      return { convertedNodes: reaflowNodes, convertedEdges: reaflowEdges };
    } catch (error) {
      console.error('HierarchicalMindMapDisplay: Error converting hierarchy:', error);
      return { convertedNodes: [], convertedEdges: [] };
    }
  }, [currentMindMap?.hierarchical_data]);

  // Update state when conversion changes
  useEffect(() => {
    setNodes(convertedNodes);
    setEdges(convertedEdges);

    // Debug logging
    console.log('HierarchicalMindMapDisplay: State updated', {
      nodesCount: convertedNodes.length,
      edgesCount: convertedEdges.length,
      dimensions,
      hasCurrentMindMap: !!currentMindMap
    });
  }, [convertedNodes, convertedEdges, dimensions, currentMindMap]);

  const handleReset = useCallback(() => {
    if (currentMindMap?.hierarchical_data) {
      console.log('HierarchicalMindMapDisplay: Resetting view');
      const { nodes: reaflowNodes, edges: reaflowEdges } = convertHierarchyToReaflow(
        currentMindMap.hierarchical_data
      );
      setNodes(reaflowNodes);
      setEdges(reaflowEdges);

      // Force a re-fit and center after a small delay
      setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
      }, 200);
    }
  }, [currentMindMap]);

  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen);

    if (!isFullscreen) {
      // Request fullscreen
      if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen();
      }
    } else {
      // Exit fullscreen
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  }, [isFullscreen]);

  if (!currentMindMap) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <p className="text-lg font-medium">No mind map available</p>
          <p className="text-sm">Upload a document to generate a hierarchical mind map</p>
        </div>
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <p className="text-lg font-medium">Loading mind map...</p>
          <p className="text-sm">Processing hierarchical structure</p>
        </div>
      </div>
    );
  }

  return (
    <div
      id="mind-map-container"
      className={cn(
        'w-full h-full bg-background border border-border rounded-lg overflow-hidden relative min-h-0 min-w-0',
        isFullscreen && 'fixed inset-0 z-50 rounded-none'
      )}
      style={{ width: '100%', height: '100%' }}
    >
      {/* Controls */}
      <div className="absolute top-4 right-4 z-10 flex gap-2">
        <Button
          variant="secondary"
          size="sm"
          onClick={handleReset}
          className="bg-background/80 backdrop-blur-sm"
        >
          <RotateCcw className="h-4 w-4" />
          {!isMobile && <span className="ml-2">Reset View</span>}
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={toggleFullscreen}
          className="bg-background/80 backdrop-blur-sm"
        >
          {isFullscreen ? (
            <>
              <Minimize2 className="h-4 w-4" />
              {!isMobile && <span className="ml-2">Exit Fullscreen</span>}
            </>
          ) : (
            <>
              <Maximize2 className="h-4 w-4" />
              {!isMobile && <span className="ml-2">Fullscreen</span>}
            </>
          )}
        </Button>
      </div>

      {/* Mind Map Canvas */}
      <div className="absolute inset-0">
        {/* SVG definitions for arrow markers */}
        <svg width="0" height="0" style={{ position: 'absolute' }}>
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3.5, 0 7"
                fill="currentColor"
                className="text-muted-foreground"
              />
            </marker>
          </defs>
        </svg>

        <Canvas
          ref={canvasRef}
          key={`${nodes.length}-${edges.length}-${dimensions.width}-${dimensions.height}`}
          nodes={nodes}
          edges={edges}
          direction="DOWN"
          layoutOptions={{
            'elk.algorithm': 'layered',
            'elk.direction': 'DOWN',
            'elk.spacing.nodeNode': '40',
            'elk.layered.spacing.nodeNodeBetweenLayers': '60',
            'elk.spacing.edgeNode': '20',
            'elk.layered.nodePlacement.strategy': 'NETWORK_SIMPLEX',
            'elk.alignment': 'CENTER',
            'elk.contentAlignment': 'CENTER',
          }}
          pannable={true}
          zoomable={true}
          animated={false}
          fit={true}
          maxZoom={3}
          minZoom={0.1}
          width={dimensions.width}
          height={dimensions.height}
          node={(nodeProps) => (
            <CustomNode
              {...nodeProps}
              text={nodes.find(n => n.id === nodeProps.id)?.text || 'Node'}
            />
          )}
          edge={(edgeProps) => <CustomEdge {...edgeProps} />}
        />
      </div>
    </div>
  );
}
