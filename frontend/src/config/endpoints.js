/**
 * Frontend API Configuration
 * Centralizado en un solo lugar para evitar hardcoding de puertos
 */

// ✅ Usa VITE_API_URL del .env, default http://localhost:8000
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Endpoints - Aligned with backend router definitions
export const API = {
  // Health
  HEALTH: `${API_URL}/api/health`,
  
  // Database Management (@router.get("") and @router.post("/save"))
  // Note: Backend does NOT use user_id parameter for these endpoints
  DATABASE_LIST: () => `${API_URL}/api/databases`,
  DATABASE_TEST: () => `${API_URL}/api/databases/test`,
  DATABASE_ADD: () => `${API_URL}/api/databases/save`,
  DATABASE_ACTIVATE: (dbName) => `${API_URL}/api/databases/${dbName}/activate`,
  DATABASE_DELETE: (dbName) => `${API_URL}/api/databases/${dbName}`,
  DATABASE_GET: (dbName) => `${API_URL}/api/databases/${dbName}`,
  CREDENTIAL_LIST: () => `${API_URL}/api/databases/credentials/list`,
  CREDENTIAL_VERIFY: (dbName) => `${API_URL}/api/databases/credentials/${dbName}/verify`,
  
  // Schema (@router.post("/scan") and @router.get(""))
  SCHEMA_SCAN: (dbName, sessionId) => 
    `${API_URL}/api/schema/scan?db_name=${dbName}&session_id=${sessionId}`,
  SCHEMA_GET: (dbName, sessionId) =>
    `${API_URL}/api/schema?db_name=${dbName}&session_id=${sessionId}`,
  SCHEMA_EXPORT: (dbName) =>
    `${API_URL}/api/schema/export?db_name=${dbName}`,
  
  // Query & Ambiguity
  ANALYZE_AMBIGUITY: `${API_URL}/api/query/analyze-ambiguity`,
  SELECT_CLARIFICATION: `${API_URL}/api/query/select-clarification`,
  QUERY_SUBMIT: `${API_URL}/api/query`,
  QUERY_EXAMPLES: `${API_URL}/api/query/examples`,
};

console.log('🔌 API Configuration:', { API_URL, API });

export default API;
