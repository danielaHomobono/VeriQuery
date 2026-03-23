/**
 * API Configuration
 * 
 * Conecta el frontend al backend FastAPI
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_TIMEOUT = 30000; // 30 segundos

export const apiConfig = {
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  }
};

/**
 * Fetch wrapper con mejor manejo de errores
 */
export const apiFetch = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  console.log(`📡 API Call: ${options.method || 'GET'} ${url}`);
  
  try {
    const response = await fetch(url, {
      ...apiConfig,
      ...options,
      headers: {
        ...apiConfig.headers,
        ...options.headers,
      }
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log(`✅ Response:`, data);
    return data;
  } catch (error) {
    console.error(`❌ API Error: ${error.message}`);
    throw error;
  }
};

/**
 * API Endpoints
 */
export const API_ENDPOINTS = {
  // Health
  health: '/api/health',
  
  // Database Management
  testConnection: '/api/database/test-connection',
  saveDatabase: '/api/database/save',
  listDatabases: '/api/database/list',
  activateDatabase: '/api/database/activate',
  
  // Schema
  scanSchema: '/api/schema/scan',
  getCachedSchema: '/api/schema/cached',
  exportSchema: '/api/schema/export',
  
  // Queries
  executeQuery: '/api/query/execute',
  analyzeAmbiguity: '/api/ambiguity/analyze',
  
  // Docs
  docs: '/docs',
  openapi: '/openapi.json',
};

export default apiConfig;
