import React, { useState, useEffect } from 'react';
import { ShoppingBag, RefreshCw, AlertCircle, Search, Filter } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useProducts } from '@/hooks/useApi';
import { useToast } from '@/hooks/useToast';
import { formatCurrency, debounce } from '@/lib/utils';
import { Product } from '@/types';

const ProductsTab: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredProducts, setFilteredProducts] = useState<Product[]>([]);
  
  const { getProducts, loading, error } = useProducts();
  const { error: showError } = useToast();

  const debouncedSearch = debounce((query: string) => {
    if (!query.trim()) {
      setFilteredProducts(products);
      return;
    }

    const filtered = products.filter(product => 
      product.title.toLowerCase().includes(query.toLowerCase()) ||
      product.description.toLowerCase().includes(query.toLowerCase()) ||
      product.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
    );
    setFilteredProducts(filtered);
  }, 300);

  useEffect(() => {
    debouncedSearch(searchQuery);
  }, [searchQuery, products, debouncedSearch]);

  const loadProducts = async () => {
    try {
      const response = await getProducts('', 50);
      if (response.success && response.data) {
        const productData = response.data.products || [];
        setProducts(productData);
        setFilteredProducts(productData);
      }
    } catch (err) {
      console.error('Failed to load products:', err);
      showError('Failed to load products. Please try again.');
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const handleRefresh = () => {
    loadProducts();
  };

  const getAvailabilityBadge = (product: Product) => {
    if (product.available) {
      return (
        <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
          In Stock
        </Badge>
      );
    }
    return (
      <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
        Out of Stock
      </Badge>
    );
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-white">Shopify Products</h2>
          <p className="text-white/70">Products available through the AI assistant</p>
        </div>
        
        <Button
          onClick={handleRefresh}
          disabled={loading}
          className="btn-feelori"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Search and Filters */}
      <Card className="glass-card">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/50" />
              <Input
                placeholder="Search products..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input-feelori pl-10"
              />
            </div>
            <Button variant="outline" className="border-white/20 text-white hover:bg-white/10">
              <Filter className="w-4 h-4 mr-2" />
              Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Error State */}
      {error && (
        <Card className="glass-card border-red-500/30">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 text-red-400">
              <AlertCircle className="w-5 h-5" />
              <span>Error loading products: {error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" text="Loading products..." />
        </div>
      )}

      {/* Products Grid */}
      {!loading && filteredProducts.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredProducts.map((product) => (
            <Card key={product.id} className="card-feelori group">
              {/* Product Image */}
              {product.images && product.images.length > 0 && (
                <div className="aspect-square overflow-hidden rounded-t-2xl">
                  <img
                    src={product.images[0]}
                    alt={product.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                </div>
              )}
              
              <CardContent className="p-6 space-y-4">
                <div>
                  <h3 className="text-white font-semibold text-lg mb-2 line-clamp-2">
                    {product.title}
                  </h3>
                  <p className="text-feelori-primary text-xl font-bold">
                    {formatCurrency(product.price)}
                  </p>
                </div>

                <p className="text-white/70 text-sm line-clamp-3">
                  {product.description.replace(/<[^>]*>/g, '')}
                </p>

                <div className="flex items-center justify-between">
                  {getAvailabilityBadge(product)}
                  
                  {product.tags.length > 0 && (
                    <div className="flex gap-1">
                      {product.tags.slice(0, 2).map((tag, index) => (
                        <Badge
                          key={index}
                          variant="outline"
                          className="text-xs border-white/20 text-white/60"
                        >
                          {tag.trim()}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>

                {product.variants && product.variants.length > 0 && (
                  <div className="text-white/60 text-xs">
                    {product.variants.length} variant(s) available
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && filteredProducts.length === 0 && (
        <Card className="glass-card">
          <CardContent className="p-12 text-center space-y-4">
            <div className="flex justify-center">
              <div className="p-4 bg-white/10 rounded-full">
                <ShoppingBag className="w-12 h-12 text-white/40" />
              </div>
            </div>
            <h3 className="text-white text-xl font-semibold">
              {searchQuery ? 'No products found' : 'No products available'}
            </h3>
            <p className="text-white/60 max-w-md mx-auto">
              {searchQuery 
                ? `No products match "${searchQuery}". Try adjusting your search terms.`
                : 'Check your Shopify connection or add some products to your store.'
              }
            </p>
            {searchQuery && (
              <Button
                onClick={() => setSearchQuery('')}
                variant="outline"
                className="border-white/20 text-white hover:bg-white/10"
              >
                Clear Search
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ProductsTab;