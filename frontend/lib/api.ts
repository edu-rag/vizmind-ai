const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// VizMind AI API Types
export interface AttachmentInfo {
  filename: string;
  s3_path?: string;
  status: string;
  error_message?: string;
}

export interface HierarchicalNode {
  id: string;
  data: { label: string };
  children: HierarchicalNode[];
}

export interface MindMapResponse {
  attachment: AttachmentInfo;
  status: string;
  hierarchical_data?: HierarchicalNode;
  mongodb_doc_id?: string;
  error_message?: string;
  processing_metadata?: {
    processing_time?: number;
    chunk_count?: number;
    embedding_dimension?: number;
    stage?: string;
  };
}

export interface CitationSource {
  type: string;
  identifier: string;
  title?: string;
  page_number?: number;
  snippet?: string;
}

export interface NodeDetailResponse {
  query: string;
  answer: string;
  cited_sources: CitationSource[];
  confidence_score?: number;
  processing_time?: number;
  message?: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

// Function to handle logout when token is expired
const handleTokenExpiration = () => {
  // Import the store dynamically to avoid circular dependencies
  import('@/lib/store').then(({ useAppStore }) => {
    const { logout } = useAppStore.getState();
    logout();

    // Show a toast notification using sonner
    if (typeof window !== 'undefined') {
      import('sonner').then(({ toast }) => {
        toast.error('Session expired. Please log in again.');
      });
    }

    // Redirect to home page after a short delay
    if (typeof window !== 'undefined') {
      setTimeout(() => {
        window.location.href = '/';
      }, 1000); // 1 second delay to show the toast
    }
  });
};// Helper function to make authenticated requests
const makeRequest = async <T>(
  url: string,
  options: RequestInit = {},
  jwt?: string | null
): Promise<ApiResponse<T>> => {
  try {
    // Ensure headers is always a plain object to allow property assignment
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers ? (options.headers as Record<string, string>) : {}),
    };

    if (jwt) {
      headers['Authorization'] = `Bearer ${jwt}`;
    }

    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
    });

    // Check for 401 Unauthorized response (token expired)
    if (response.status === 401) {
      console.warn('Token expired or invalid. Logging out user.');
      handleTokenExpiration();
      return { error: 'Authentication expired. Please log in again.' };
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    console.error('API request failed:', error);
    return { error: error instanceof Error ? error.message : 'Unknown error' };
  }
};

// Authentication
export const authenticateWithGoogle = async (googleIdToken: string) => {
  return makeRequest<{
    access_token: string;
    user_info: {
      id: string;
      email: string;
      name: string;
      picture: string;
    };
  }>('/api/v1/auth/google', {
    method: 'POST',
    body: JSON.stringify({ google_id_token: googleIdToken }),
  });
};

// Legacy concept map generation - REMOVED
// Use generateHierarchicalMindMap instead

// Generate hierarchical mind map from PDF using VizMind AI
export const generateHierarchicalMindMap = async (file: File, jwt: string) => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/v1/maps/generate-mindmap`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${jwt}`,
      },
      body: formData,
    });

    // Check for 401 Unauthorized response (token expired)
    if (response.status === 401) {
      console.warn('Token expired or invalid during mind map generation. Logging out user.');
      handleTokenExpiration();
      return { error: 'Authentication expired. Please log in again.' };
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: MindMapResponse = await response.json();

    // Check if the backend returned an error
    if (data.status === 'error' || data.error_message) {
      return { error: data.error_message || 'Mind map generation failed' };
    }

    // Transform the response to match what the frontend expects
    if (data.hierarchical_data && data.mongodb_doc_id) {
      const transformedData = {
        mongodb_doc_id: data.mongodb_doc_id,
        title: data.attachment.filename.replace('.pdf', ''),
        hierarchical_data: data.hierarchical_data,
        original_filename: data.attachment.filename,
        processing_metadata: data.processing_metadata
      };
      return { data: transformedData };
    }

    return { error: 'No mind map data received from server' };
  } catch (error) {
    console.error('Generate hierarchical mind map failed:', error);
    return { error: error instanceof Error ? error.message : 'Unknown error' };
  };
};

// Get user's map history
export const getMapHistory = async (jwt: string) => {
  return makeRequest<{
    history: Array<{
      map_id: string;
      title: string;
      original_filename: string;
      created_at: string;
    }>;
  }>('/api/v1/maps/history', {}, jwt);
};

// Get specific hierarchical mind map
export const getHierarchicalMindMap = async (mapId: string, jwt: string) => {
  return makeRequest<{
    mongodb_doc_id: string;
    title: string;
    hierarchical_data: {
      id: string;
      data: { label: string };
      children: any[];
    };
    original_filename?: string;
  }>(`/api/v1/maps/${mapId}`, {}, jwt);
};


export const deleteChatHistory = async (
  mapId: string,
  nodeId: string,
  jwt: string
) => {
  return makeRequest<{ success: boolean; message: string }>(`/api/v1/chat/delete/${mapId}/${nodeId}`, {
    method: 'DELETE',
  }, jwt);
};

export const askQuestionWithHistory = async (
  mapId: string,
  question: string,
  jwt: string,
  nodeId?: string,
  nodeLabel?: string,
  nodeParent?: string,
  nodeChildren?: string[],
  topK: number = 5
) => {
  return makeRequest<NodeDetailResponse>(`/api/v1/chat`, {
    method: 'POST',
    body: JSON.stringify({
      map_id: mapId,
      question: question,
      node_id: nodeId,
      node_label: nodeLabel,
      node_parent: nodeParent,
      node_children: nodeChildren,
      top_k: topK,
    }),
  }, jwt);
};