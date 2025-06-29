'use client';

import { usePathname } from 'next/navigation';
import { HistorySidebar } from '@/components/HistorySidebar';
import { MobileHeader } from '@/components/MobileHeader';
import { useAppStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';

interface AppLayoutWrapperProps {
  children: React.ReactNode;
}

export function AppLayoutWrapper({ children }: AppLayoutWrapperProps) {
  const pathname = usePathname();
  const { isSidebarCollapsed } = useAppStore();
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Check if we're on a map page
  const isMapPage = pathname?.startsWith('/maps/');
  
  // For map pages, don't show the sidebar layout
  if (isMapPage) {
    return <>{children}</>;
  }

  // For home page and other pages, show the sidebar layout
  return (
    <div className="h-screen flex flex-col md:flex-row bg-background overflow-hidden">
      {/* Mobile Header */}
      {isMobile && <MobileHeader />}
      
      {/* Sidebar - Hidden on mobile by default */}
      <div className={cn(
        'transition-all duration-300 ease-in-out',
        isMobile ? (
          isSidebarCollapsed 
            ? 'hidden' 
            : 'fixed inset-0 z-50 bg-background'
        ) : (
          isSidebarCollapsed ? 'w-16' : 'w-80'
        )
      )}>
        <HistorySidebar />
      </div>
      
      {/* Main Content */}
      <div className={cn(
        'flex-1 transition-all duration-300 ease-in-out overflow-hidden',
        'flex flex-col',
        !isMobile && (isSidebarCollapsed ? 'ml-0' : 'ml-0')
      )}>
        {children}
      </div>
    </div>
  );
}