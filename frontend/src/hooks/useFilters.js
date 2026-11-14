import { useState, useCallback } from 'react';

export function useFilters(initialState = {}) {
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    category_id: undefined,
    region_id: undefined,
    search: '',
    datePreset: 'all',
    ...initialState
  });

  const setDatePreset = useCallback((preset) => {
    const today = new Date();
    let start = new Date();

    if (preset === '30d') {
      start.setDate(today.getDate() - 30);
    } else if (preset === '90d') {
      start.setDate(today.getDate() - 90);
    } else if (preset === '12m') {
      start.setFullYear(today.getFullYear() - 1);
    } else if (preset === 'all') {
      setFilters(prev => ({
        ...prev,
        start_date: '',
        end_date: '',
        datePreset: 'all'
      }));
      return;
    }

    setFilters(prev => ({
      ...prev,
      start_date: start.toISOString().split('T')[0],
      end_date: today.toISOString().split('T')[0],
      datePreset: preset
    }));
  }, []);

  const setCategory = useCallback((categoryId) => {
    setFilters(prev => ({
      ...prev,
      category_id: categoryId || undefined
    }));
  }, []);

  const setRegion = useCallback((regionId) => {
    setFilters(prev => ({
      ...prev,
      region_id: regionId || undefined
    }));
  }, []);

  const setSearch = useCallback((query) => {
    setFilters(prev => ({
      ...prev,
      search: query
    }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters({
      start_date: '',
      end_date: '',
      category_id: undefined,
      region_id: undefined,
      search: '',
      datePreset: 'all'
    });
  }, []);

  return {
    filters,
    setFilters,
    setDatePreset,
    setCategory,
    setRegion,
    setSearch,
    resetFilters
  };
}

