"use client";

import { useState, useEffect } from "react";
import { AppLayout } from "@/components/app-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Progress } from "@/components/ui/progress";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Play, 
  Square, 
  Download, 
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Loader2,
  Search,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Eye
} from "lucide-react";
import { useScrapingRun, useScrapingResults } from "@/lib/hooks";
import { handleApiError, scrapingApi } from "@/lib/api";

export default function ScrapingPage() {
  const [selectedCategories, setSelectedCategories] = useState("all");
  const [selectedStores, setSelectedStores] = useState("all");
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previousStatus, setPreviousStatus] = useState<string | null>(null);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  
  // Pagination and filtering state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);
  const [searchTerm, setSearchTerm] = useState("");
  const [storeFilter, setStoreFilter] = useState("all");
  const [matchFilter, setMatchFilter] = useState("all");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const { run, loading: runLoading, startScraping, stopScraping, fetchProgress } = useScrapingRun(currentRunId || undefined);
  const { results, loading: resultsLoading, exportResults, fetchResults } = useScrapingResults(currentRunId || undefined);

  // Load latest run on mount
  useEffect(() => {
    const loadLatestRun = async () => {
      try {
        const latestRun = await scrapingApi.getLatestRun();
        if (latestRun?.id) {
          console.log('Loaded latest run:', latestRun.id, 'Status:', latestRun.status);
          setCurrentRunId(latestRun.id);
        }
      } catch (err) {
        console.error('Failed to load latest run:', err);
      } finally {
        setIsInitialLoad(false);
      }
    };
    loadLatestRun();
  }, []);

  // Poll for progress when run is active
  useEffect(() => {
    if (currentRunId && run?.status === 'running') {
      const interval = setInterval(() => {
        fetchProgress(currentRunId);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [currentRunId, run?.status, fetchProgress]);

  // Poll for results while run is in progress
  useEffect(() => {
    if (currentRunId && run?.status === 'running') {
      // Fetch results immediately
      fetchResults(currentRunId);
      
      // Then poll every 5 seconds
      const interval = setInterval(() => {
        fetchResults(currentRunId);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [currentRunId, run?.status, fetchResults]);

  // Fetch results when run status changes to 'completed'
  useEffect(() => {
    if (currentRunId && run?.status === 'completed' && previousStatus !== 'completed') {
      console.log(`Run ${currentRunId} completed, fetching final results...`);
      fetchResults(currentRunId);
    }
    if (run?.status) {
      setPreviousStatus(run.status);
    }
  }, [currentRunId, run?.status, previousStatus, fetchResults]);

  const handleStartScraping = async () => {
    try {
      setError(null);
      setPreviousStatus(null);
      const targetProducts = selectedCategories === "all" ? undefined : [selectedCategories];
      const stores = selectedStores === "all" ? undefined : [selectedStores];
      
      const runId = await startScraping(targetProducts, stores);
      setCurrentRunId(runId);
    } catch (err) {
      setError(handleApiError(err));
    }
  };

  const handleStopScraping = async () => {
    if (!currentRunId) return;
    
    try {
      setError(null);
      await stopScraping(currentRunId);
    } catch (err) {
      setError(handleApiError(err));
    }
  };

  const handleExportResults = async () => {
    if (currentRunId) {
      try {
        await exportResults(currentRunId);
      } catch (err) {
        setError(handleApiError(err));
      }
    }
  };

  const handleRefreshResults = async () => {
    if (currentRunId) {
      try {
        setError(null);
        await fetchResults(currentRunId);
      } catch (err) {
        setError(handleApiError(err));
      }
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "running": return <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />;
      case "failed": return <XCircle className="h-4 w-4 text-red-600" />;
      case "stopped": return <Square className="h-4 w-4 text-orange-600" />;
      case "pending": return <Clock className="h-4 w-4 text-gray-400" />;
      default: return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case "completed": return "default";
      case "running": return "secondary";
      case "failed": return "destructive";
      case "stopped": return "outline";
      default: return "outline";
    }
  };

  const progress = run && run.stores_total > 0 ? (run.stores_completed / run.stores_total) * 100 : 0;

  // Filter and sort results
  const filteredResults = results.filter(product => {
    const matchesSearch = searchTerm === "" || 
      product.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.store_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (product.brand && product.brand.toLowerCase().includes(searchTerm.toLowerCase())) ||
      product.search_term.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStore = storeFilter === "all" || product.store_name === storeFilter;
    
    const matchesMatchFilter = matchFilter === "all" || 
      (matchFilter === "matched" && product.matched_catalog_id) ||
      (matchFilter === "unmatched" && !product.matched_catalog_id);
    
    return matchesSearch && matchesStore && matchesMatchFilter;
  }).sort((a, b) => {
    let aValue: string | number | Date, bValue: string | number | Date;
    
    switch (sortBy) {
      case "store_name":
        aValue = a.store_name;
        bValue = b.store_name;
        break;
      case "title":
        aValue = a.title;
        bValue = b.title;
        break;
      case "price":
        aValue = a.price;
        bValue = b.price;
        break;
      case "created_at":
      default:
        aValue = new Date(a.created_at);
        bValue = new Date(b.created_at);
        break;
    }
    
    if (sortOrder === "asc") {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  // Pagination
  const totalPages = Math.ceil(filteredResults.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedResults = filteredResults.slice(startIndex, startIndex + itemsPerPage);
  
  // Get unique stores for filter dropdown
  const uniqueStores = Array.from(new Set(results.map(r => r.store_name))).sort();
  
  // Reset pagination when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, storeFilter, matchFilter, sortBy, sortOrder]);

  return (
    <AppLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground">
          Competitor Price Scraping
        </h1>
        <p className="mt-2 text-muted-foreground">
          Collect and monitor competitor pricing data from eco-conscious brands
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <span className="text-destructive font-medium">Error</span>
          </div>
          <p className="text-destructive/90 mt-1">{error}</p>
        </div>
      )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Start New Scrape */}
            <Card className="h-fit">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Play className="h-5 w-5 text-primary" />
                  Start New Scraping Run
                </CardTitle>
                <CardDescription>
                  Configure and launch a new competitor price collection
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="categories" className="text-sm font-medium">
                    Target Categories
                  </Label>
                  <Select value={selectedCategories} onValueChange={setSelectedCategories}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select categories to scrape" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Categories</SelectItem>
                      <SelectItem value="sunglasses">Sunglasses</SelectItem>
                      <SelectItem value="bottles">Water Bottles</SelectItem>
                      <SelectItem value="notebooks">Notebooks</SelectItem>
                      <SelectItem value="bags">Bags</SelectItem>
                      <SelectItem value="apparel">Apparel</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="stores" className="text-sm font-medium">
                    Target Stores
                  </Label>
                  <Select value={selectedStores} onValueChange={setSelectedStores}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select stores to scrape" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Stores (15)</SelectItem>
                      <SelectItem value="madetrade">Made Trade</SelectItem>
                      <SelectItem value="earthhero">EarthHero</SelectItem>
                      <SelectItem value="goodee">GOODEE</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  onClick={handleStartScraping} 
                  disabled={runLoading || run?.status === "running"}
                  className="w-full"
                  size="lg"
                >
                  {runLoading ? (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      Start Scraping
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Current Run Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <RefreshCw className="h-5 w-5 text-primary" />
                  Current Run Status
                </CardTitle>
                <CardDescription>
                  Monitor the progress of your scraping operation
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {run ? (
                  <>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between py-2 border-b">
                        <span className="font-medium text-sm">Run ID:</span>
                        <Badge variant="outline" className="font-mono text-xs">{run.id}</Badge>
                      </div>
                      
                      <div className="flex items-center justify-between py-2 border-b">
                        <span className="font-medium text-sm">Status:</span>
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(run.status)}
                          <Badge variant={getStatusBadgeVariant(run.status)}>
                            {run.status}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    {run.status === "running" && (
                      <div className="space-y-3 p-4 bg-muted/50 rounded-lg">
                        <div className="flex justify-between text-sm">
                          <span className="font-medium">Progress</span>
                          <span className="text-muted-foreground">{run.stores_completed} / {run.stores_total} stores</span>
                        </div>
                        <Progress value={progress} className="h-2" />
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-4 bg-primary/10 rounded-lg border border-primary/20">
                        <div className="text-2xl font-bold text-primary">{run.products_found}</div>
                        <div className="text-sm text-muted-foreground">Products Found</div>
                      </div>
                      <div className="text-center p-4 bg-muted/50 rounded-lg">
                        <div className="text-2xl font-bold">{run.stores_completed}</div>
                        <div className="text-sm text-muted-foreground">Stores Done</div>
                      </div>
                    </div>

                    {run.status === "running" && (
                      <Button 
                        variant="outline" 
                        className="w-full"
                        onClick={handleStopScraping}
                        disabled={runLoading}
                      >
                        {runLoading ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Stopping...
                          </>
                        ) : (
                          <>
                            <Square className="mr-2 h-4 w-4" />
                            Stop Scraping
                          </>
                        )}
                      </Button>
                    )}
                  </>
                ) : (
                  <div className="text-center py-8">
                    <div className="text-muted-foreground mb-4">
                      <Clock className="h-12 w-12 mx-auto mb-3 text-muted-foreground/50" />
                      <p>No active scraping run</p>
                      <p className="text-sm">Start one to see progress here</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Results */}
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Eye className="h-5 w-5 text-primary" />
                    Scraped Products
                    {filteredResults.length > 0 && (
                      <Badge variant="secondary" className="ml-2">
                        {filteredResults.length} results
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription>
                    Products collected from competitor stores with filtering and pagination
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleRefreshResults}
                    disabled={!currentRunId || resultsLoading}
                  >
                    {resultsLoading ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="mr-2 h-4 w-4" />
                    )}
                    Refresh
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleExportResults}
                    disabled={!currentRunId || results.length === 0}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Export CSV
                  </Button>
                </div>
              </div>
              
              {/* Filters and Search */}
              {results.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                  <div className="space-y-2">
                    <Label htmlFor="search" className="text-sm font-medium">Search</Label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="search"
                        placeholder="Search products, stores, brands..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-9"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="store-filter" className="text-sm font-medium">Store</Label>
                    <Select value={storeFilter} onValueChange={setStoreFilter}>
                      <SelectTrigger>
                        <SelectValue placeholder="Filter by store" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Stores</SelectItem>
                        {uniqueStores.map(store => (
                          <SelectItem key={store} value={store}>{store}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="match-filter" className="text-sm font-medium">Match Status</Label>
                    <Select value={matchFilter} onValueChange={setMatchFilter}>
                      <SelectTrigger>
                        <SelectValue placeholder="Filter by match" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Products</SelectItem>
                        <SelectItem value="matched">Matched Only</SelectItem>
                        <SelectItem value="unmatched">Unmatched Only</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="sort" className="text-sm font-medium">Sort By</Label>
                    <Select value={`${sortBy}-${sortOrder}`} onValueChange={(value) => {
                      const [field, order] = value.split('-');
                      setSortBy(field);
                      setSortOrder(order as 'asc' | 'desc');
                    }}>
                      <SelectTrigger>
                        <SelectValue placeholder="Sort options" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="created_at-desc">Newest First</SelectItem>
                        <SelectItem value="created_at-asc">Oldest First</SelectItem>
                        <SelectItem value="store_name-asc">Store A-Z</SelectItem>
                        <SelectItem value="store_name-desc">Store Z-A</SelectItem>
                        <SelectItem value="title-asc">Product A-Z</SelectItem>
                        <SelectItem value="title-desc">Product Z-A</SelectItem>
                        <SelectItem value="price-asc">Price Low-High</SelectItem>
                        <SelectItem value="price-desc">Price High-Low</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}
            </CardHeader>
            
            <CardContent>
              {resultsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin mr-2" />
                  <span>Loading results...</span>
                </div>
              ) : filteredResults.length > 0 ? (
                <div className="space-y-4">
                  {/* Results Table */}
                  <div className="border rounded-lg">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-[120px]">Store</TableHead>
                          <TableHead className="min-w-[300px]">Product</TableHead>
                          <TableHead className="w-[100px]">Brand</TableHead>
                          <TableHead className="w-[100px]">Price</TableHead>
                          <TableHead className="w-[150px]">Search Term</TableHead>
                          <TableHead className="w-[150px]">Match Status</TableHead>
                          <TableHead className="w-[80px]">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {paginatedResults.map((product, index) => (
                          <TableRow key={`${product.store_name}-${product.title}-${product.created_at}-${index}`}>
                            <TableCell className="font-medium">
                              <Badge variant="outline" className="text-xs">
                                {product.store_name}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="space-y-1">
                                <div className="font-medium text-sm leading-tight">
                                  {product.title}
                                </div>
                                {product.material && (
                                  <div className="text-xs text-muted-foreground">
                                    Material: {product.material}
                                  </div>
                                )}
                                {product.size && (
                                  <div className="text-xs text-muted-foreground">
                                    Size: {product.size}
                                  </div>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              {product.brand ? (
                                <Badge variant="secondary" className="text-xs">
                                  {product.brand}
                                </Badge>
                              ) : (
                                <span className="text-muted-foreground text-xs">-</span>
                              )}
                            </TableCell>
                            <TableCell>
                              <div className="font-semibold">
                                {product.currency}{product.price.toFixed(2)}
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className="text-xs font-mono">
                                {product.search_term}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {product.matched_catalog_id ? (
                                <Badge variant="default" className="text-xs">
                                  <CheckCircle className="mr-1 h-3 w-3" />
                                  {product.matched_catalog_id}
                                </Badge>
                              ) : (
                                <Badge variant="destructive" className="text-xs">
                                  <XCircle className="mr-1 h-3 w-3" />
                                  No match
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => window.open(product.product_url, '_blank')}
                                className="h-8 w-8 p-0"
                              >
                                <ExternalLink className="h-4 w-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  
                  {/* Pagination Controls */}
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <span>Show</span>
                      <Select value={itemsPerPage.toString()} onValueChange={(value) => {
                        setItemsPerPage(Number(value));
                        setCurrentPage(1);
                      }}>
                        <SelectTrigger className="w-20">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="10">10</SelectItem>
                          <SelectItem value="25">25</SelectItem>
                          <SelectItem value="50">50</SelectItem>
                          <SelectItem value="100">100</SelectItem>
                        </SelectContent>
                      </Select>
                      <span>of {filteredResults.length} results</span>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                        disabled={currentPage === 1}
                      >
                        <ChevronLeft className="h-4 w-4" />
                        Previous
                      </Button>
                      
                      <div className="flex items-center gap-1 text-sm">
                        <span>Page {currentPage} of {totalPages}</span>
                      </div>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                        disabled={currentPage === totalPages}
                      >
                        Next
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  {isInitialLoad ? (
                    'Loading...'
                  ) : currentRunId ? (
                    run?.status === 'running' ? 'Scraping in progress... Products will appear as they are found.' : 
                    searchTerm || storeFilter !== 'all' || matchFilter !== 'all' ? 'No products match your current filters.' :
                    'No products found in this run.'
                  ) : (
                    'Start a scraping run to see results here.'
                  )}
                </div>
              )}
            </CardContent>
          </Card>
    </AppLayout>
  );
}