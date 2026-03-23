import { useState, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { API } from '../config/endpoints';

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
        API.SCHEMA_SCAN(dbName, sessionId),
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ database_name: dbName })
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
