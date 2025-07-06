import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: string;
  email: string;
  name: string;
  picture: string;
}

export interface AttachmentInfo {
  filename: string;
  s3_path?: string;
  status: string;
  error_message?: string;
}

export interface MapHistoryItem {
  map_id: string;
  title: string;
  original_filename: string;
  created_at: string;
  attachments?: AttachmentInfo[];
}

// Legacy ReactFlow interfaces removed - using only hierarchical mind maps

export interface HierarchicalNode {
  id: string;
  data: { label: string };
  children: HierarchicalNode[];
}

export interface HierarchicalMindMap {
  mongodb_doc_id: string;
  hierarchical_data: HierarchicalNode;
  title: string;
  original_filename?: string;
}

interface AppState {
  // Authentication
  user: User | null;
  jwt: string | null;
  isAuthenticated: boolean;

  // Legacy map history - kept for backward compatibility during transition
  mapHistory: MapHistoryItem[];

  // NEW: Hierarchical Mind Maps
  currentMindMap: HierarchicalMindMap | null;
  mindMapHistory: Array<{
    id: string;
    title: string;
    original_filename: string;
    created_at: string;
  }>;

  // UI State
  selectedNodeData: HierarchicalNode | null;
  isDetailPanelOpen: boolean;
  isSidebarCollapsed: boolean;
  isLoading: boolean;
  uploadProgress: number;

  // Actions
  setUser: (user: User | null) => void;
  setJWT: (jwt: string | null) => void;
  setCurrentMindMap: (mindMap: HierarchicalMindMap | null) => void;
  setMapHistory: (history: MapHistoryItem[]) => void;
  addToHistory: (item: MapHistoryItem) => void;
  setSelectedNodeData: (nodeData: HierarchicalNode | null) => void;
  setDetailPanelOpen: (open: boolean) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setLoading: (loading: boolean) => void;
  setUploadProgress: (progress: number) => void;
  logout: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      jwt: null,
      isAuthenticated: false,
      mapHistory: [],
      currentMindMap: null,
      mindMapHistory: [],
      selectedNodeData: null,
      isDetailPanelOpen: false,
      isSidebarCollapsed: false,
      isLoading: false,
      uploadProgress: 0,

      // Actions
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setJWT: (jwt) => set({ jwt }),
      setCurrentMindMap: (mindMap) => set({ currentMindMap: mindMap }),
      setMapHistory: (history) => set({ mapHistory: history }),
      addToHistory: (item) => set({ mapHistory: [item, ...get().mapHistory] }),
      setSelectedNodeData: (nodeData) => {
        console.log('🏪 setSelectedNodeData called with:', nodeData);
        set({ selectedNodeData: nodeData });
      },
      setDetailPanelOpen: (open) => {
        console.log('🏪 setDetailPanelOpen called with:', open);
        set({ isDetailPanelOpen: open });
      },
      setSidebarCollapsed: (collapsed) => set({ isSidebarCollapsed: collapsed }),
      setLoading: (loading) => set({ isLoading: loading }),
      setUploadProgress: (progress) => set({ uploadProgress: progress }),
      logout: () => set({
        user: null,
        jwt: null,
        isAuthenticated: false,
        currentMindMap: null,
        selectedNodeData: null,
        isDetailPanelOpen: false
      }),
    }),
    {
      name: 'knowledge-platform-storage',
      partialize: (state) => ({
        user: state.user,
        jwt: state.jwt,
        isAuthenticated: state.isAuthenticated,
        mapHistory: state.mapHistory,
        isSidebarCollapsed: state.isSidebarCollapsed,
      }),
    }
  )
);