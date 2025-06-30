'use client';

import { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  Panel,
  MarkerType,
  Handle,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { RotateCcw, Maximize2, Minimize2 } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import { ThemeToggle } from '@/components/ThemeToggle';

const nodeTypes = {
  concept: ConceptNode,
};

function ConceptNode({ data, selected }: { data: any; selected: boolean }) {
  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 bg-background transition-all duration-200 min-w-[120px] text-center shadow-sm relative',
        'touch-target cursor-pointer',
        selected
          ? 'border-primary shadow-lg scale-105'
          : 'border-border hover:border-primary/50 hover:shadow-md'
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!w-2 !h-2 !bg-primary"
      />
      <div className="font-medium text-responsive-sm text-foreground">
        {data.label}
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-2 !h-2 !bg-primary"
      />
    </div>
  );
}

export function ConceptMapDisplay() {
  const { currentMap, setSelectedNode, setDetailPanelOpen } = useAppStore();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    if (currentMap?.react_flow_data) {
      const { nodes: mapNodes, edges: mapEdges } = currentMap.react_flow_data;

      console.log('ConceptMapDisplay: Raw data from backend:', {
        nodes: mapNodes.length,
        edges: mapEdges.length,
        nodesSample: mapNodes.slice(0, 3),
        edgesSample: mapEdges.slice(0, 3)
      });

      // Validate backend data structure
      if (!Array.isArray(mapNodes) || !Array.isArray(mapEdges)) {
        console.error('ConceptMapDisplay: Invalid data structure from backend', {
          nodesType: typeof mapNodes,
          edgesType: typeof mapEdges,
          nodesIsArray: Array.isArray(mapNodes),
          edgesIsArray: Array.isArray(mapEdges)
        });
        return;
      }

      // Transform nodes to include custom styling
      const styledNodes = mapNodes.map((node, index) => {
        // Ensure node has required properties
        const nodeId = node.id || `node-${index}`;
        const nodeLabel = node.data?.label || 'Unlabeled Node';
        const nodePosition = node.position || { x: 100 + (index % 5) * 200, y: 100 + Math.floor(index / 5) * 150 };

        return {
          id: nodeId,
          type: 'concept', // Ensure all nodes are of type 'concept'
          data: {
            label: nodeLabel,
          },
          position: nodePosition,
          style: {
            width: 'auto',
            height: 'auto',
          },
        };
      });

      // Transform edges to include custom styling
      const styledEdges = mapEdges.map((edge, index) => {
        // Ensure edge has required properties
        const edgeId = edge.id || `edge-${index}`;
        const edgeSource = edge.source;
        const edgeTarget = edge.target;
        const edgeLabel = edge.label;

        // Validate edge connectivity
        if (!edgeSource || !edgeTarget) {
          console.warn('ConceptMapDisplay: Edge missing source or target', edge);
          return null;
        }

        // Check if source and target nodes exist
        const sourceExists = styledNodes.some(node => node.id === edgeSource);
        const targetExists = styledNodes.some(node => node.id === edgeTarget);

        if (!sourceExists || !targetExists) {
          console.warn('ConceptMapDisplay: Edge references non-existent nodes', {
            edge,
            sourceExists,
            targetExists,
            availableNodeIds: styledNodes.map(n => n.id)
          });
          return null;
        }

        return {
          id: edgeId,
          source: edgeSource,
          target: edgeTarget,
          type: 'default',
          animated: true,
          label: edgeLabel,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 20,
            height: 20,
            color: 'hsl(var(--primary))',
          },
          style: {
            stroke: 'hsl(var(--primary))',
            strokeWidth: 2
          },
          labelStyle: {
            fill: 'hsl(var(--foreground))',
            fontSize: isMobile ? 10 : 12,
            fontWeight: 500,
          },
          labelBgStyle: {
            fill: 'hsl(var(--background))',
            fillOpacity: 0.8,
          },
        };
      }).filter((edge): edge is NonNullable<typeof edge> => edge !== null); // Type-safe filter

      console.log('ConceptMapDisplay: Transformed data:', {
        styledNodes: styledNodes.length,
        styledEdges: styledEdges.length,
        nodesSample: styledNodes.slice(0, 3),
        edgesSample: styledEdges.slice(0, 3)
      });

      // Log any issues with connectivity
      if (styledEdges.length < mapEdges.length) {
        console.warn('ConceptMapDisplay: Some edges were filtered out due to connectivity issues', {
          originalEdges: mapEdges.length,
          filteredEdges: styledEdges.length,
          difference: mapEdges.length - styledEdges.length
        });
      }

      setNodes(styledNodes);
      setEdges(styledEdges);
    }
  }, [currentMap, setNodes, setEdges, isMobile]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node.id);
    setDetailPanelOpen(true);
  }, [setSelectedNode, setDetailPanelOpen]);

  const handleReset = () => {
    if (currentMap?.react_flow_data) {
      const { nodes: mapNodes, edges: mapEdges } = currentMap.react_flow_data;

      console.log('ConceptMapDisplay: Resetting view with data:', {
        nodes: mapNodes.length,
        edges: mapEdges.length
      });

      // Use the same transformation logic as in useEffect
      const styledNodes = mapNodes.map((node, index) => {
        const nodeId = node.id || `node-${index}`;
        const nodeLabel = node.data?.label || 'Unlabeled Node';
        const nodePosition = node.position || { x: 100 + (index % 5) * 200, y: 100 + Math.floor(index / 5) * 150 };

        return {
          id: nodeId,
          type: 'concept', // Ensure all nodes are of type 'concept'
          data: { label: nodeLabel },
          position: nodePosition,
          style: {
            width: 'auto',
            height: 'auto',
          },
        };
      });

      const styledEdges = mapEdges.map((edge, index) => {
        const edgeId = edge.id || `edge-${index}`;
        const edgeSource = edge.source;
        const edgeTarget = edge.target;
        const edgeLabel = edge.label;

        if (!edgeSource || !edgeTarget) return null;

        const sourceExists = styledNodes.some(node => node.id === edgeSource);
        const targetExists = styledNodes.some(node => node.id === edgeTarget);

        if (!sourceExists || !targetExists) return null;

        return {
          id: edgeId,
          source: edgeSource,
          target: edgeTarget,
          type: 'default',
          animated: true,
          label: edgeLabel,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 20,
            height: 20,
            color: 'hsl(var(--primary))',
          },
          style: {
            stroke: 'hsl(var(--primary))',
            strokeWidth: 2
          },
          labelStyle: {
            fill: 'hsl(var(--foreground))',
            fontSize: isMobile ? 10 : 12,
            fontWeight: 500,
          },
          labelBgStyle: {
            fill: 'hsl(var(--background))',
            fillOpacity: 0.8,
          },
        };
      }).filter((edge): edge is NonNullable<typeof edge> => edge !== null);

      setNodes(styledNodes);
      setEdges(styledEdges);
    }
  };

  const toggleFullscreen = () => {
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
  };

  if (!currentMap) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <p className="text-lg font-medium">No concept map available</p>
          <p className="text-sm">Upload a document to generate a concept map</p>
        </div>
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <p className="text-lg font-medium">No concepts found</p>
          <p className="text-sm">The document may not contain enough conceptual content</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn(
      'h-full bg-background border border-border rounded-lg overflow-hidden',
      isFullscreen && 'fixed inset-0 z-50 rounded-none'
    )}>
      <div className="h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.1}
          maxZoom={2}
          defaultViewport={{ x: 0, y: 0, zoom: isMobile ? 0.8 : 1 }}
          className="bg-background"
          nodesDraggable={!isMobile}
          nodesConnectable={!isMobile}
          elementsSelectable={true}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={isMobile ? 15 : 20}
            size={1}
            color="hsl(var(--muted-foreground))"
            className="opacity-30"
          />

          <Controls
            className="bg-background border border-border rounded-lg shadow-sm"
            showZoom
            showFitView
            showInteractive={!isMobile}
            position={isMobile ? 'bottom-right' : 'bottom-left'}
          />

          <Panel position="top-left" className="space-x-2">
            <Card className="p-2">
              <div className={cn(
                'flex items-center space-x-2',
                isMobile && 'flex-col space-x-0 space-y-2'
              )}>
                <Button
                  variant="ghost"
                  size={isMobile ? 'icon' : 'sm'}
                  onClick={handleReset}
                  className="touch-target"
                  aria-label="Reset view"
                >
                  <RotateCcw className="h-4 w-4" />
                  {!isMobile && <span className="ml-1">Reset</span>}
                </Button>

                <Button
                  variant="ghost"
                  size={isMobile ? 'icon' : 'sm'}
                  onClick={toggleFullscreen}
                  className="touch-target"
                  aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
                >
                  {isFullscreen ? (
                    <Minimize2 className="h-4 w-4" />
                  ) : (
                    <Maximize2 className="h-4 w-4" />
                  )}
                  {!isMobile && (
                    <span className="ml-1">
                      {isFullscreen ? 'Exit' : 'Fullscreen'}
                    </span>
                  )}
                </Button>

                <ThemeToggle size="icon" className="touch-target" />
              </div>
            </Card>
          </Panel>

          <Panel position="top-right">
            <Card className="p-3 max-w-xs">
              <div className="text-responsive-sm">
                <p className="font-medium text-foreground mb-1 truncate">
                  {currentMap.source_filename}
                </p>
                <p className="text-muted-foreground text-responsive-xs">
                  {isMobile ? 'Tap nodes to explore' : 'Click on nodes to explore concepts'}
                </p>
              </div>
            </Card>
          </Panel>
        </ReactFlow>
      </div>
    </div>
  );
}
