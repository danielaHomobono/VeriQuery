import { useState, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';

export const useSchemaScanner = () => {
  const { selectedDatabase, sessionId } = useAppStore();
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!selectedDatabase || !sessionId) {
      setSchema(null);
      return;
    }

    scanSchema();
  }, [selectedDatabase, sessionId]);

  const scanSchema = async () => {
    setLoading(true);
    setError(null);

    try {
      // selectedDatabase might be a string or object, handle both cases
      const dbName = typeof selectedDatabase === 'string' 
        ? selectedDatabase 
        : selectedDatabase.db_name;

      const response = await fetch(
        `http://localhost:8889/api/schema/scan?db_name=${dbName}&session_id=${sessionId}`,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to scan schema: ${response.statusText}`);
      }

      const data = await response.json();
      setSchema(data);
    } catch (err) {
      console.error('Schema scan error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { schema, loading, error, refetch: scanSchema };
};
