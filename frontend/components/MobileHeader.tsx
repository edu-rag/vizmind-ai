'use client';

import { Button } from '@/components/ui/button';
import { Menu, X, Sparkles } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { ThemeToggle } from '@/components/ThemeToggle';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

export function MobileHeader() {
  const { isSidebarCollapsed, setSidebarCollapsed } = useAppStore();

  return (
    <motion.header
      className="md:hidden bg-background/80 backdrop-blur-lg border-b border-border safe-area-top sticky top-0 z-40"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: 'spring' as const, stiffness: 300, damping: 30 }}
    >
      <div className="flex items-center justify-between h-14 px-4">
        <div className="flex items-center space-x-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarCollapsed(!isSidebarCollapsed)}
            className="touch-target"
            aria-label={isSidebarCollapsed ? 'Open menu' : 'Close menu'}
          >
            <AnimatePresence mode="wait">
              {isSidebarCollapsed ? (
                <motion.div
                  key="menu"
                  initial={{ rotate: -90, opacity: 0 }}
                  animate={{ rotate: 0, opacity: 1 }}
                  exit={{ rotate: 90, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <Menu className="h-5 w-5" />
                </motion.div>
              ) : (
                <motion.div
                  key="close"
                  initial={{ rotate: 90, opacity: 0 }}
                  animate={{ rotate: 0, opacity: 1 }}
                  exit={{ rotate: -90, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <X className="h-5 w-5" />
                </motion.div>
              )}
            </AnimatePresence>
          </Button>

          <div className="flex items-center gap-2">
            <motion.div
              className="w-8 h-8 gradient-ai rounded-lg flex items-center justify-center"
              animate={{ rotate: [0, 5, -5, 0] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
            >
              <Sparkles className="h-4 w-4 text-white" />
            </motion.div>
            <h1 className="text-responsive-lg font-bold gradient-text truncate">
              VizMind AI
            </h1>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <ThemeToggle size="icon" className="touch-target" />
        </div>
      </div>
    </motion.header>
  );
}