import { useState, useEffect } from 'react';
import { apiFetch, API_ENDPOINTS } from '../config/api';

/**
 * Hook para conectarse al backend
 */
export const useBackendConnection = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [backendStatus, setBackendStatus] = useState(null);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        setLoading(true);
        const data = await apiFetch(API_ENDPOINTS.health);
        setBackendStatus(data);
        setIsConnected(true);
        setError(null);
        console.log('✅ Connected to backend:', data);
      } catch (err) {
        setIsConnected(false);
        setError(err.message);
        console.error('❌ Backend connection failed:', err);
      } finally {
        setLoading(false);
      }
    };

    checkConnection();
    
    // Verificar cada 30 segundos
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  return { isConnected, loading, error, backendStatus };
};

/**
 * Hook para test de conexión a base de datos
 */
export const useTestConnection = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const testConnection = async (config) => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiFetch(API_ENDPOINTS.testConnection, {
        method: 'POST',
        body: JSON.stringify(config),
      });
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { testConnection, loading, error, result };
};

/**
 * Hook para obtener esquema
 */
export const useScanSchema = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [schema, setSchema] = useState(null);

  const scanSchema = async (databaseName) => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiFetch(`${API_ENDPOINTS.scanSchema}?db=${databaseName}`);
      setSchema(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { scanSchema, loading, error, schema };
};

export default useBackendConnection;
