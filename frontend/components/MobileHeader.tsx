'use client';

import { Button } from '@/components/ui/button';
import { Menu, X } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { ThemeToggle } from '@/components/ThemeToggle';
import { cn } from '@/lib/utils';

export function MobileHeader() {
  const { isSidebarCollapsed, setSidebarCollapsed } = useAppStore();

  return (
    <header className="md:hidden bg-background border-b border-border safe-area-top">
      <div className="flex items-center justify-between h-14 px-4">
        <div className="flex items-center space-x-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarCollapsed(!isSidebarCollapsed)}
            className="touch-target"
            aria-label={isSidebarCollapsed ? 'Open menu' : 'Close menu'}
          >
            {isSidebarCollapsed ? (
              <Menu className="h-5 w-5" />
            ) : (
              <X className="h-5 w-5" />
            )}
          </Button>
          
          <h1 className="text-responsive-lg font-semibold text-foreground truncate">
            Knowledge Platform
          </h1>
        </div>
        
        <div className="flex items-center space-x-2">
          <ThemeToggle size="icon" className="touch-target" />
        </div>
      </div>
    </header>
  );
}