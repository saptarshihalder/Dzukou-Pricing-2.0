"use client";

import { useState, useEffect } from "react";
import { AppLayout } from "@/components/app-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { 
  TrendingUp, 
  TrendingDown,
  Filter,
  Download,
  AlertTriangle,
  Target,
  Zap,
  Loader2,
  AlertCircle,
  Search,
  RefreshCw,
  CheckCircle,
  DollarSign,
  Eye,
  BarChart3
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts";
import { handleApiError, formatters } from "@/lib/api";

// Helper function to make API requests
async function fetchAPI<T>(endpoint: string): Promise<T> {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
}

interface CategoryAnalysis {
  category: string;
  our_avg_price: number;
  competitor_min: number;
  competitor_max: number;
  competitor_median: number;
  market_position: string;
  opportunity: number;
  products: number;
  competitor_data_points: number;
}

interface StoreAnalysis {
  store: string;
  avg_price: number;
  price_range: string;
  products: number;
  overlap: number;
  overlap_percent: number;
  positioning: string;
}

export default function CompetitiveAnalysisPage() {
  const [categoryAnalysis, setCategoryAnalysis] = useState<CategoryAnalysis[]>([]);
  const [storeAnalysis, setStoreAnalysis] = useState<StoreAnalysis[]>([]);
  const [filteredCategoryAnalysis, setFilteredCategoryAnalysis] = useState<CategoryAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("opportunity");
  const [positionFilter, setPositionFilter] = useState("all");
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [overviewStats, setOverviewStats] = useState({
    marketPosition: 73,
    avgPriceGap: 12.3,
    revenueOpportunity: 8450
  });

  useEffect(() => {
    const fetchAnalysisData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [categoryData, storeData] = await Promise.all([
          fetchAPI<CategoryAnalysis[]>('/routes/competitive-analysis/categories'),
          fetchAPI<StoreAnalysis[]>('/routes/competitive-analysis/stores')
        ]);

        console.log('Category data received:', categoryData);
        console.log('Store data received:', storeData);
        setCategoryAnalysis(categoryData);
        setStoreAnalysis(storeData);
        setLastRefresh(new Date());
        
        // Calculate overview stats from real data
        if (categoryData.length > 0) {
          const competitiveCount = categoryData.filter(c => c.market_position === 'competitive').length;
          const marketPosition = Math.round((competitiveCount / categoryData.length) * 100);
          const avgOpportunity = categoryData.reduce((sum, c) => sum + c.opportunity, 0) / categoryData.length;
          
          setOverviewStats({
            marketPosition,
            avgPriceGap: avgOpportunity,
            revenueOpportunity: Math.round(avgOpportunity * 686) // Rough estimate
          });
        }
      } catch (err) {
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysisData();
  }, []);

  // Apply filters and sorting to category analysis
  useEffect(() => {
    console.log('Applying filters to categoryAnalysis:', categoryAnalysis);
    console.log('Current filters - searchTerm:', searchTerm, 'positionFilter:', positionFilter, 'sortBy:', sortBy);
    let filtered = [...categoryAnalysis];
    
    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(row => 
        row.category.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // Position filter
    if (positionFilter !== 'all') {
      filtered = filtered.filter(row => row.market_position === positionFilter);
    }
    
    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'opportunity':
          return b.opportunity - a.opportunity;
        case 'products':
          return b.products - a.products;
        case 'data_points':
          return b.competitor_data_points - a.competitor_data_points;
        case 'category':
          return a.category.localeCompare(b.category);
        default:
          return 0;
      }
    });
    
    console.log('Filtered results:', filtered);
    setFilteredCategoryAnalysis(filtered);
  }, [categoryAnalysis, searchTerm, positionFilter, sortBy]);

  const refreshData = async () => {
    setRefreshing(true);
    try {
      const [categoryData, storeData] = await Promise.all([
        fetchAPI<CategoryAnalysis[]>('/routes/competitive-analysis/categories'),
        fetchAPI<StoreAnalysis[]>('/routes/competitive-analysis/stores')
      ]);

      setCategoryAnalysis(categoryData);
      setStoreAnalysis(storeData);
      setLastRefresh(new Date());
      
      // Recalculate overview stats
      if (categoryData.length > 0) {
        const competitiveCount = categoryData.filter(c => c.market_position === 'competitive').length;
        const marketPosition = Math.round((competitiveCount / categoryData.length) * 100);
        const avgOpportunity = categoryData.reduce((sum, c) => sum + c.opportunity, 0) / categoryData.length;
        
        setOverviewStats({
          marketPosition,
          avgPriceGap: avgOpportunity,
          revenueOpportunity: Math.round(avgOpportunity * 686)
        });
      }
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setRefreshing(false);
    }
  };

  const formatCurrency = (amount: number) => formatters.currency(amount);
  const formatPercent = (value: number) => formatters.percentage(value);

  const getPositionBadge = (position: string) => {
    switch (position) {
      case "competitive": return <Badge variant="default">Competitive</Badge>;
      case "above": return <Badge variant="secondary">Above Market</Badge>;
      case "below": return <Badge variant="outline">Below Market</Badge>;
      default: return <Badge variant="outline">{position}</Badge>;
    }
  };

  const getPositionColor = (position: string) => {
    switch (position) {
      case "below": return "text-green-600 bg-green-100";
      case "above": return "text-red-600 bg-red-100";
      case "competitive": return "text-blue-600 bg-blue-100";
      default: return "text-gray-600 bg-gray-100";
    }
  };

  const getPositioningBadge = (positioning: string) => {
    switch (positioning) {
      case "premium": return <Badge variant="secondary">Premium</Badge>;
      case "luxury": return <Badge className="bg-purple-100 text-purple-800">Luxury</Badge>;
      case "value": return <Badge variant="outline">Value</Badge>;
      default: return <Badge variant="outline">{positioning}</Badge>;
    }
  };

  const getPositionIcon = (position: string) => {
    switch (position) {
      case "below": return <TrendingUp className="h-4 w-4" />;
      case "above": return <TrendingDown className="h-4 w-4" />;
      case "competitive": return <Target className="h-4 w-4" />;
      default: return <DollarSign className="h-4 w-4" />;
    }
  };

  const exportCategoryData = () => {
    if (filteredCategoryAnalysis.length === 0) {
      return;
    }

    const csvData = filteredCategoryAnalysis.map(row => ({
      'Category': row.category,
      'Our Avg Price': row.our_avg_price,
      'Competitor Min': row.competitor_min,
      'Competitor Median': row.competitor_median,
      'Competitor Max': row.competitor_max,
      'Market Position': row.market_position,
      'Opportunity %': row.opportunity,
      'Our Products': row.products,
      'Competitor Data Points': row.competitor_data_points
    }));
    
    const csv = [
      Object.keys(csvData[0]).join(','),
      ...csvData.map(row => Object.values(row).join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `competitive-analysis-categories-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Prepare chart data
  const chartData = filteredCategoryAnalysis.map(row => ({
    category: row.category.charAt(0).toUpperCase() + row.category.slice(1),
    ourPrice: row.our_avg_price,
    competitorMin: row.competitor_min,
    competitorMedian: row.competitor_median,
    competitorMax: row.competitor_max,
    opportunity: row.opportunity
  }));

  if (loading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>Loading competitive analysis...</span>
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
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Failed to load competitive analysis
          </h3>
          <p className="text-gray-600 dark:text-gray-300 mb-4">{error}</p>
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
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Competitive Analysis
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-300">
          Analyze market positioning and identify pricing opportunities
        </p>
      </div>

          {/* Enhanced Search and Filters */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center">
                  <Filter className="mr-2 h-5 w-5" />
                  Search & Filters
                </div>
                <div className="text-sm text-muted-foreground">
                  Last updated: {lastRefresh.toLocaleTimeString()}
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <div className="lg:col-span-2">
                  <label className="text-sm font-medium mb-2 block">Search Categories</label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                    <Input
                      placeholder="Search categories..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Position</label>
                  <Select value={positionFilter} onValueChange={setPositionFilter}>
                    <SelectTrigger>
                      <SelectValue placeholder="Filter by position" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Positions</SelectItem>
                      <SelectItem value="below">Below Market</SelectItem>
                      <SelectItem value="competitive">Competitive</SelectItem>
                      <SelectItem value="above">Above Market</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Sort By</label>
                  <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger>
                      <SelectValue placeholder="Sort by" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="opportunity">Opportunity</SelectItem>
                      <SelectItem value="products">Product Count</SelectItem>
                      <SelectItem value="data_points">Data Points</SelectItem>
                      <SelectItem value="category">Category Name</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-end gap-2">
                  <Button 
                    onClick={refreshData} 
                    disabled={refreshing}
                    variant="outline" 
                    className="flex-1"
                  >
                    {refreshing ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="mr-2 h-4 w-4" />
                    )}
                    Refresh
                  </Button>
                  <Button onClick={exportCategoryData} variant="outline">
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="categories">By Category</TabsTrigger>
              <TabsTrigger value="stores">By Store</TabsTrigger>
              <TabsTrigger value="gaps">Price Gaps</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                  <CardHeader className="flex flex-row items-center space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Market Position</CardTitle>
                    <Target className="h-4 w-4 ml-auto text-blue-600" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{overviewStats.marketPosition}%</div>
                    <p className="text-xs text-muted-foreground">
                      Products competitively priced
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Avg Price Gap</CardTitle>
                    <TrendingUp className="h-4 w-4 ml-auto text-green-600" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-600">+{overviewStats.avgPriceGap.toFixed(1)}%</div>
                    <p className="text-xs text-muted-foreground">
                      Potential price increase
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Revenue Opportunity</CardTitle>
                    <Zap className="h-4 w-4 ml-auto text-yellow-600" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-yellow-600">€{overviewStats.revenueOpportunity.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">
                      Monthly uplift potential
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Price Comparison Chart */}
              {chartData.length > 0 && (
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <BarChart3 className="mr-2 h-5 w-5 text-blue-600" />
                      Price Comparison by Category
                    </CardTitle>
                    <CardDescription>
                      Visual comparison of our prices vs competitor ranges
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ChartContainer
                      config={{
                        ourPrice: {
                          label: "Our Average Price",
                          color: "hsl(142, 76%, 36%)", // Green
                        },
                        competitorMin: {
                          label: "Competitor Minimum",
                          color: "hsl(217, 91%, 60%)", // Blue
                        },
                        competitorMedian: {
                          label: "Market Median",
                          color: "hsl(45, 93%, 47%)", // Amber/Gold
                        },
                        competitorMax: {
                          label: "Competitor Maximum",
                          color: "hsl(0, 84%, 60%)", // Red
                        },
                      }}
                      className="h-[400px] w-full"
                    >
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart 
                          data={chartData}
                          margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted-foreground))" opacity={0.2} />
                          <XAxis 
                            dataKey="category" 
                            fontSize={12}
                            angle={-45}
                            textAnchor="end"
                            height={80}
                            stroke="hsl(var(--foreground))"
                          />
                          <YAxis 
                            fontSize={12}
                            stroke="hsl(var(--foreground))"
                            tickFormatter={(value) => `€${value}`}
                          />
                          <ChartTooltip 
                            content={<ChartTooltipContent 
                              formatter={(value, name) => [
                                `€${Number(value).toFixed(2)}`,
                                name
                              ]}
                            />} 
                          />
                          <Bar 
                            dataKey="ourPrice" 
                            fill="var(--color-ourPrice)" 
                            name="Our Average Price"
                            radius={[2, 2, 0, 0]}
                          />
                          <Bar 
                            dataKey="competitorMin" 
                            fill="var(--color-competitorMin)" 
                            name="Competitor Minimum"
                            radius={[2, 2, 0, 0]}
                          />
                          <Bar 
                            dataKey="competitorMedian" 
                            fill="var(--color-competitorMedian)" 
                            name="Market Median"
                            radius={[2, 2, 0, 0]}
                          />
                          <Bar 
                            dataKey="competitorMax" 
                            fill="var(--color-competitorMax)" 
                            name="Competitor Maximum"
                            radius={[2, 2, 0, 0]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </ChartContainer>
                    
                    {/* Chart Legend */}
                    <div className="flex flex-wrap justify-center gap-6 mt-4 p-4 bg-muted/30 rounded-lg">
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded" style={{ backgroundColor: "hsl(142, 76%, 36%)" }}></div>
                        <span className="text-sm font-medium">Our Average Price</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded" style={{ backgroundColor: "hsl(217, 91%, 60%)" }}></div>
                        <span className="text-sm font-medium">Competitor Minimum</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded" style={{ backgroundColor: "hsl(45, 93%, 47%)" }}></div>
                        <span className="text-sm font-medium">Market Median</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded" style={{ backgroundColor: "hsl(0, 84%, 60%)" }}></div>
                        <span className="text-sm font-medium">Competitor Maximum</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Top Opportunities */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <AlertTriangle className="mr-2 h-5 w-5 text-yellow-600" />
                    Top Pricing Opportunities
                  </CardTitle>
                  <CardDescription>
                    Categories with the highest pricing optimization potential
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {categoryAnalysis.length > 0 ? (
                    <div className="space-y-4">
                      {categoryAnalysis
                        .sort((a, b) => b.opportunity - a.opportunity)
                        .slice(0, 3)
                        .map((item, index) => (
                        <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                          <div>
                            <div className="font-medium">{item.category}</div>
                            <div className="text-sm text-muted-foreground">
                              Current: {formatCurrency(item.our_avg_price)} | Range: {formatCurrency(item.competitor_min)} - {formatCurrency(item.competitor_max)}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-green-600">+{formatPercent(item.opportunity)}</div>
                            <div className="text-sm text-muted-foreground">
                              {item.products} products
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-6 text-muted-foreground">
                      No competitive data available. Run a scraping operation first.
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Categories Tab */}
            <TabsContent value="categories" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Price Analysis by Category</span>
                    <Badge variant="outline">
                      {filteredCategoryAnalysis.length} of {categoryAnalysis.length} categories
                    </Badge>
                  </CardTitle>
                  <div className="text-sm text-muted-foreground">
                    Debug: Raw categories: {categoryAnalysis.map(c => c.category).join(', ')}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Debug: Filtered categories: {filteredCategoryAnalysis.map(c => c.category).join(', ')}
                  </div>
                  <CardDescription>
                    Compare your pricing strategy across different product categories
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {filteredCategoryAnalysis.length > 0 ? (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Category</TableHead>
                          <TableHead>Our Avg Price</TableHead>
                          <TableHead>Market Range</TableHead>
                          <TableHead>Market Median</TableHead>
                          <TableHead>Position</TableHead>
                          <TableHead>Opportunity</TableHead>
                          <TableHead>Data Points</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredCategoryAnalysis.map((category, index) => (
                          <TableRow key={index} className="hover:bg-muted/50">
                            <TableCell className="font-medium">{category.category}</TableCell>
                            <TableCell>{formatCurrency(category.our_avg_price)}</TableCell>
                            <TableCell>
                              <div className="space-y-1 text-sm">
                                <div className="text-blue-600">{formatCurrency(category.competitor_min)}</div>
                                <div className="text-gray-500">to</div>
                                <div className="text-red-600">{formatCurrency(category.competitor_max)}</div>
                              </div>
                            </TableCell>
                            <TableCell className="font-medium">{formatCurrency(category.competitor_median)}</TableCell>
                            <TableCell>
                              <Badge className={`${getPositionColor(category.market_position)} border-none`}>
                                {getPositionIcon(category.market_position)}
                                <span className="ml-1">{category.market_position}</span>
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className={`font-bold ${
                                category.opportunity > 0 ? 'text-green-600' : 'text-gray-400'
                              }`}>
                                {category.opportunity > 0 ? '+' : ''}{formatPercent(category.opportunity)}
                              </div>
                              {category.opportunity > 0 && (
                                <div className="text-xs text-green-500">
                                  Revenue potential
                                </div>
                              )}
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              <div>{category.products} products</div>
                              <div>{category.competitor_data_points} data points</div>
                            </TableCell>
                            <TableCell>
                              <Dialog>
                                <DialogTrigger asChild>
                                  <Button size="sm" variant="outline">
                                    <Eye className="h-4 w-4 mr-1" />
                                    Details
                                  </Button>
                                </DialogTrigger>
                                <DialogContent className="max-w-2xl">
                                  <DialogHeader>
                                    <DialogTitle className="flex items-center gap-2">
                                      {category.category} Category Analysis
                                      {getPositionBadge(category.market_position)}
                                    </DialogTitle>
                                    <DialogDescription>
                                      Detailed competitive analysis for {category.category} products
                                    </DialogDescription>
                                  </DialogHeader>
                                  <div className="grid grid-cols-2 gap-6">
                                    <div className="space-y-4">
                                      <h4 className="font-medium">Price Distribution</h4>
                                      <div className="space-y-2">
                                        <div className="flex justify-between">
                                          <span className="text-muted-foreground">Our Average:</span>
                                          <span className="font-bold text-green-600">{formatCurrency(category.our_avg_price)}</span>
                                        </div>
                                        <div className="flex justify-between">
                                          <span className="text-muted-foreground">Market Min:</span>
                                          <span className="text-blue-600">{formatCurrency(category.competitor_min)}</span>
                                        </div>
                                        <div className="flex justify-between">
                                          <span className="text-muted-foreground">Market Median:</span>
                                          <span className="text-amber-600">{formatCurrency(category.competitor_median)}</span>
                                        </div>
                                        <div className="flex justify-between">
                                          <span className="text-muted-foreground">Market Max:</span>
                                          <span className="text-red-600">{formatCurrency(category.competitor_max)}</span>
                                        </div>
                                      </div>
                                    </div>
                                    <div className="space-y-4">
                                      <h4 className="font-medium">Market Insights</h4>
                                      <div className="space-y-3">
                                        {category.opportunity > 0 && (
                                          <Alert className="border-green-200 bg-green-50">
                                            <TrendingUp className="h-4 w-4" />
                                            <AlertDescription className="text-green-800">
                                              <div className="font-medium mb-1">Pricing Opportunity</div>
                                              <div className="text-sm">
                                                You could potentially increase prices by <strong>{formatPercent(category.opportunity)}</strong> 
                                                while remaining competitive in this category.
                                              </div>
                                            </AlertDescription>
                                          </Alert>
                                        )}
                                        
                                        {category.market_position === 'above' && (
                                          <Alert className="border-red-200 bg-red-50">
                                            <AlertTriangle className="h-4 w-4" />
                                            <AlertDescription className="text-red-800">
                                              <div className="font-medium mb-1">Above Market Range</div>
                                              <div className="text-sm">
                                                Your products are priced above the market median. Consider market positioning strategy.
                                              </div>
                                            </AlertDescription>
                                          </Alert>
                                        )}
                                        
                                        {category.market_position === 'competitive' && (
                                          <Alert className="border-blue-200 bg-blue-50">
                                            <CheckCircle className="h-4 w-4" />
                                            <AlertDescription className="text-blue-800">
                                              <div className="font-medium mb-1">Competitively Positioned</div>
                                              <div className="text-sm">
                                                Your products are well-positioned within the market range.
                                              </div>
                                            </AlertDescription>
                                          </Alert>
                                        )}
                                        
                                        <div className="text-sm text-muted-foreground">
                                          <div><strong>Portfolio:</strong> {category.products} products</div>
                                          <div><strong>Market Data:</strong> {category.competitor_data_points} competitor prices</div>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                </DialogContent>
                              </Dialog>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      {categoryAnalysis.length > 0 
                        ? "No categories match your current filters."
                        : "No category analysis data available. Run a scraping operation to get competitor data."
                      }
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Stores Tab */}
            <TabsContent value="stores" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Competitor Store Analysis</CardTitle>
                  <CardDescription>
                    Compare pricing strategies across different competitor stores
                  </CardDescription>
                  <div className="text-sm text-muted-foreground">
                    Debug: Stores found: {storeAnalysis.map(s => s.store).join(', ')}
                  </div>
                </CardHeader>
                <CardContent>
                  {storeAnalysis.length > 0 ? (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Store</TableHead>
                          <TableHead>Avg Price</TableHead>
                          <TableHead>Price Range</TableHead>
                          <TableHead>Products</TableHead>
                          <TableHead>Overlap</TableHead>
                          <TableHead>Positioning</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {storeAnalysis.map((store, index) => (
                          <TableRow key={index}>
                            <TableCell className="font-medium">{store.store}</TableCell>
                            <TableCell>{formatCurrency(store.avg_price)}</TableCell>
                            <TableCell>{store.price_range}</TableCell>
                            <TableCell>{store.products}</TableCell>
                            <TableCell>
                              <div>
                                <span className="font-medium">{store.overlap}</span>
                                <span className="text-sm text-muted-foreground ml-1">
                                  ({formatPercent(store.overlap_percent)})
                                </span>
                              </div>
                            </TableCell>
                            <TableCell>
                              {getPositioningBadge(store.positioning)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No store analysis data available. Run a scraping operation to get competitor data.
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Price Gaps Tab */}
            <TabsContent value="gaps" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Price Gap Analysis</CardTitle>
                  <CardDescription>
                    Detailed price gaps will be available after running price optimization
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8 text-muted-foreground">
                    <Target className="mx-auto h-12 w-12 mb-4" />
                    <h3 className="text-lg font-medium mb-2">Price Gap Analysis</h3>
                    <p className="mb-4">Run price optimization to see detailed gap analysis for individual products.</p>
                    <Button asChild>
                      <a href="/pricing-recommendations">Go to Price Recommendations</a>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
    </AppLayout>
  );
}