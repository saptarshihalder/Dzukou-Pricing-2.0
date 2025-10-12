// API utility functions for the frontend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new ApiError(response.status, `HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

// Scraping API functions
export const scrapingApi = {
  async getLatestRun() {
    return apiRequest<{
      id: string;
      status: string;
      started_at: string;
      completed_at: string | null;
      stores_total: number;
      stores_completed: number;
      products_found: number;
    } | null>('/routes/latest-run');
  },

  async startScraping(targetProducts?: string[], stores?: string[]) {
    return apiRequest<{ run_id: string }>('/routes/start-scraping', {
      method: 'POST',
      body: JSON.stringify({
        target_products: targetProducts,
        stores: stores,
      }),
    });
  },

  async stopScraping(runId: string) {
    return apiRequest<{ message: string; run_id: string }>(`/routes/stop-scraping/${runId}`, {
      method: 'POST',
    });
  },

  async getProgress(runId: string) {
    return apiRequest<{
      status: string;
      stores_total: number;
      stores_completed: number;
      products_found: number;
    }>(`/routes/scraping-progress/${runId}`);
  },

  async getResults(runId: string) {
    return apiRequest<Array<{
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
    }>>(`/routes/scraping-results/${runId}`);
  },

  async exportResults(runId: string) {
    const response = await fetch(`${API_BASE_URL}/routes/runs/${runId}/export.csv`);
    if (!response.ok) {
      throw new ApiError(response.status, `Export failed: ${response.status}`);
    }
    return response.blob();
  },
};

// Optimization API functions
export const optimizationApi = {
  async getCachedRecommendations(maxAgeHours: number = 24) {
    return apiRequest<{
      recommendations: Array<{
        product_id: string;
        current_price: number;
        recommended_price: number;
        price_change_percent: number;
        expected_profit_change: number;
        risk_level: 'low' | 'medium' | 'high';
        confidence_score: number;
        scenarios: {
          conservative: { price: number; expected_margin: number };
          recommended: { price: number; expected_margin: number };
          aggressive: { price: number; expected_margin: number };
        };
        rationale: string;
        constraint_flags: string[];
      }>;
      cache_info: {
        cached_products: number;
        cache_age_hours: number;
        oldest_cache: string | null;
        newest_cache: string | null;
      };
    }>(`/routes/cached-recommendations?max_age_hours=${maxAgeHours}`);
  },

  async optimizePrice(productId: string, constraints?: {
    min_margin_percent?: number;
    max_price_increase_percent?: number;
    psychological_pricing?: boolean;
  }) {
    return apiRequest<{
      product_id: string;
      current_price: number;
      recommended_price: number;
      price_change_percent: number;
      expected_profit_change: number;
      risk_level: 'low' | 'medium' | 'high';
      confidence_score: number;
      scenarios: {
        conservative: { price: number; expected_margin: number };
        recommended: { price: number; expected_margin: number };
        aggressive: { price: number; expected_margin: number };
      };
      rationale: string;
      constraint_flags: string[];
    }>('/routes/optimize-price', {
      method: 'POST',
      body: JSON.stringify({
        product_id: productId,
        constraints,
      }),
    });
  },

  async optimizeBatch(productIds?: string[], constraints?: {
    min_margin_percent?: number;
    max_price_increase_percent?: number;
    psychological_pricing?: boolean;
  }, useCache: boolean = true, cacheMaxAgeHours: number = 24) {
    const url = new URL(`${API_BASE_URL}/routes/optimize-batch`);
    url.searchParams.set('use_cache', useCache.toString());
    url.searchParams.set('cache_max_age_hours', cacheMaxAgeHours.toString());

    return apiRequest<{
      recommendations: Array<{
        product_id: string;
        current_price: number;
        recommended_price: number;
        price_change_percent: number;
        expected_profit_change: number;
        risk_level: 'low' | 'medium' | 'high';
        confidence_score: number;
        scenarios: {
          conservative: { price: number; expected_margin: number };
          recommended: { price: number; expected_margin: number };
          aggressive: { price: number; expected_margin: number };
        };
        rationale: string;
        constraint_flags: string[];
      }>;
    }>(url.pathname + url.search, {
      method: 'POST',
      body: JSON.stringify({
        product_ids: productIds,
        constraints,
      }),
    });
  },
};

// Health check
export const healthApi = {
  async check() {
    return apiRequest<{ ok: boolean }>('/routes/health');
  },
};

// Utility functions for data formatting
export const formatters = {
  currency: (amount: number, currency = 'EUR') => {
    return new Intl.NumberFormat('en-EU', {
      style: 'currency',
      currency,
    }).format(amount);
  },

  percentage: (value: number) => {
    return `${value.toFixed(1)}%`;
  },

  date: (dateString: string) => {
    return new Date(dateString).toLocaleString();
  },

  confidence: (score: number) => {
    return `${Math.round(score * 100)}%`;
  },
};

// Error handling utilities
export const handleApiError = (error: unknown): string => {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 400:
        return 'Invalid request. Please check your input.';
      case 404:
        return 'Resource not found.';
      case 500:
        return 'Internal server error. Please try again later.';
      default:
        return `Server error: ${error.message}`;
    }
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return 'An unexpected error occurred.';
};