import { useState, useEffect, useCallback } from 'react';
import { scrapingApi, optimizationApi, healthApi, handleApiError } from './api';

// Hook for managing scraping runs
export function useScrapingRun(runId?: string) {
  const [run, setRun] = useState<{
    id: string;
    status: string;
    stores_total: number;
    stores_completed: number;
    products_found: number;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProgress = useCallback(async (id: string) => {
    if (!id) return;
    
    try {
      const progress = await scrapingApi.getProgress(id);
      setRun({
        id,
        status: progress.status,
        stores_total: progress.stores_total,
        stores_completed: progress.stores_completed,
        products_found: progress.products_found,
      });
    } catch (err) {
      setError(handleApiError(err));
    }
  }, []);

  const startScraping = useCallback(async (targetProducts?: string[], stores?: string[]) => {
    setLoading(true);
    setError(null);
    try {
      const result = await scrapingApi.startScraping(targetProducts, stores);
      return result.run_id;
    } catch (err) {
      setError(handleApiError(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const stopScraping = useCallback(async (runId: string) => {
    setLoading(true);
    setError(null);
    try {
      await scrapingApi.stopScraping(runId);
      // Fetch updated progress to reflect stopped status
      await fetchProgress(runId);
    } catch (err) {
      setError(handleApiError(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchProgress]);

  useEffect(() => {
    if (runId) {
      fetchProgress(runId);
      
      // Poll for updates if running
      const interval = setInterval(() => {
        if (run?.status === 'running') {
          fetchProgress(runId);
        }
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [runId, fetchProgress, run?.status]);

  return {
    run,
    loading,
    error,
    startScraping,
    stopScraping,
    fetchProgress,
  };
}

// Hook for managing scraping results
export function useScrapingResults(runId?: string) {
  const [results, setResults] = useState<Array<{
    run_id: string;
    store_name: string;
    product_url: string;
    product_id: string | null;
    title: string;
    price: number;
    currency: string;
    brand: string | null;
    material: string | null;
    size: string | null;
    search_term: string;
    matched_catalog_id: string | null;
    created_at: string;
  }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchResults = useCallback(async (id: string) => {
    if (!id) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await scrapingApi.getResults(id);
      setResults(data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const exportResults = useCallback(async (id: string) => {
    try {
      const blob = await scrapingApi.exportResults(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scraping-results-${id}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(handleApiError(err));
    }
  }, []);

  useEffect(() => {
    if (runId) {
      fetchResults(runId);
    }
  }, [runId, fetchResults]);

  return {
    results,
    loading,
    error,
    fetchResults,
    exportResults,
  };
}

// Hook for price optimization
export function usePriceOptimization() {
  const [recommendations, setRecommendations] = useState<Array<{
    product_id: string;
    current_price: number;
    recommended_price: number;
    price_change_percent: number;
    expected_profit_change: number;
    risk_level: 'low' | 'medium' | 'high';
    confidence_score: number;
    scenarios: {
      conservative: { price: number; expected_margin: number; psychological_analysis?: any };
      recommended: { price: number; expected_margin: number; psychological_analysis?: any };
      aggressive: { price: number; expected_margin: number; psychological_analysis?: any };
    };
    rationale: string;
    constraint_flags: string[];
    psychological_analysis?: any;
    psychological_pricing_enabled?: boolean;
  }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cacheInfo, setCacheInfo] = useState<{
    cached_products: number;
    cache_age_hours: number;
    oldest_cache: string | null;
    newest_cache: string | null;
  } | null>(null);

  const getCachedRecommendations = useCallback(async (maxAgeHours: number = 24) => {
    setLoading(true);
    setError(null);
    try {
      const result = await optimizationApi.getCachedRecommendations(maxAgeHours);
      setRecommendations(result.recommendations);
      setCacheInfo(result.cache_info);
      return result;
    } catch (err) {
      setError(handleApiError(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const optimizePrice = useCallback(async (productId: string, constraints?: {
    min_margin_percent?: number;
    max_price_increase_percent?: number;
    psychological_pricing?: boolean;
  }) => {
    setLoading(true);
    setError(null);
    try {
      const recommendation = await optimizationApi.optimizePrice(productId, constraints);
      return recommendation;
    } catch (err) {
      setError(handleApiError(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const optimizeBatch = useCallback(async (productIds?: string[], constraints?: {
    min_margin_percent?: number;
    max_price_increase_percent?: number;
    psychological_pricing?: boolean;
  }, useCache: boolean = true, cacheMaxAgeHours: number = 24) => {
    setLoading(true);
    setError(null);
    try {
      const result = await optimizationApi.optimizeBatch(productIds, constraints, useCache, cacheMaxAgeHours);
      setRecommendations(result.recommendations);
      // Clear cache info when doing fresh optimization
      if (!useCache) {
        setCacheInfo(null);
      }
      return result.recommendations;
    } catch (err) {
      setError(handleApiError(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    recommendations,
    loading,
    error,
    cacheInfo,
    optimizePrice,
    optimizeBatch,
    getCachedRecommendations,
  };
}

// Hook for API health monitoring
export function useApiHealth() {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      await healthApi.check();
      setIsHealthy(true);
      setLastCheck(new Date());
    } catch {
      setIsHealthy(false);
      setLastCheck(new Date());
    }
  }, []);

  useEffect(() => {
    checkHealth();
    
    // Check health every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return {
    isHealthy,
    lastCheck,
    checkHealth,
  };
}

// Hook for local storage persistence
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue] as const;
}

// Hook for debounced values
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}