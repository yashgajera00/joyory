import React, { useState } from 'react';
import { BagIcon, ShieldCheckIcon } from './Icons';
import { formatRupees } from '@/lib/utils';

export default function ProductCard({ product, onSelectProduct, onAddToCart, showCategory = true }) {
  const [adding, setAdding] = useState(false);

  const handleQuickAdd = async (e) => {
    e.stopPropagation();
    setAdding(true);
    try {
      await onAddToCart(product.id, 1);
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="product-card" onClick={() => onSelectProduct(product.id)}>
      {/* Top Badges */}
      {showCategory && (
        <div className="product-card-badges">
          <span className="category-pill">{product.category_display || product.category}</span>
        </div>
      )}

      {/* Product Image */}
      <div className="product-visual-box">
        <img
          src={product.image_url || `/images/products/product_${product.id}.jpg`}
          alt={product.name}
          className="product-card-img"
          loading="lazy"
          onError={(e) => {
            const prodFallback = `/images/products/product_${product.id}.jpg`;
            const catFallback = `/images/products/${product.category}.jpg`;
            if (e.target.src.indexOf(`product_${product.id}.jpg`) === -1) {
              e.target.src = prodFallback;
            } else if (e.target.src.indexOf(`${product.category}.jpg`) === -1) {
              e.target.src = catFallback;
            }
          }}
        />
      </div>

      {/* Product Info */}
      <div className="product-card-body">
        <h3 className="product-title">{product.name}</h3>
        <p className="product-texture-tag">
          Texture: <strong>{product.texture_display || product.texture}</strong> &bull; Climate: <strong>{product.climate_display || product.suitable_climate}</strong>
        </p>

        {/* Key Ingredients */}
        {product.ingredients && product.ingredients.length > 0 && (
          <div className="product-ingredients-preview">
            {product.ingredients.slice(0, 3).map((ing) => (
              <span key={ing.id} className="ingredient-tag">
                {ing.name}
              </span>
            ))}
            {product.ingredients.length > 3 && (
              <span className="ingredient-tag-more">+{product.ingredients.length - 3}</span>
            )}
          </div>
        )}

        {/* Card Footer: Price & Add */}
        <div className="product-card-footer">
          <div className="product-price">{formatRupees(product.price)}</div>
          <button
            className="btn-quick-add"
            onClick={handleQuickAdd}
            disabled={adding}
            title="Add to cart"
          >
            <BagIcon size={16} />
            <span>{adding ? 'Adding...' : 'Add'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
