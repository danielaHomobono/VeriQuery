/**
 * Frontend API Configuration
 * Centralizado en un solo lugar para evitar hardcoding de puertos
 */

// ✅ Usa VITE_API_URL del .env, default http://localhost:8000
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Endpoints
export const API = {
  // Health
  HEALTH: `${API_URL}/api/health`,
  
  // Database Management
  DATABASE_LIST: (userId) => `${API_URL}/api/databases/list?user_id=${userId}`,
  DATABASE_TEST: `${API_URL}/api/databases/test-connection`,
  DATABASE_ADD: (userId) => `${API_URL}/api/databases/add?user_id=${userId}`,
  DATABASE_VERIFY: (dbName) => `${API_URL}/api/databases/verify?db_name=${dbName}`,
  
  // Schema
  SCHEMA_SCAN: (dbName, sessionId) => 
    `${API_URL}/api/schema/scan?db_name=${dbName}&session_id=${sessionId}`,
  
  // Query & Ambiguity
  ANALYZE_AMBIGUITY: `${API_URL}/api/query/analyze-ambiguity`,
  SELECT_CLARIFICATION: `${API_URL}/api/query/select-clarification`,
};

console.log('🔌 API Configuration:', { API_URL, API });

export default API;
