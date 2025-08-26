const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

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

// Generate hierarchical mind map from PDF (NEW)
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

    const data = await response.json();
    return { data };
  } catch (error) {
    console.error('Generate hierarchical mind map failed:', error);
    return { error: error instanceof Error ? error.message : 'Unknown error' };
  }
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

// Get node details using RAG
export const getNodeDetails = async (
  mapId: string,
  nodeQuery: string,
  jwt: string,
  topK: number = 3
) => {
  const params = new URLSearchParams({
    map_id: mapId,
    node_query: nodeQuery,
    top_k: topK.toString(),
  });

  return makeRequest<{
    query: string;
    answer: string;
    cited_sources: Array<{
      type: string;
      identifier: string;
      title: string;
      snippet: string;
    }>;
    message: string;
  }>(`/api/v1/maps/details?${params.toString()}`, {}, jwt);
};

// Ask question about concept
export const askQuestion = async (
  conceptMapId: string,
  question: string,
  jwt: string,
  contextNodeLabel?: string
) => {

  return makeRequest<{
    query: string;
    answer: string;
    cited_sources: Array<{
      type: string;
      identifier: string;
      title: string;
      snippet: string;
    }>;
    search_performed: string;
  }>(`/api/v1/maps/ask`, {
    method: 'POST',
    body: JSON.stringify({
      map_id: conceptMapId,
      question,
    }),
  }, jwt);
};