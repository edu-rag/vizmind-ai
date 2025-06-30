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
  source_filename: string;
  created_at: string;
  attachments?: AttachmentInfo[];
}

export interface ReactFlowData {
  nodes: Array<{
    id: string;
    data: { label: string };
    position: { x: number; y: number };
    type?: string;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    type?: string;
    label?: string;
  }>;
}

export interface ConceptMap {
  mongodb_doc_id: string;
  react_flow_data: ReactFlowData;
  source_filename?: string;
}

interface AppState {
  // Authentication
  user: User | null;
  jwt: string | null;
  isAuthenticated: boolean;

  // Maps
  currentMap: ConceptMap | null;
  mapHistory: MapHistoryItem[];

  // UI State
  selectedNode: string | null;
  isDetailPanelOpen: boolean;
  isSidebarCollapsed: boolean;
  isChatSidebarOpen: boolean;
  isLoading: boolean;
  uploadProgress: number;

  // Actions
  setUser: (user: User | null) => void;
  setJWT: (jwt: string | null) => void;
  setCurrentMap: (map: ConceptMap | null) => void;
  setMapHistory: (history: MapHistoryItem[]) => void;
  addToHistory: (item: MapHistoryItem) => void;
  setSelectedNode: (nodeId: string | null) => void;
  setDetailPanelOpen: (open: boolean) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setChatSidebarOpen: (open: boolean) => void;
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
      currentMap: null,
      mapHistory: [],
      selectedNode: null,
      isDetailPanelOpen: false,
      isSidebarCollapsed: false,
      isChatSidebarOpen: false,
      isLoading: false,
      uploadProgress: 0,

      // Actions
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setJWT: (jwt) => set({ jwt }),
      setCurrentMap: (map) => set({ currentMap: map }),
      setMapHistory: (history) => set({ mapHistory: history }),
      addToHistory: (item) => set({ mapHistory: [item, ...get().mapHistory] }),
      setSelectedNode: (nodeId) => set({ selectedNode: nodeId }),
      setDetailPanelOpen: (open) => set({ isDetailPanelOpen: open }),
      setSidebarCollapsed: (collapsed) => set({ isSidebarCollapsed: collapsed }),
      setChatSidebarOpen: (open) => set({ isChatSidebarOpen: open }),
      setLoading: (loading) => set({ isLoading: loading }),
      setUploadProgress: (progress) => set({ uploadProgress: progress }),
      logout: () => set({
        user: null,
        jwt: null,
        isAuthenticated: false,
        currentMap: null,
        selectedNode: null,
        isDetailPanelOpen: false,
        isChatSidebarOpen: false
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