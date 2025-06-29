const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

// Helper function to make authenticated requests
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

// Generate concept map
export const generateConceptMap = async (files: File[], jwt: string) => {
  try {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    const response = await fetch(`${API_BASE_URL}/api/v1/maps/generate/`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${jwt}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    console.error('Generate concept map failed:', error);
    return { error: error instanceof Error ? error.message : 'Unknown error' };
  }
};

// Get user's map history
export const getMapHistory = async (jwt: string) => {
  return makeRequest<{
    history: Array<{
      map_id: string;
      source_filename: string;
      created_at: string;
    }>;
  }>('/api/v1/maps/history/', {}, jwt);
};

// Get specific concept map
export const getConceptMap = async (mapId: string, jwt: string) => {
  return makeRequest<{
    mongodb_doc_id: string;
    react_flow_data: {
      nodes: Array<{
        id: string;
        data: { label: string };
        position: { x: number; y: number };
      }>;
      edges: Array<{
        id: string;
        source: string;
        target: string;
        label?: string;
      }>;
    };
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
  }>(`/api/v1/maps/details/?${params.toString()}`, {}, jwt);
};

// Ask question about concept
export const askQuestion = async (
  conceptMapId: string,
  question: string,
  jwt: string,
  contextNodeLabel?: string
) => {
  const params = new URLSearchParams({
    concept_map_id: conceptMapId,
    question,
  });

  if (contextNodeLabel) {
    params.append('context_node_label', contextNodeLabel);
  }

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
  }>(`/api/v1/maps/ask/?${params.toString()}`, {}, jwt);
};