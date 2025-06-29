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
        'px-4 py-3 rounded-lg border-2 bg-background transition-all duration-200 min-w-[120px] text-center shadow-sm',
        'touch-target cursor-pointer',
        selected 
          ? 'border-primary shadow-lg scale-105' 
          : 'border-border hover:border-primary/50 hover:shadow-md'
      )}
    >
      <div className="font-medium text-responsive-sm text-foreground">
        {data.label}
      </div>
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
      
      // Transform nodes to include custom styling
      const styledNodes = mapNodes.map((node) => ({
        ...node,
        type: 'concept',
        data: { 
          ...node.data,
        },
        style: {
          width: 'auto',
          height: 'auto',
        },
      }));

      // Transform edges to include custom styling
      const styledEdges = mapEdges.map((edge) => ({
        ...edge,
        type: 'smoothstep',
        animated: true,
        style: { stroke: 'hsl(var(--primary))' },
        labelStyle: { 
          fill: 'hsl(var(--foreground))', 
          fontSize: isMobile ? 10 : 12,
          fontWeight: 500,
        },
        labelBgStyle: { 
          fill: 'hsl(var(--background))', 
          fillOpacity: 0.8,
        },
      }));

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
      
      const styledNodes = mapNodes.map((node) => ({
        ...node,
        type: 'concept',
        data: { ...node.data },
      }));

      const styledEdges = mapEdges.map((edge) => ({
        ...edge,
        type: 'smoothstep',
        animated: true,
      }));

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
    return null;
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