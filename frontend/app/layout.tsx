import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { GoogleAuthProvider } from '@/components/GoogleAuthProvider';
import { ThemeProvider } from '@/components/ThemeProvider';
import { Toaster } from '@/components/ui/sonner';
import { HistorySidebar } from '@/components/HistorySidebar';
import { MobileHeader } from '@/components/MobileHeader';
import { AppLayoutWrapper } from '@/components/AppLayoutWrapper';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'VizMind AI - Transform Documents into Intelligent Mind Maps',
  description: 'Transform your PDF documents into interactive hierarchical mind maps with AI-powered insights and intelligent Q&A',
  keywords: ['PDF', 'mind maps', 'AI', 'VizMind AI', 'interactive', 'document analysis', 'RAG', 'LangGraph'],
  authors: [{ name: 'VizMind AI Team' }],
  creator: 'VizMind AI',
  publisher: 'VizMind AI',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL('https://vizmind-ai.com'),
  openGraph: {
    title: 'VizMind AI - Transform Documents into Intelligent Mind Maps',
    description: 'Transform your PDF documents into interactive hierarchical mind maps with AI-powered insights and intelligent Q&A',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'VizMind AI - Transform Documents into Intelligent Mind Maps',
    description: 'Transform your PDF documents into interactive hierarchical mind maps with AI-powered insights and intelligent Q&A',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#0a0a0a' },
  ],
  colorScheme: 'light dark',
  viewportFit: 'cover',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning className={inter.variable}>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const stored = localStorage.getItem('theme-storage');
                const theme = stored ? JSON.parse(stored).state?.theme || 'system' : 'system';
                const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                const isDark = theme === 'dark' || (theme === 'system' && systemDark);
                
                document.documentElement.classList.add(isDark ? 'dark' : 'light');
                document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
              } catch (e) {
                document.documentElement.classList.add('light');
                document.documentElement.setAttribute('data-theme', 'light');
              }
            `,
          }}
        />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className={`${inter.className} font-sans antialiased safe-area-top safe-area-bottom`}>
        <ThemeProvider>
          <GoogleAuthProvider>
            <AppLayoutWrapper>
              {children}
            </AppLayoutWrapper>
            <Toaster
              richColors
              position="top-center"
              toastOptions={{
                className: 'text-responsive-sm',
                style: {
                  minHeight: '44px',
                },
              }}
            />
          </GoogleAuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}