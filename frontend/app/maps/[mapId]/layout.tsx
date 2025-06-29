import type { Metadata } from 'next';

interface MapLayoutProps {
  children: React.ReactNode;
  params: { mapId: string };
}

export async function generateMetadata({ params }: MapLayoutProps): Promise<Metadata> {
  const mapId = params.mapId;

  return {
    title: `Concept Map - Knowledge Platform`,
    description: 'Interactive concept map generated from PDF document',
    openGraph: {
      title: 'Interactive Concept Map',
      description: 'Explore this AI-generated concept map with interactive nodes and relationships',
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title: 'Interactive Concept Map',
      description: 'Explore this AI-generated concept map with interactive nodes and relationships',
    },
  };
}

export default function MapLayout({ children }: MapLayoutProps) {
  return children;
}