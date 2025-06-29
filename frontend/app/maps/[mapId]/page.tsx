'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  ArrowLeft,
  Share2,
  Download,
  MoreHorizontal,
  AlertCircle,
  Home,
  MessageCircle
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ConceptMapDisplay } from '@/components/ConceptMapDisplay';
import { NodeDetailPanel } from '@/components/NodeDetailPanel';
import { ChatSidebar } from '@/components/ChatSidebar';
import { useAppStore } from '@/lib/store';
import { getConceptMap } from '@/lib/api';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import Link from 'next/link';

export default function MapPage() {
  const params = useParams();
  const router = useRouter();
  const mapId = params.mapId as string;

  const {
    currentMap,
    setCurrentMap,
    isAuthenticated,
    jwt,
    setSelectedNode,
    setDetailPanelOpen,
    isChatSidebarOpen,
    setChatSidebarOpen
  } = useAppStore();

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
    if (mapId && jwt) {
      loadMap();
    } else if (!isAuthenticated) {
      setError('Please sign in to view concept maps');
      setIsLoading(false);
    }
  }, [mapId, jwt, isAuthenticated]);

  const loadMap = async () => {
    if (!jwt || !mapId) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await getConceptMap(mapId, jwt);

      if (result.error) {
        setError('Failed to load concept map');
        return;
      }

      if (result.data) {
        setCurrentMap(result.data);
        toast.success('Map loaded successfully');
      } else {
        setError('Concept map not found');
      }
    } catch (error) {
      console.error('Error loading map:', error);
      setError('An error occurred while loading the map');
    } finally {
      setIsLoading(false);
    }
  };

  const handleShare = async () => {
    try {
      await navigator.share({
        title: currentMap?.source_filename || 'Concept Map',
        text: 'Check out this interactive concept map',
        url: window.location.href,
      });
    } catch (error) {
      // Fallback to clipboard
      await navigator.clipboard.writeText(window.location.href);
      toast.success('Link copied to clipboard');
    }
  };

  const handleDownload = () => {
    // TODO: Implement download functionality
    toast.info('Download feature coming soon');
  };

  const handleGoHome = () => {
    // Clear current map and navigate home
    setCurrentMap(null);
    setSelectedNode(null);
    setDetailPanelOpen(false);
    router.push('/');
  };

  if (isLoading) {
    return (
      <div className="h-screen flex flex-col bg-background">
        {/* Header Skeleton */}
        <div className="border-b border-border p-4">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div className="flex items-center space-x-4">
              <Skeleton className="h-10 w-10 rounded-lg" />
              <div className="space-y-2">
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-4 w-32" />
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Skeleton className="h-10 w-20" />
              <Skeleton className="h-10 w-20" />
            </div>
          </div>
        </div>

        {/* Map Skeleton */}
        <div className="flex-1 p-4">
          <div className="h-full max-w-7xl mx-auto">
            <Skeleton className="h-full w-full rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <Card className="p-8 max-w-md mx-4 text-center">
          <div className="w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="h-8 w-8 text-destructive" />
          </div>
          <h2 className="text-xl font-semibold text-foreground mb-2">
            Unable to Load Map
          </h2>
          <p className="text-muted-foreground mb-6">
            {error}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button onClick={handleGoHome} variant="default">
              <Home className="mr-2 h-4 w-4" />
              Go Home
            </Button>
            <Button onClick={loadMap} variant="outline">
              Try Again
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (!currentMap) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <Card className="p-8 max-w-md mx-4 text-center">
          <h2 className="text-xl font-semibold text-foreground mb-2">
            Map Not Found
          </h2>
          <p className="text-muted-foreground mb-6">
            The concept map you're looking for doesn't exist or has been removed.
          </p>
          <Button onClick={handleGoHome} variant="default">
            <Home className="mr-2 h-4 w-4" />
            Go Home
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="border-b border-border bg-background/95 backdrop-blur-sm">
        <div className="flex items-center justify-between h-16 px-4 max-w-7xl mx-auto">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleGoHome}
              className="touch-target"
              aria-label="Go back to home"
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
            {!isMobile && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleShare}
                  className="touch-target"
                >
                  <Share2 className="mr-2 h-4 w-4" />
                  Share
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownload}
                  className="touch-target"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Export
                </Button>

                <Button
                  variant={isChatSidebarOpen ? "default" : "outline"}
                  size="sm"
                  onClick={() => setChatSidebarOpen(!isChatSidebarOpen)}
                  className="touch-target"
                >
                  <MessageCircle className="mr-2 h-4 w-4" />
                  Chat
                </Button>
              </>
            )}

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="touch-target"
                  aria-label="More options"
                >
                  <MoreHorizontal className="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                {isMobile && (
                  <>
                    <DropdownMenuItem onClick={handleShare}>
                      <Share2 className="mr-2 h-4 w-4" />
                      Share Map
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={handleDownload}>
                      <Download className="mr-2 h-4 w-4" />
                      Export Map
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setChatSidebarOpen(!isChatSidebarOpen)}>
                      <MessageCircle className="mr-2 h-4 w-4" />
                      {isChatSidebarOpen ? 'Close Chat' : 'Open Chat'}
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                  </>
                )}
                <DropdownMenuItem asChild>
                  <Link href="/">
                    <Home className="mr-2 h-4 w-4" />
                    Go to Home
                  </Link>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden flex">
        <div className="flex-1 max-w-7xl mx-auto p-4">
          <ConceptMapDisplay />
        </div>

        {/* Chat Sidebar */}
        <ChatSidebar />
      </main>

      {/* Node Detail Panel */}
      <NodeDetailPanel />
    </div>
  );
}