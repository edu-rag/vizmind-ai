'use client';

import { useEffect } from 'react';
import { useThemeStore } from '@/lib/theme-store';

interface ThemeProviderProps {
  children: React.ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const { theme, setTheme } = useThemeStore();

  useEffect(() => {
    // Initialize theme on mount
    const initializeTheme = () => {
      const storedTheme = localStorage.getItem('theme-storage');
      let initialTheme = 'system';
      
      if (storedTheme) {
        try {
          const parsed = JSON.parse(storedTheme);
          initialTheme = parsed.state?.theme || 'system';
        } catch (error) {
          console.error('Error parsing stored theme:', error);
        }
      }
      
      setTheme(initialTheme as any);
    };

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      if (theme === 'system') {
        setTheme('system');
      }
    };

    initializeTheme();
    mediaQuery.addEventListener('change', handleChange);

    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme, setTheme]);

  return <>{children}</>;
}