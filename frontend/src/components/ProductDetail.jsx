import React, { useState, useEffect } from 'react';
import { fetchProductDetail, checkIngredientConflicts } from '../services/api';
import { BagIcon, ShieldCheckIcon, AlertTriangleIcon, ArrowRightIcon, DropletIcon, SunIcon } from './Icons';
import { formatRupees } from '@/lib/utils';

export default function ProductDetail({ productId, cartProductIds = [], onBack, onAddToCart, onGoToCart }) {
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [adding, setAdding] = useState(false);
  const [conflictPreview, setConflictPreview] = useState(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const prodData = await fetchProductDetail(productId);
        setProduct(prodData);

        // Pre-check conflicts against existing cart products
        if (cartProductIds.length > 0) {
          const conflictData = await checkIngredientConflicts(productId, cartProductIds);
          setConflictPreview(conflictData);
        } else {
          setConflictPreview(null);
        }
      } catch (err) {
        setError(err.message || 'Failed to load product details.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [productId, cartProductIds]);

  const handleAdd = async () => {
    setAdding(true);
    try {
      await onAddToCart(product.id, quantity);
    } finally {
      setAdding(false);
    }
  };

  if (loading) {
    return (
      <div className="product-detail-skeleton">
        <div className="skeleton-image"></div>
        <div className="skeleton-details"></div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="error-box">
        <h3>Product Not Found</h3>
        <p>{error || "Unable to display this product."}</p>
        <button className="btn-secondary" onClick={onBack}>
          Return to Catalog
        </button>
      </div>
    );
  }

  return (
    <div className="product-detail-container">
      {/* Breadcrumb Navigation */}
      <div className="detail-breadcrumbs">
        <button className="breadcrumb-link" onClick={onBack}>
          &larr; Back to Catalog
        </button>
        <span className="breadcrumb-separator">/</span>
        <span className="breadcrumb-current">{product.category_display || product.category}</span>
      </div>

      <div className="detail-layout">
        {/* Left Column: Visual Presentation */}
        <div className="detail-visual-col">
          <div className="detail-image-card">
            <img
              src={product.image_url || `/images/products/${product.category}.jpg`}
              alt={product.name}
              className="detail-main-img"
              onError={(e) => {
                if (!e.target.src.endsWith(`${product.category}.jpg`)) {
                  e.target.src = `/images/products/${product.category}.jpg`;
                }
              }}
            />
            <div className="detail-climate-badge">
              <SunIcon size={16} />
              <span>{product.climate_display || product.suitable_climate}</span>
            </div>
          </div>
        </div>

        {/* Right Column: Information & Actions */}
        <div className="detail-info-col">
          <div className="detail-header">
            <div className="detail-tags-row">
              <span className="category-pill">{product.category_display || product.category}</span>
              <span className={`active-level-pill ${product.active_level === 'high' ? 'badge-active-high' : product.active_level === 'medium' ? 'badge-active-med' : 'badge-active-gentle'}`}>
                {product.active_display || product.active_level.toUpperCase()}
              </span>
              <span className="duration-pill">&asymp; {product.typical_duration_days} Days Supply</span>
            </div>

            <h1 className="detail-product-name">{product.name}</h1>
            <div className="detail-price-row">
              <span className="detail-price">{formatRupees(product.price)}</span>
              <span className="detail-usage-frequency">Use {product.usage_frequency.replace(/_/g, ' ')} &bull; {product.time_of_day}</span>
            </div>
          </div>

          <p className="detail-description">{product.description}</p>

          {/* Key Specifications Grid */}
          <div className="detail-specs-grid">
            <div className="spec-card">
              <span className="spec-label">Texture</span>
              <span className="spec-value">{product.texture_display || product.texture}</span>
            </div>
            <div className="spec-card">
              <span className="spec-label">Hydration Depth</span>
              <span className="spec-value">{product.hydration_display || product.hydration_level}</span>
            </div>
            <div className="spec-card">
              <span className="spec-label">Target Climate</span>
              <span className="spec-value">{product.climate_display || product.suitable_climate}</span>
            </div>
            <div className="spec-card">
              <span className="spec-label">Routine Stage</span>
              <span className="spec-value">{product.routine_stage_display || `Stage ${product.routine_stage}`}</span>
            </div>
            <div className="spec-card">
              <span className="spec-label">Skin Types</span>
              <span className="spec-value">{product.skin_types || 'All Skin Types'}</span>
            </div>
            <div className="spec-card">
              <span className="spec-label">Primary Concerns</span>
              <span className="spec-value">{product.concerns || 'Barrier Support, Daily Health'}</span>
            </div>
          </div>

          {/* Conflict Pre-check Banner against existing Cart items */}
          {conflictPreview && conflictPreview.has_conflicts && (
            <div className="detail-conflict-preview-banner">
              <div className="conflict-preview-header">
                <AlertTriangleIcon size={18} className="text-amber" />
                <h4>Routine Harmony Consideration</h4>
              </div>
              <p className="conflict-preview-text">
                This formula contains actives that interact with items already in your cart (e.g.{' '}
                <strong>{conflictPreview.warnings[0]?.ingredient_a}</strong> +{' '}
                <strong>{conflictPreview.warnings[0]?.ingredient_b}</strong>).
              </p>
              <p className="conflict-preview-suggestion">
                <em>Guidance: {conflictPreview.warnings[0]?.suggestion}</em>
              </p>
            </div>
          )}

          {/* Add to Cart Actions */}
          <div className="detail-purchase-actions">
            <div className="quantity-stepper">
              <button
                type="button"
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                className="stepper-btn"
                disabled={quantity <= 1}
              >
                &minus;
              </button>
              <span className="stepper-value">{quantity}</span>
              <button
                type="button"
                onClick={() => setQuantity((q) => q + 1)}
                className="stepper-btn"
              >
                +
              </button>
            </div>

            <button
              type="button"
              className="btn-add-primary"
              onClick={handleAdd}
              disabled={adding}
            >
              <BagIcon size={18} />
              <span>{adding ? 'Adding to Cart...' : `Add to Bag • ${formatRupees(parseFloat(product.price) * quantity)}`}</span>
            </button>
          </div>

          {/* Full Ingredients Breakdown from Database */}
          <div className="detail-ingredients-section">
            <div className="ingredients-header">
              <ShieldCheckIcon size={18} />
              <h3>Full Active Ingredient Profile (From Database)</h3>
            </div>
            <div className="ingredients-list">
              {product.ingredients && product.ingredients.length > 0 ? (
                product.ingredients.map((ing) => (
                  <div key={ing.id} className="ingredient-detail-item">
                    <div className="ing-name-row">
                      <span className="ing-name">{ing.name}</span>
                      <span className="ing-category-badge">{ing.category_display || ing.category}</span>
                    </div>
                    {ing.description && <p className="ing-desc">{ing.description}</p>}
                  </div>
                ))
              ) : (
                <p className="text-muted">Gentle carrier formulation with supportive botanical emollients.</p>
              )}
            </div>
          </div>

          {/* Database Ingredient Interactions & Synergies */}
          {product.known_interactions && product.known_interactions.length > 0 && (
            <div className="detail-database-interactions-section">
              <div className="interactions-db-header">
                <AlertTriangleIcon size={18} className="text-amber" />
                <h3>Documented Active Interactions & Synergies</h3>
              </div>
              <div className="interactions-db-list">
                {product.known_interactions.map((rule) => (
                  <div key={rule.id} className={`db-rule-card rule-${rule.severity}`}>
                    <div className="db-rule-head">
                      <span className="db-pair-name">
                        {rule.ingredient_a_name} + {rule.ingredient_b_name}
                      </span>
                      <span className={`severity-pill pill-${rule.severity}`}>
                        {rule.severity.toUpperCase()}
                      </span>
                    </div>
                    <p className="db-rule-msg">{rule.message}</p>
                    <p className="db-rule-rec"><strong>Recommendation:</strong> {rule.recommendation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
