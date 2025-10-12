"use client";

import { useState, useEffect } from "react";
import { AppLayout } from "@/components/app-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { 
  Target, 
  TrendingUp, 
  TrendingDown,
  Download,
  Filter,
  Brain,
  Calculator,
  AlertTriangle,
  CheckCircle,
  Info,
  Zap,
  Loader2,
  AlertCircle
} from "lucide-react";
import { usePriceOptimization } from "@/lib/hooks";
import { formatters, handleApiError } from "@/lib/api";

interface ExtendedPriceRecommendation {
  product_id: string;
  current_price: number;
  recommended_price: number;
  price_change_percent: number;
  expected_profit_change: number;
  risk_level: "low" | "medium" | "high";
  confidence_score: number;
  scenarios: {
    conservative: { price: number; expected_margin: number };
    recommended: { price: number; expected_margin: number };
    aggressive: { price: number; expected_margin: number };
  };
  rationale: string;
  rationale_sections?: {
    competitive_analysis?: string;
    llm_insights?: string;
  };
  constraint_flags: string[];
}

export default function PricingRecommendationsPage() {
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedRisk, setSelectedRisk] = useState("all");
  const [minConfidence, setMinConfidence] = useState("0");
  const [enablePsychologicalPricing, setEnablePsychologicalPricing] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<typeof recommendations[0] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [useCache, setUseCache] = useState(true);
  const [cacheMaxAge, setCacheMaxAge] = useState(24);

  const { recommendations, loading, optimizeBatch, getCachedRecommendations, cacheInfo } = usePriceOptimization();

  useEffect(() => {
    // Load initial recommendations when component mounts
    const loadRecommendations = async () => {
      try {
        setError(null);
        if (useCache) {
          // Try to load from cache first
          const cachedResult = await getCachedRecommendations(cacheMaxAge);
          if (cachedResult.recommendations.length === 0) {
            // No cache, fallback to fresh optimization
            await optimizeBatch(undefined, {
              min_margin_percent: 30,
              max_price_increase_percent: 25,
              psychological_pricing: enablePsychologicalPricing
            }, false); // Force fresh optimization
          }
        } else {
          // Fresh optimization
          await optimizeBatch(undefined, {
            min_margin_percent: 30,
            max_price_increase_percent: 25,
            psychological_pricing: enablePsychologicalPricing
          }, false);
        }
      } catch (err) {
        setError(handleApiError(err));
      }
    };

    loadRecommendations();
  }, [optimizeBatch, getCachedRecommendations, enablePsychologicalPricing, useCache, cacheMaxAge]);

  const runBatchOptimization = async (forceRefresh: boolean = false) => {
    try {
      setError(null);
      await optimizeBatch(undefined, {
        min_margin_percent: 30,
        max_price_increase_percent: 25,
        psychological_pricing: enablePsychologicalPricing
      }, !forceRefresh && useCache, cacheMaxAge);
    } catch (err) {
      setError(handleApiError(err));
    }
  };

  const getRiskBadgeVariant = (risk: string) => {
    switch (risk) {
      case "low": return "default";
      case "medium": return "secondary";
      case "high": return "destructive";
      default: return "outline";
    }
  };

  const getRiskIcon = (risk: string) => {
    switch (risk) {
      case "low": return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "medium": return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case "high": return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default: return <Info className="h-4 w-4" />;
    }
  };

  const filteredRecommendations = recommendations.filter(rec => {
    // Get category from product_id or use a mapping - for now just check if it matches
    const categoryMatch = selectedCategory === "all" || 
      rec.product_id.toLowerCase().includes(selectedCategory.toLowerCase()) ||
      (selectedCategory === "sunglasses" && rec.product_id.includes("SUN")) ||
      (selectedCategory === "bottles" && rec.product_id.includes("BOT")) ||
      (selectedCategory === "notebooks" && rec.product_id.includes("NOTE")) ||
      (selectedCategory === "bags" && rec.product_id.includes("BAG"));
    
    if (!categoryMatch) return false;
    if (selectedRisk !== "all" && rec.risk_level !== selectedRisk) return false;
    if (rec.confidence_score < parseFloat(minConfidence)) return false;
    return true;
  });

  if (loading && recommendations.length === 0) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>Generating pricing recommendations...</span>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Pricing Recommendations
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-300">
          AI-powered pricing optimization with scenario analysis
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <span className="text-red-800 font-medium">Error</span>
          </div>
          <p className="text-red-700 mt-1">{error}</p>
        </div>
      )}

      {/* Cache Status */}
      {cacheInfo && cacheInfo.cached_products > 0 && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Info className="h-5 w-5 text-blue-600" />
              <span className="text-blue-800 font-medium">Using Cached Recommendations</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => runBatchOptimization(true)}
              disabled={loading}
            >
              <Zap className="mr-2 h-4 w-4" />
              Refresh All
            </Button>
          </div>
          <p className="text-blue-700 mt-1">
            Showing {cacheInfo.cached_products} cached recommendations. 
            Cache age: up to {cacheInfo.cache_age_hours} hours.
            {cacheInfo.newest_cache && (
              <> Latest update: {new Date(cacheInfo.newest_cache).toLocaleString()}</>
            )}
          </p>
        </div>
      )}

          {/* Controls */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center">
                  <Calculator className="mr-2 h-5 w-5" />
                  Optimization Controls
                </div>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <Brain className="h-4 w-4" />
                    <Label htmlFor="psychological-pricing-toggle">Psychological Pricing</Label>
                    <Switch id="psychological-pricing-toggle" checked={enablePsychologicalPricing} onCheckedChange={setEnablePsychologicalPricing} />
                  </div>
                  <div className="flex items-center space-x-2">
                    <Target className="h-4 w-4" />
                    <Label htmlFor="cache-toggle">Use Cache</Label>
                    <Switch id="cache-toggle" checked={useCache} onCheckedChange={setUseCache} />
                  </div>
                  {useCache && (
                    <div className="flex items-center space-x-2">
                      <Label className="text-sm">Max Age:</Label>
                      <Select value={cacheMaxAge.toString()} onValueChange={(value) => setCacheMaxAge(parseInt(value))}>
                        <SelectTrigger className="w-20">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1">1h</SelectItem>
                          <SelectItem value="6">6h</SelectItem>
                          <SelectItem value="24">24h</SelectItem>
                          <SelectItem value="72">72h</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <Label className="text-sm font-medium mb-2 block">Category</Label>
                  <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Categories</SelectItem>
                      <SelectItem value="sunglasses">Sunglasses</SelectItem>
                      <SelectItem value="bottles">Bottles</SelectItem>
                      <SelectItem value="notebooks">Notebooks</SelectItem>
                      <SelectItem value="bags">Bags</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label className="text-sm font-medium mb-2 block">Risk Level</Label>
                  <Select value={selectedRisk} onValueChange={setSelectedRisk}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select risk" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Risk Levels</SelectItem>
                      <SelectItem value="low">Low Risk</SelectItem>
                      <SelectItem value="medium">Medium Risk</SelectItem>
                      <SelectItem value="high">High Risk</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-sm font-medium mb-2 block">Min Confidence</Label>
                  <Select value={minConfidence} onValueChange={setMinConfidence}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select confidence" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0">Any (0%)</SelectItem>
                      <SelectItem value="0.5">Medium (50%)</SelectItem>
                      <SelectItem value="0.7">High (70%)</SelectItem>
                      <SelectItem value="0.8">Very High (80%)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-end">
                  <Button 
                    onClick={() => runBatchOptimization()}
                    disabled={loading}
                    className="w-full"
                  >
                    {loading ? (
                      <>
                        <Target className="mr-2 h-4 w-4 animate-spin" />
                        Optimizing...
                      </>
                    ) : (
                      <>
                        <Target className="mr-2 h-4 w-4" />
                        {useCache ? 'Load/Optimize' : 'Fresh Optimization'}
                      </>
                    )}
                  </Button>
                </div>
              </div>

              <div className="flex space-x-2">
                <Button variant="outline" size="sm">
                  <Download className="mr-2 h-4 w-4" />
                  Export CSV
                </Button>
                <Button variant="outline" size="sm">
                  <Filter className="mr-2 h-4 w-4" />
                  Advanced Filters
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardHeader className="flex flex-row items-center space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Products</CardTitle>
                <Target className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{filteredRecommendations.length}</div>
                <p className="text-xs text-muted-foreground">
                  With recommendations
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Price Increase</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {filteredRecommendations.length > 0 
                    ? formatters.percentage(filteredRecommendations.reduce((acc, rec) => acc + rec.price_change_percent, 0) / filteredRecommendations.length)
                    : '0%'
                  }
                </div>
                <p className="text-xs text-muted-foreground">
                  Recommended adjustment
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Uplift</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {formatters.currency(filteredRecommendations.reduce((acc, rec) => acc + rec.expected_profit_change, 0))}
                </div>
                <p className="text-xs text-muted-foreground">
                  Monthly potential
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
                <Brain className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {filteredRecommendations.length > 0
                    ? Math.round(filteredRecommendations.reduce((acc, rec) => acc + rec.confidence_score, 0) / filteredRecommendations.length * 100)
                    : 0
                  }%
                </div>
                <p className="text-xs text-muted-foreground">
                  Model confidence
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Recommendations Table */}
          <Card>
            <CardHeader>
              <CardTitle>Price Recommendations</CardTitle>
              <CardDescription>
                Optimized pricing suggestions based on competitive analysis and AI insights
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Product</TableHead>
                    <TableHead>Current Price</TableHead>
                    <TableHead>Recommended Price</TableHead>
                    <TableHead>Change</TableHead>
                    <TableHead>Monthly Uplift</TableHead>
                    <TableHead>Risk</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRecommendations.length > 0 ? (
                    filteredRecommendations.map((rec) => (
                      <TableRow key={rec.product_id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{rec.product_id}</div>
                            <div className="text-sm text-muted-foreground">Product ID</div>
                          </div>
                        </TableCell>
                        <TableCell>{formatters.currency(rec.current_price)}</TableCell>
                        <TableCell className="font-medium">
                          {formatters.currency(rec.recommended_price)}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center">
                            {rec.price_change_percent > 0 ? (
                              <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
                            ) : (
                              <TrendingDown className="h-4 w-4 text-red-600 mr-1" />
                            )}
                            <span className={rec.price_change_percent > 0 ? "text-green-600" : "text-red-600"}>
                              {formatters.percentage(rec.price_change_percent)}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-green-600 font-medium">
                          {formatters.currency(rec.expected_profit_change)}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-1">
                            {getRiskIcon(rec.risk_level)}
                            <Badge variant={getRiskBadgeVariant(rec.risk_level)}>
                              {rec.risk_level}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center">
                            <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full" 
                                style={{ width: `${rec.confidence_score * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-sm">{formatters.confidence(rec.confidence_score)}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button variant="outline" size="sm" onClick={() => setSelectedProduct(rec)}>
                                View Details
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-2xl">
                              <DialogHeader>
                                <DialogTitle>{rec.product_id}</DialogTitle>
                                <DialogDescription>
                                  Detailed pricing recommendation and scenario analysis
                                </DialogDescription>
                              </DialogHeader>
                              {selectedProduct && (
                                <div className="space-y-6">
                                  {/* Current vs Recommended */}
                                  <div className="grid grid-cols-2 gap-4">
                                    <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded">
                                      <div className="text-2xl font-bold">{formatters.currency(selectedProduct.current_price)}</div>
                                      <div className="text-sm text-muted-foreground">Current Price</div>
                                    </div>
                                    <div className="text-center p-4 bg-blue-50 dark:bg-blue-900 rounded">
                                      <div className="text-2xl font-bold text-blue-600">{formatters.currency(selectedProduct.recommended_price)}</div>
                                      <div className="text-sm text-muted-foreground">Recommended Price</div>
                                    </div>
                                  </div>

                                  {/* Scenarios */}
                                  <div>
                                    <h4 className="font-medium mb-3">Pricing Scenarios</h4>
                                    <div className="grid grid-cols-3 gap-4">
                                      <div className="text-center p-3 border rounded">
                                        <div className="font-bold">{formatters.currency(selectedProduct.scenarios.conservative.price)}</div>
                                        <div className="text-sm text-muted-foreground">Conservative</div>
                                        <div className="text-xs text-green-600">{formatters.percentage(selectedProduct.scenarios.conservative.expected_margin)} margin</div>
                                      </div>
                                      <div className="text-center p-3 border rounded bg-blue-50 dark:bg-blue-900">
                                        <div className="font-bold text-blue-600">{formatters.currency(selectedProduct.scenarios.recommended.price)}</div>
                                        <div className="text-sm text-muted-foreground">Recommended</div>
                                        <div className="text-xs text-green-600">{formatters.percentage(selectedProduct.scenarios.recommended.expected_margin)} margin</div>
                                      </div>
                                      <div className="text-center p-3 border rounded">
                                        <div className="font-bold">{formatters.currency(selectedProduct.scenarios.aggressive.price)}</div>
                                        <div className="text-sm text-muted-foreground">Aggressive</div>
                                        <div className="text-xs text-green-600">{formatters.percentage(selectedProduct.scenarios.aggressive.expected_margin)} margin</div>
                                      </div>
                                    </div>
                                  </div>

                                  {/* Rationale */}
                                  <div>
                                    <h4 className="font-medium mb-2">AI Rationale</h4>
                                    <div className="space-y-3">
                                      {/* Competitive Analysis */}
                                      <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded border-l-4 border-blue-400">
                                        <h5 className="font-medium text-blue-900 dark:text-blue-100 mb-1">Competitive Analysis</h5>
                                        <p className="text-sm text-blue-800 dark:text-blue-200">
                                          {(selectedProduct as ExtendedPriceRecommendation).rationale_sections?.competitive_analysis || 
                                           selectedProduct.rationale.split(';').slice(0, 3).join('; ')}
                                        </p>
                                      </div>
                                      
                                      {/* LLM Insights */}
                                      {((selectedProduct as ExtendedPriceRecommendation).rationale_sections?.llm_insights || 
                                        selectedProduct.rationale.includes('LLM analysis')) && (
                                        <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded border-l-4 border-purple-400">
                                          <h5 className="font-medium text-purple-900 dark:text-purple-100 mb-1">AI Insights</h5>
                                          <p className="text-sm text-purple-800 dark:text-purple-200">
                                            {(selectedProduct as ExtendedPriceRecommendation).rationale_sections?.llm_insights || 
                                             selectedProduct.rationale.split(';').slice(3).join('; ')}
                                          </p>
                                        </div>
                                      )}
                                      
                                      {/* Fallback for simple rationale */}
                                      {!(selectedProduct as ExtendedPriceRecommendation).rationale_sections && !selectedProduct.rationale.includes('LLM analysis') && (
                                        <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded">
                                          <p className="text-sm text-muted-foreground">
                                            {selectedProduct.rationale}
                                          </p>
                                        </div>
                                      )}
                                    </div>
                                  </div>

                                  {/* Constraints */}
                                  <div>
                                    <h4 className="font-medium mb-2">Applied Constraints</h4>
                                    <div className="flex flex-wrap gap-2">
                                      {selectedProduct.constraint_flags.map((flag: string, index: number) => (
                                        <Badge key={index} variant="outline">
                                          {flag.replace('_', ' ')}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              )}
                            </DialogContent>
                          </Dialog>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                        {loading ? 'Generating recommendations...' : 'No recommendations available. Try running optimization.'}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
    </AppLayout>
  );
}