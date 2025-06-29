'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  FileText,
  LogOut,
  X,
  User,
  Settings,
  Clock,
  Layers,
  ExternalLink
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { getMapHistory } from '@/lib/api';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { ThemeToggle } from '@/components/ThemeToggle';
import Link from 'next/link';

export function HistorySidebar() {
  const router = useRouter();
  const {
    user,
    jwt,
    isAuthenticated,
    mapHistory,
    isSidebarCollapsed,
    currentMap,
    setMapHistory,
    setSidebarCollapsed,
    setCurrentMap,
    logout,
  } = useAppStore();

  const [isLoading, setIsLoading] = useState(false);
  const [hoveredMapId, setHoveredMapId] = useState<string | null>(null);
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
    if (isAuthenticated && jwt) {
      loadHistory();
    }
  }, [isAuthenticated, jwt]);

  const loadHistory = async () => {
    if (!jwt) return;

    setIsLoading(true);
    try {
      const result = await getMapHistory(jwt);
      if (result.data) {
        setMapHistory(result.data.history);
      } else {
        toast.error('Failed to load map history');
      }
    } catch (error) {
      toast.error('Failed to load map history');
    } finally {
      setIsLoading(false);
    }
  };

  const handleMapClick = (mapId: string) => {
    router.push(`/maps/${mapId}`);
    if (isMobile) {
      setSidebarCollapsed(true);
    }
  };

  const handleNewMap = () => {
    setCurrentMap(null);
    router.push('/');
    if (isMobile) {
      setSidebarCollapsed(true);
    }
  };

  const handleLogout = () => {
    logout();
    toast.success('Signed out successfully');
    router.push('/');
    if (isMobile) {
      setSidebarCollapsed(true);
    }
  };

  const handleCloseMobile = () => {
    if (isMobile) {
      setSidebarCollapsed(true);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.abs(now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 168) { // 7 days
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const getUserInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  // Show recent maps (last 4)
  const recentMaps = mapHistory.slice(0, 4);

  return (
    <div
      className={cn(
        'h-full bg-background border-r border-border transition-all duration-300 flex flex-col',
        'shadow-sm',
        isMobile ? 'w-full' : (isSidebarCollapsed ? 'w-16' : 'w-80')
      )}
    >
      {/* Header */}
      <div className="spacing-mobile-sm border-b border-border bg-background/95 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          {(!isSidebarCollapsed || isMobile) && (
            <Link href="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Layers className="h-5 w-5 text-primary-foreground" />
              </div>
              <div>
                <h2 className="text-responsive-lg font-semibold text-foreground">
                  Knowledge Maps
                </h2>
                <p className="text-responsive-xs text-muted-foreground">
                  Interactive concept mapping
                </p>
              </div>
            </Link>
          )}

          <div className="flex items-center space-x-2 ml-auto">
            {/* Mobile close button */}
            {isMobile && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleCloseMobile}
                className="touch-target"
                aria-label="Close sidebar"
              >
                <X className="h-5 w-5" />
              </Button>
            )}

            {/* Desktop collapse toggle */}
            {!isMobile && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarCollapsed(!isSidebarCollapsed)}
                className="touch-target hover:bg-accent transition-colors"
                aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              >
                {isSidebarCollapsed ? (
                  <ChevronRight className="h-4 w-4" />
                ) : (
                  <ChevronLeft className="h-4 w-4" />
                )}
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Collapsed state - show only icons */}
      {!isMobile && isSidebarCollapsed && (
        <div className="flex-1 flex flex-col items-center py-4 space-y-4">
          <Button
            onClick={handleNewMap}
            size="icon"
            variant="default"
            className="touch-target bg-primary text-primary-foreground hover:bg-primary/90"
            aria-label="Create new map"
          >
            <Plus className="h-5 w-5" />
          </Button>

          {isAuthenticated && user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="touch-target"
                  aria-label="Account menu"
                >
                  <Avatar className="h-8 w-8">
                    <AvatarImage src={user.picture} alt={user.name} />
                    <AvatarFallback className="text-xs">
                      {getUserInitials(user.name)}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" side="right" className="w-56">
                <div className="px-2 py-1.5">
                  <p className="text-sm font-medium">{user.name}</p>
                  <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                </div>
                <DropdownMenuSeparator />
                <div className="px-2 py-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Theme</span>
                    <ThemeToggle size="sm" />
                  </div>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-destructive">
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      )}

      {/* Expanded state content */}
      {(!isSidebarCollapsed || isMobile) && (
        <>
          {/* Quick Actions */}
          <div className="spacing-mobile-sm">
            <Button
              onClick={handleNewMap}
              className={cn(
                "w-full touch-target text-responsive-sm justify-start",
                "bg-primary text-primary-foreground hover:bg-primary/90",
                "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              )}
              variant="default"
            >
              <Plus className="mr-2 h-4 w-4" />
              Create New Map
            </Button>
          </div>

          <Separator />

          {/* Content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {!isAuthenticated ? (
              <div className="spacing-mobile text-center text-muted-foreground">
                <div className="w-16 h-16 mx-auto mb-4 bg-muted/30 rounded-full flex items-center justify-center">
                  <FileText className="h-8 w-8 opacity-50" />
                </div>
                <h3 className="text-responsive-sm font-medium mb-2">Welcome!</h3>
                <p className="text-responsive-xs">Sign in to see your map history and create interactive concept maps</p>
              </div>
            ) : (
              <>
                {/* Recent Maps Section */}
                <div className="flex-1 overflow-hidden flex flex-col">
                  <div className="spacing-mobile-sm pb-2">
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <h3 className="text-responsive-sm font-medium text-foreground">
                        Recent Maps
                      </h3>
                    </div>
                  </div>

                  <ScrollArea className="flex-1 px-4">
                    {isLoading ? (
                      <div className="space-y-3">
                        {[...Array(4)].map((_, i) => (
                          <Card key={i} className="p-4">
                            <div className="flex items-start space-x-3">
                              <Skeleton className="h-10 w-10 rounded-lg flex-shrink-0" />
                              <div className="flex-1 space-y-2">
                                <Skeleton className="h-4 w-full" />
                                <Skeleton className="h-3 w-20" />
                              </div>
                            </div>
                          </Card>
                        ))}
                      </div>
                    ) : recentMaps.length === 0 ? (
                      <div className="text-center text-muted-foreground py-8">
                        <div className="w-16 h-16 mx-auto mb-4 bg-muted/30 rounded-full flex items-center justify-center">
                          <FileText className="h-8 w-8 opacity-50" />
                        </div>
                        <h4 className="text-responsive-sm font-medium mb-2">No maps yet</h4>
                        <p className="text-responsive-xs">Upload a PDF to create your first interactive concept map</p>
                      </div>
                    ) : (
                      <div className="space-y-3 pb-4">
                        {recentMaps.map((item, index) => (
                          <div key={item.map_id} className="relative group">
                            <Card
                              className={cn(
                                'p-4 cursor-pointer transition-all duration-200 touch-target group',
                                'focus-visible-ring hover:shadow-md hover:scale-[1.02]',
                                currentMap?.mongodb_doc_id === item.map_id
                                  ? 'bg-primary/5 border-primary/20 shadow-sm'
                                  : 'hover:bg-accent/50 border-border',
                                hoveredMapId === item.map_id && 'shadow-lg'
                              )}
                              onClick={() => handleMapClick(item.map_id)}
                              onMouseEnter={() => setHoveredMapId(item.map_id)}
                              onMouseLeave={() => setHoveredMapId(null)}
                              role="button"
                              tabIndex={0}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                  e.preventDefault();
                                  handleMapClick(item.map_id);
                                }
                              }}
                              aria-label={`Open map: ${item.source_filename}`}
                            >
                              <div className="flex items-start space-x-3">
                                <div className={cn(
                                  'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors',
                                  currentMap?.mongodb_doc_id === item.map_id
                                    ? 'bg-primary text-primary-foreground'
                                    : 'bg-muted group-hover:bg-primary/10'
                                )}>
                                  <FileText className="h-5 w-5" />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-responsive-sm font-medium text-foreground truncate group-hover:text-primary transition-colors">
                                    {item.source_filename.replace('.pdf', '')}
                                  </p>
                                  <div className="flex items-center space-x-2 mt-1">
                                    <p className="text-responsive-xs text-muted-foreground">
                                      {formatDate(item.created_at)}
                                    </p>
                                    {index === 0 && (
                                      <span className="text-responsive-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                                        Latest
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </Card>

                            {/* Open in New Tab Button */}
                            <Button
                              variant="secondary"
                              size="icon"
                              className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 shadow-sm h-7 w-7"
                              onClick={(e) => {
                                e.stopPropagation();
                                window.open(`/maps/${item.map_id}`, '_blank');
                              }}
                              title="Open in new tab"
                            >
                              <ExternalLink className="h-3 w-3" />
                            </Button>
                          </div>
                        ))}

                        {mapHistory.length > 4 && (
                          <Button
                            variant="ghost"
                            className="w-full text-responsive-xs text-muted-foreground hover:text-foreground"
                            onClick={() => {
                              // TODO: Implement full history view
                              toast.info('Full history view coming soon');
                            }}
                          >
                            View all {mapHistory.length} maps
                          </Button>
                        )}
                      </div>
                    )}
                  </ScrollArea>
                </div>

                <Separator />

                {/* Footer - Account Menu */}
                {user && (
                  <div className="spacing-mobile-sm">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          className="w-full justify-start touch-target hover:bg-accent transition-colors"
                        >
                          <div className="flex items-center space-x-3 w-full">
                            <Avatar className="h-8 w-8 flex-shrink-0">
                              <AvatarImage src={user.picture} alt={user.name} />
                              <AvatarFallback className="text-xs">
                                {getUserInitials(user.name)}
                              </AvatarFallback>
                            </Avatar>
                            <div className="flex-1 min-w-0 text-left">
                              <p className="text-responsive-sm font-medium text-foreground truncate">
                                {user.name}
                              </p>
                              <p className="text-responsive-xs text-muted-foreground truncate">
                                Account settings
                              </p>
                            </div>
                            <Settings className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                          </div>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" side="top" className="w-64 mb-2">
                        <div className="px-3 py-2">
                          <div className="flex items-center space-x-3">
                            <Avatar className="h-10 w-10">
                              <AvatarImage src={user.picture} alt={user.name} />
                              <AvatarFallback>
                                {getUserInitials(user.name)}
                              </AvatarFallback>
                            </Avatar>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium truncate">{user.name}</p>
                              <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                            </div>
                          </div>
                        </div>
                        <DropdownMenuSeparator />
                        <div className="px-3 py-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Theme</span>
                            <ThemeToggle size="sm" />
                          </div>
                        </div>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={handleLogout} className="text-destructive">
                          <LogOut className="mr-2 h-4 w-4" />
                          Sign Out
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                )}
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}