import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import API_BASE_URL from '../../config';

// Loads /filter-options for a column. The column goes in the query string so
// names containing "/", "?" or "#" work.
const useFilterOptions = (column, onError) => {
  const [options, setOptions] = useState({});
  const [loading, setLoading] = useState(true);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`${API_BASE_URL}/filter-options`, { params: { column } });
        if (!cancelled) setOptions(response.data || {});
      } catch (error) {
        if (!cancelled) onErrorRef.current?.('Failed to load filter options');
        console.error('Error loading filter options:', error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [column]);

  return { options, loading };
};

export default useFilterOptions;
