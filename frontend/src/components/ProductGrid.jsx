import React, { useState, useEffect } from 'react';
import ProductCard from './ProductCard';
import { SearchIcon, SparklesIcon } from './Icons';
import { fetchProducts } from '../services/api';

// Category photo assets
import allImg from '../assets/all.png';
import cleansersImg from '../assets/cleansers.png';
import exfoliantsImg from '../assets/exfoliants.png';
import moisturizersImg from '../assets/moisturizers.png';
import serumsImg from '../assets/serums.png';
import sunscreensImg from '../assets/sunscreens.png';
import tonersImg from '../assets/toners.png';

const CATEGORIES = [
  { id: 'all', label: 'All Essentials', image: allImg },
  { id: 'cleanser', label: 'Cleansers', image: cleansersImg },
  { id: 'toner', label: 'Toners', image: tonersImg },
  { id: 'serum', label: 'Serums', image: serumsImg },
  { id: 'exfoliant', label: 'Exfoliants', image: exfoliantsImg },
  { id: 'moisturizer', label: 'Moisturizers', image: moisturizersImg },
  { id: 'sunscreen', label: 'Sunscreens', image: sunscreensImg },
];

const CLIMATES = [
  { id: 'all', label: 'All Climates' },
  { id: 'hot_humid', label: 'Hot & Humid' },
  { id: 'hot_dry', label: 'Hot & Dry' },
  { id: 'cold_dry', label: 'Cold & Dry' },
];

export default function ProductGrid({ onSelectProduct, onAddToCart, initialCategory = 'all', onSelectCategory }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [category, setCategory] = useState(initialCategory || 'all');
  const [climate, setClimate] = useState('all');
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (initialCategory) {
      setCategory(initialCategory);
    }
  }, [initialCategory]);

  const loadProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProducts({ category, climate, search });
      setProducts(Array.isArray(data) ? data : (data?.results || []));
    } catch (err) {
      setError(err.message || 'Unable to load products. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, [category, climate]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadProducts();
  };

  return (
    <section className="catalog-section">
      {/* All 7 Category Image Links in One Single Line */}
      <div className="catalog-categories-strip">
        {CATEGORIES.map((cat) => (
          <div
            key={cat.id}
            className={`cat-image-wrapper ${category === cat.id ? 'active' : ''}`}
            onClick={() => {
              setCategory(cat.id);
              if (onSelectCategory) onSelectCategory(cat.id);
            }}
            title={cat.label}
            aria-label={cat.label}
          >
            <img
              src={cat.image}
              alt={cat.label}
              className="cat-image-link"
              loading="lazy"
            />
          </div>
        ))}
      </div>

      {/* Search Bar & Climate Filter Bar Directly Above Product List */}
      <div className="catalog-controls">
        <form className="search-form" onSubmit={handleSearchSubmit}>
          <SearchIcon size={18} className="search-icon" />
          <input
            type="text"
            placeholder="Search by product name, ingredient..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="search-input"
          />
        </form>

        <div className="climate-filter-wrapper">
          <label htmlFor="climate-select" className="filter-label">Climate Focus:</label>
          <select
            id="climate-select"
            value={climate}
            onChange={(e) => setClimate(e.target.value)}
            className="custom-select"
          >
            {CLIMATES.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* States: Loading, Error, Empty, List */}
      {loading ? (
        <div className="products-grid-skeleton">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="skeleton-card"></div>
          ))}
        </div>
      ) : error ? (
        <div className="error-box">
          <p className="error-title">Error Loading Catalog</p>
          <p className="error-desc">{error}</p>
          <button className="btn-retry" onClick={loadProducts}>
            Retry
          </button>
        </div>
      ) : products.length === 0 ? (
        <div className="empty-catalog-box">
          <SparklesIcon size={32} />
          <h3>No matching formulas found</h3>
          <p>Try clearing your category filter or search keywords to see all products.</p>
          <button
            className="btn-secondary"
            onClick={() => {
              setCategory('all');
              setClimate('all');
              setSearch('');
            }}
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="products-grid">
          {products.map((p) => (
            <ProductCard
              key={p.id}
              product={p}
              showCategory={category === 'all'}
              onSelectProduct={onSelectProduct}
              onAddToCart={onAddToCart}
            />
          ))}
        </div>
      )}
    </section>
  );
}
