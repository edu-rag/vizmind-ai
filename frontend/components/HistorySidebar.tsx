'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
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
  ExternalLink,
  Search,
  Filter,
  Calendar,
  SortAsc,
  SortDesc,
  Brain,
  Sparkles,
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { getMapHistory, getHierarchicalMindMap } from '@/lib/api';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { ThemeToggle } from '@/components/ThemeToggle';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';

type SortOption = 'newest' | 'oldest' | 'name-asc' | 'name-desc';

export function HistorySidebar() {
  const router = useRouter();
  const {
    user,
    jwt,
    isAuthenticated,
    mapHistory,
    isSidebarCollapsed,
    currentMindMap,
    setMapHistory,
    setSidebarCollapsed,
    setCurrentMindMap,
    logout,
  } = useAppStore();

  const [isLoading, setIsLoading] = useState(false);
  const [hoveredMapId, setHoveredMapId] = useState<string | null>(null);
  const [isMobile, setIsMobile] = useState(false);
  const [displayedMaps, setDisplayedMaps] = useState(8);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [showSortMenu, setShowSortMenu] = useState(false);

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

  const handleMapClick = async (mapId: string) => {
    if (!jwt) return;

    try {
      const result = await getHierarchicalMindMap(mapId, jwt);

      if (result.data) {
        setCurrentMindMap(result.data);
        router.push('/');
        toast.success('Mind map loaded successfully');
      } else {
        toast.error('Failed to load hierarchical mind map');
      }
    } catch (error) {
      console.error('Error loading mind map:', error);
      toast.error('Failed to load hierarchical mind map');
    }

    if (isMobile) {
      setSidebarCollapsed(true);
    }
  };

  const handleNewMap = () => {
    setCurrentMindMap(null);
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
    // Parse the UTC timestamp from the API (format: "2025-10-08T17:33:49.109000")
    // The API returns UTC time without 'Z' suffix, so we need to add it for proper parsing
    const utcDateString = dateString.endsWith('Z') ? dateString : `${dateString}Z`;
    const date = new Date(utcDateString);

    const now = new Date();
    const diffInHours = Math.abs(now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
    } else if (diffInHours < 168) {
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

  // Filter and sort maps
  const filteredAndSortedMaps = mapHistory
    .filter(map => {
      if (!searchQuery) return true;
      return map.original_filename.toLowerCase().includes(searchQuery.toLowerCase());
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'oldest':
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case 'name-asc':
          return a.original_filename.localeCompare(b.original_filename);
        case 'name-desc':
          return b.original_filename.localeCompare(a.original_filename);
        default:
          return 0;
      }
    });

  const visibleMaps = filteredAndSortedMaps.slice(0, displayedMaps);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;

    if (scrollPercentage > 0.8 && !isLoadingMore && displayedMaps < filteredAndSortedMaps.length) {
      setIsLoadingMore(true);
      setTimeout(() => {
        setDisplayedMaps(prev => Math.min(prev + 6, filteredAndSortedMaps.length));
        setIsLoadingMore(false);
      }, 300);
    }
  };

  useEffect(() => {
    setDisplayedMaps(8);
  }, [mapHistory, searchQuery, sortBy]);

  return (
    <motion.div
      className={cn(
        'h-full bg-background border-r border-border flex flex-col shadow-lg',
        isMobile ? 'w-full' : (isSidebarCollapsed ? 'w-16' : 'w-80')
      )}
      initial={false}
      animate={{
        width: isMobile ? '100%' : (isSidebarCollapsed ? '4rem' : '20rem')
      }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
    >
      {/* Header */}
      <div className="p-4 border-b border-border glass">
        <div className="flex items-center justify-between">
          {(!isSidebarCollapsed || isMobile) && (
            <Link href="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <motion.div
                className="w-8 h-8 gradient-ai rounded-lg flex items-center justify-center"
                whileHover={{ scale: 1.1, rotate: 5 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <Brain className="h-5 w-5 text-white" />
              </motion.div>
              <div>
                <h2 className="text-sm font-bold text-foreground">VizMind AI</h2>
                <p className="text-xs text-muted-foreground">Intelligent mapping</p>
              </div>
            </Link>
          )}

          <div className="flex items-center space-x-2">
            {!isMobile && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarCollapsed(!isSidebarCollapsed)}
                className="h-8 w-8"
                aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              >
                {isSidebarCollapsed ? (
                  <ChevronRight className="h-4 w-4" />
                ) : (
                  <ChevronLeft className="h-4 w-4" />
                )}
              </Button>
            )}

            {isMobile && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleCloseMobile}
                className="h-8 w-8"
                aria-label="Close sidebar"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Collapsed View */}
      {isSidebarCollapsed && !isMobile ? (
        <div className="flex flex-col items-center space-y-4 py-4">
          <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleNewMap}
              className="h-10 w-10 gradient-ai text-white"
              aria-label="Create new map"
            >
              <Plus className="h-5 w-5" />
            </Button>
          </motion.div>

          <Separator />

          <div className="flex-1 overflow-y-auto space-y-2">
            {visibleMaps.slice(0, 5).map((item) => (
              <motion.div
                key={item.map_id}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                <Button
                  variant={currentMindMap?.mongodb_doc_id === item.map_id ? 'default' : 'ghost'}
                  size="icon"
                  onClick={() => handleMapClick(item.map_id)}
                  className="h-10 w-10"
                  aria-label={item.original_filename}
                >
                  <FileText className="h-5 w-5" />
                </Button>
              </motion.div>
            ))}
          </div>

          {isAuthenticated && user && (
            <>
              <Separator />
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-10 w-10">
                    <Avatar className="h-8 w-8">
                      {user.picture ? (
                        <AvatarImage src={user.picture} alt={user.name || 'User'} />
                      ) : null}
                      <AvatarFallback className="text-xs gradient-ai text-white">
                        {user.name ? getUserInitials(user.name) : 'U'}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <DropdownMenuItem onClick={handleLogout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          )}
        </div>
      ) : (
        <>
          {/* New Map Button */}
          <div className="p-4">
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Button
                onClick={handleNewMap}
                className="w-full gradient-ai text-white shadow-lg hover:opacity-90"
                size="lg"
              >
                <Plus className="mr-2 h-5 w-5" />
                Create New Map
              </Button>
            </motion.div>
          </div>

          {/* Search and Sort */}
          {isAuthenticated && mapHistory.length > 0 && (
            <div className="px-4 pb-4 space-y-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Search maps..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 pr-4 h-10 bg-muted/50"
                />
              </div>

              <div className="flex items-center gap-2">
                <DropdownMenu open={showSortMenu} onOpenChange={setShowSortMenu}>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" className="flex-1 justify-start">
                      {sortBy === 'newest' && <Clock className="mr-2 h-4 w-4" />}
                      {sortBy === 'oldest' && <Calendar className="mr-2 h-4 w-4" />}
                      {sortBy === 'name-asc' && <SortAsc className="mr-2 h-4 w-4" />}
                      {sortBy === 'name-desc' && <SortDesc className="mr-2 h-4 w-4" />}
                      <span className="text-xs">
                        {sortBy === 'newest' && 'Newest First'}
                        {sortBy === 'oldest' && 'Oldest First'}
                        {sortBy === 'name-asc' && 'Name (A-Z)'}
                        {sortBy === 'name-desc' && 'Name (Z-A)'}
                      </span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-48">
                    <DropdownMenuItem onClick={() => setSortBy('newest')}>
                      <Clock className="mr-2 h-4 w-4" />
                      Newest First
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setSortBy('oldest')}>
                      <Calendar className="mr-2 h-4 w-4" />
                      Oldest First
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => setSortBy('name-asc')}>
                      <SortAsc className="mr-2 h-4 w-4" />
                      Name (A-Z)
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setSortBy('name-desc')}>
                      <SortDesc className="mr-2 h-4 w-4" />
                      Name (Z-A)
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>

                <Badge variant="secondary" className="text-xs px-2 py-1">
                  {filteredAndSortedMaps.length}
                </Badge>
              </div>
            </div>
          )}

          {/* Maps List */}
          <div className="flex-1 overflow-hidden">
            {!isAuthenticated ? (
              <div className="p-4 text-center space-y-4">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                  className="gradient-ai-subtle rounded-xl p-6"
                >
                  <Sparkles className="h-12 w-12 mx-auto mb-3 text-primary" />
                  <h3 className="font-semibold text-foreground mb-2">Sign in to continue</h3>
                  <p className="text-sm text-muted-foreground">
                    Create and save your mind maps with AI-powered insights
                  </p>
                </motion.div>
              </div>
            ) : isLoading ? (
              <div className="p-4 space-y-3">
                {[1, 2, 3, 4].map((i) => (
                  <Card key={i} className="p-3">
                    <Skeleton className="h-4 w-3/4 mb-2" />
                    <Skeleton className="h-3 w-1/2" />
                  </Card>
                ))}
              </div>
            ) : visibleMaps.length === 0 ? (
              <div className="p-4 text-center space-y-4">
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5 }}
                >
                  <FileText className="h-12 w-12 mx-auto text-muted-foreground opacity-50 mb-3" />
                  <p className="text-sm text-muted-foreground">
                    {searchQuery ? 'No maps match your search' : 'No mind maps yet'}
                  </p>
                  {!searchQuery && (
                    <p className="text-xs text-muted-foreground mt-1">
                      Upload a PDF to get started
                    </p>
                  )}
                </motion.div>
              </div>
            ) : (
              <ScrollArea className="h-full" onScroll={handleScroll}>
                <div className="p-4 space-y-2">
                  <AnimatePresence>
                    {visibleMaps.map((item, index) => (
                      <motion.div
                        key={item.map_id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ duration: 0.2, delay: index * 0.03 }}
                        onMouseEnter={() => setHoveredMapId(item.map_id)}
                        onMouseLeave={() => setHoveredMapId(null)}
                      >
                        <Card
                          className={cn(
                            'group relative overflow-hidden cursor-pointer transition-all duration-200',
                            'hover:shadow-lg hover:border-primary/50',
                            currentMindMap?.mongodb_doc_id === item.map_id &&
                            'border-primary/70 bg-primary/5'
                          )}
                          onClick={() => handleMapClick(item.map_id)}
                        >
                          {/* Gradient overlay on hover */}
                          <div className="absolute inset-0 gradient-ai-subtle opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                          <div className="relative p-3 space-y-2">
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <div className="w-8 h-8 rounded-lg gradient-ai-subtle flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                                    <FileText className="h-4 w-4 text-primary" />
                                  </div>
                                  <Badge variant="secondary" className="text-xs">
                                    PDF
                                  </Badge>
                                </div>
                                <h4 className="text-sm font-medium text-foreground line-clamp-2 mb-1 group-hover:text-primary transition-colors">
                                  {item.original_filename.replace('.pdf', '')}
                                </h4>
                                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                  <Clock className="h-3 w-3" />
                                  {formatDate(item.created_at)}
                                </div>
                              </div>

                              <AnimatePresence>
                                {hoveredMapId === item.map_id && (
                                  <motion.div
                                    initial={{ opacity: 0, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.8 }}
                                    transition={{ duration: 0.15 }}
                                  >
                                    <Button
                                      variant="secondary"
                                      size="icon"
                                      className="h-8 w-8 shadow-lg"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        window.open(`/maps/${item.map_id}`, '_blank');
                                      }}
                                      aria-label="Open in new tab"
                                    >
                                      <ExternalLink className="h-4 w-4" />
                                    </Button>
                                  </motion.div>
                                )}
                              </AnimatePresence>
                            </div>
                          </div>
                        </Card>
                      </motion.div>
                    ))}
                  </AnimatePresence>

                  {isLoadingMore && (
                    <div className="py-4 text-center">
                      <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                    </div>
                  )}

                  {displayedMaps < filteredAndSortedMaps.length && !isLoadingMore && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="pt-2"
                    >
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={() => setDisplayedMaps(prev => Math.min(prev + 6, filteredAndSortedMaps.length))}
                      >
                        Load More ({filteredAndSortedMaps.length - displayedMaps} remaining)
                      </Button>
                    </motion.div>
                  )}
                </div>
              </ScrollArea>
            )}
          </div>

          {/* Footer with User Profile */}
          {isAuthenticated && user && (
            <div className="p-4 border-t border-border glass">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <Avatar className="h-9 w-9 ring-2 ring-primary/20">
                    {user.picture ? (
                      <AvatarImage src={user.picture} alt={user.name || 'User'} />
                    ) : null}
                    <AvatarFallback className="text-xs gradient-ai text-white">
                      {user.name ? getUserInitials(user.name) : 'U'}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {user.name || 'User'}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">
                      {user.email}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-1">
                  <ThemeToggle />
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48">
                      <DropdownMenuItem>
                        <User className="mr-2 h-4 w-4" />
                        Account Settings
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={handleLogout} className="text-destructive">
                        <LogOut className="mr-2 h-4 w-4" />
                        Sign Out
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </motion.div>
  );
}
