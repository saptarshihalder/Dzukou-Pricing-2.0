"use client";

import { useEffect, useState, useCallback } from "react";
import { AppLayout } from "@/components/app-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  Search, 
  BarChart3, 
  Target, 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Package,
  AlertCircle,
  CheckCircle,
  Loader2,
  RefreshCw
} from "lucide-react";
import Link from "next/link";
import { formatters, handleApiError } from "@/lib/api";
import { usePriceOptimization } from "@/lib/hooks";

// Helper function to make API requests directly
async function fetchAPI<T>(endpoint: string): Promise<T> {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
}

interface DashboardStats {
  total_products: number;
  avg_margin: number;
  potential_uplift: number;
  avg_price_change: number;
  last_scrape_date: string | null;
  scraping_stats: {
    stores_scraped: number;
    stores_total: number;
    products_found: number;
  } | null;
}

interface Product {
  id: string;
  name: string;
  category: string;
  brand: string;
  unit_cost: number;
  current_price: number;
  currency: string;
  margin: number;
}

export default function Dashboard() {
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshingPortfolio, setRefreshingPortfolio] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { recommendations, optimizeBatch } = usePriceOptimization();

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch dashboard stats and products in parallel
      const [statsResponse, productsResponse] = await Promise.all([
        fetchAPI<DashboardStats>('/routes/dashboard-stats'),
        fetchAPI<Product[]>('/routes/products')
      ]);

      setDashboardStats(statsResponse);
      setProducts(productsResponse);

      // Generate some recommendations for display
      if (productsResponse.length > 0) {
        const sampleProductIds = productsResponse.slice(0, 4).map((p: Product) => p.id);
        try {
          await optimizeBatch(sampleProductIds, {
            min_margin_percent: 30,
            max_price_increase_percent: 20,
            psychological_pricing: false
          });
        } catch (err) {
          // Don't fail the whole dashboard if optimization fails
          console.warn('Failed to generate recommendations:', err);
        }
      }
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshPortfolioData = useCallback(async () => {
    try {
      setRefreshingPortfolio(true);
      setError(null);

      // Fetch fresh data
      const [statsResponse, productsResponse] = await Promise.all([
        fetchAPI<DashboardStats>('/routes/dashboard-stats'),
        fetchAPI<Product[]>('/routes/products')
      ]);

      setDashboardStats(statsResponse);
      setProducts(productsResponse);

      // Generate fresh recommendations (no cache)
      if (productsResponse.length > 0) {
        const sampleProductIds = productsResponse.slice(0, 4).map((p: Product) => p.id);
        try {
          await optimizeBatch(sampleProductIds, {
            min_margin_percent: 30,
            max_price_increase_percent: 20,
            psychological_pricing: false
          }, false); // useCache = false for fresh data
        } catch (err) {
          console.warn('Failed to generate fresh recommendations:', err);
        }
      }
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setRefreshingPortfolio(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    fetchDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getRiskBadgeVariant = (risk: string) => {
    switch (risk) {
      case "low": return "default";
      case "medium": return "secondary"; 
      case "high": return "destructive";
      default: return "default";
    }
  };

  if (loading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>Loading dashboard data...</span>
          </div>
        </div>
      </AppLayout>
    );
  }

  if (error) {
    return (
      <AppLayout>
        <div className="text-center py-12">
          <AlertCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">
            Failed to load dashboard
          </h3>
          <p className="text-muted-foreground mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>
            Try Again
          </Button>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground">
          Price Optimization Dashboard
        </h1>
        <p className="mt-2 text-muted-foreground">
          Monitor your pricing strategy and competitive position
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Link href="/scraping">
          <Card className="cursor-pointer hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Start Scraping</CardTitle>
              <Search className="h-4 w-4 ml-auto text-blue-600" />
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Collect latest competitor prices
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/competitive-analysis">
          <Card className="cursor-pointer hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">View Analysis</CardTitle>
              <BarChart3 className="h-4 w-4 ml-auto text-green-600" />
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Analyze market positioning
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/pricing-recommendations">
          <Card className="cursor-pointer hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Get Recommendations</CardTitle>
              <Target className="h-4 w-4 ml-auto text-purple-600" />
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Optimize your pricing strategy
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Products</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats?.total_products || 0}</div>
            <p className="text-xs text-muted-foreground">
              In catalog
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Margin</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatters.percentage(dashboardStats?.avg_margin || 0)}</div>
            <p className="text-xs text-muted-foreground">
              Across portfolio
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Potential Uplift</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatters.percentage(dashboardStats?.potential_uplift || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Revenue increase
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Price Change</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatters.percentage(dashboardStats?.avg_price_change || 0)}</div>
            <p className="text-xs text-muted-foreground">
              Recommended adjustment
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Portfolio Overview */}
      <Card className="mb-8">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Portfolio Overview</CardTitle>
              <CardDescription>
                Current pricing vs recommendations for your product catalog
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={refreshPortfolioData}
              disabled={refreshingPortfolio}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${refreshingPortfolio ? 'animate-spin' : ''}`} />
              {refreshingPortfolio ? 'Refreshing...' : 'Refresh'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Product</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Current Price</TableHead>
                  <TableHead>Margin</TableHead>
                  <TableHead>Suggested Price</TableHead>
                  <TableHead>Change</TableHead>
                  <TableHead>Uplift</TableHead>
                  <TableHead>Risk</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.slice(0, 5).map((product) => {
                  const recommendation = recommendations.find(r => r.product_id === product.id);
                  return (
                    <TableRow key={product.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{product.name}</div>
                          <div className="text-sm text-muted-foreground">{product.id}</div>
                        </div>
                      </TableCell>
                      <TableCell>{product.category}</TableCell>
                      <TableCell>{formatters.currency(product.current_price, product.currency)}</TableCell>
                      <TableCell>{formatters.percentage(product.margin)}</TableCell>
                      <TableCell className="font-medium">
                        {recommendation ? formatters.currency(recommendation.recommended_price, product.currency) : '-'}
                      </TableCell>
                      <TableCell>
                        {recommendation ? (
                          <div className="flex items-center">
                            {recommendation.price_change_percent > 0 ? (
                              <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
                            ) : (
                              <TrendingDown className="h-4 w-4 text-red-600 mr-1" />
                            )}
                            <span className={recommendation.price_change_percent > 0 ? "text-green-600" : "text-red-600"}>
                              {formatters.percentage(recommendation.price_change_percent)}
                            </span>
                          </div>
                        ) : '-'}
                      </TableCell>
                      <TableCell className="text-green-600 font-medium">
                        {recommendation ? formatters.currency(recommendation.expected_profit_change, product.currency) : '-'}
                      </TableCell>
                      <TableCell>
                        {recommendation ? (
                          <Badge variant={getRiskBadgeVariant(recommendation.risk_level)}>
                            {recommendation.risk_level}
                          </Badge>
                        ) : (
                          <Badge variant="outline">No data</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
          {products.length > 5 && (
            <div className="mt-4 text-center">
              <Button variant="outline" asChild>
                <Link href="/pricing-recommendations">
                  View All Products ({products.length})
                </Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Status Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Last Scraping Run</CardTitle>
            <CardDescription>
              Status of the most recent competitor data collection
            </CardDescription>
          </CardHeader>
          <CardContent>
            {dashboardStats?.last_scrape_date ? (
              <>
                <div className="flex items-center space-x-2 mb-4">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="font-medium">Completed Successfully</span>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Completed:</span>
                    <span>{formatters.date(dashboardStats.last_scrape_date)}</span>
                  </div>
                  {dashboardStats.scraping_stats && (
                    <>
                      <div className="flex justify-between">
                        <span>Stores scraped:</span>
                        <span>{dashboardStats.scraping_stats.stores_scraped} of {dashboardStats.scraping_stats.stores_total}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Products found:</span>
                        <span>{dashboardStats.scraping_stats.products_found.toLocaleString()}</span>
                      </div>
                    </>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center space-x-2 mb-4">
                <AlertCircle className="h-5 w-5 text-yellow-600" />
                <span className="font-medium">No completed runs</span>
              </div>
            )}
            <Button className="w-full mt-4" asChild>
              <Link href="/scraping">
                Start New Scrape
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Market Insights</CardTitle>
            <CardDescription>
              Key competitive intelligence from latest analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <TrendingUp className="h-5 w-5 text-green-600 mt-0.5" />
                <div>
                  <p className="font-medium text-sm">Potential Revenue Uplift</p>
                  <p className="text-sm text-muted-foreground">
                    {dashboardStats?.potential_uplift ? 
                      `${formatters.percentage(dashboardStats.potential_uplift)} revenue increase opportunity identified` :
                      'Run competitive analysis to identify pricing opportunities'
                    }
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <DollarSign className="h-5 w-5 text-blue-600 mt-0.5" />
                <div>
                  <p className="font-medium text-sm">Current Portfolio Margin</p>
                  <p className="text-sm text-muted-foreground">
                    {dashboardStats?.avg_margin ? 
                      `Average margin of ${formatters.percentage(dashboardStats.avg_margin)} across ${dashboardStats.total_products} products` :
                      'Calculating portfolio margins...'
                    }
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                {dashboardStats?.last_scrape_date ? (
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                )}
                <div>
                  <p className="font-medium text-sm">Competitive Data</p>
                  <p className="text-sm text-muted-foreground">
                    {dashboardStats?.last_scrape_date ? (
                      `Last updated ${formatters.date(dashboardStats.last_scrape_date)} with ${dashboardStats.scraping_stats?.products_found || 0} competitor prices`
                    ) : (
                      'No recent competitor data available - run a scraping analysis'
                    )}
                  </p>
                </div>
              </div>
            </div>
            <Button variant="outline" className="w-full mt-4" asChild>
              <Link href="/competitive-analysis">
                View Full Analysis
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
