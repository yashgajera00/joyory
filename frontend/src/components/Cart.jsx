import React, { useState } from 'react';
import { BagIcon, TrashIcon, CalendarIcon, ArrowRightIcon, SparklesIcon } from './Icons';
import ConflictWarning from './ConflictWarning';
import ClimateInsight from './ClimateInsight';
import CheckoutModal from './CheckoutModal';
import { formatRupees } from '@/lib/utils';

export default function Cart({
  cart,
  conflictData,
  loading,
  user,
  onUpdateQuantity,
  onRemoveItem,
  onAddProduct,
  onGenerateRoutine,
  onGoToShop,
  onGoToRoutine,
  onOrderSuccess,
}) {
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const items = cart?.items || [];
  const isEmpty = items.length === 0;
  const cartProductIds = items.map((item) => item.product.id);

  return (
    <div className="cart-page-container">
      <div className="cart-page-header">
        <h1 className="cart-main-title">Shopping Bag & Routine Review</h1>
        <p className="cart-main-subtext">
          Review your formulas, inspect multi-product active ingredient compatibility, and explore environmental climate adaptations.
        </p>
      </div>

      {isEmpty ? (
        <div className="cart-empty-state">
          <div className="empty-icon-wrap">
            <BagIcon size={48} />
          </div>
          <h2>Your bag is currently empty</h2>
          <p>Explore Joyory's formulas to begin building a synergistic skincare routine.</p>
          <button className="btn-add-primary" onClick={onGoToShop}>
            Explore Products
          </button>
        </div>
      ) : (
        <div className="cart-grid-layout">
          {/* Left / Main Column: Items & Routine Generators */}
          <div className="cart-items-column">
            {/* Bag Items List */}
            <div className="cart-items-card">
              <div className="cart-items-header">
                <h3>Bag Items ({cart.total_items || items.length})</h3>
              </div>

              <div className="cart-items-list">
                {items.map((item) => (
                  <div key={item.id} className="cart-item-row">
                    <div className="item-visual-thumb">
                      <img
                        src={item.product.image_url || `/images/products/${item.product.category}.jpg`}
                        alt={item.product.name}
                        className="cart-thumb-img"
                        onError={(e) => {
                          if (!e.target.src.endsWith(`${item.product.category}.jpg`)) {
                            e.target.src = `/images/products/${item.product.category}.jpg`;
                          }
                        }}
                      />
                    </div>

                    <div className="item-details">
                      <span className="item-category-label">
                        {item.product.category_display || item.product.category}
                      </span>
                      <h4 className="item-name">{item.product.name}</h4>
                      <span className="item-unit-price">{formatRupees(item.product.price)} each</span>
                      <span className="item-actives-meta">
                        Actives: {item.product.ingredients?.map((i) => i.name).join(', ') || 'Botanical'}
                      </span>
                    </div>

                    {/* Quantity Stepper */}
                    <div className="item-stepper-wrap">
                      <div className="quantity-stepper small">
                        <button
                          type="button"
                          className="stepper-btn"
                          onClick={() => {
                            if (item.quantity > 1) {
                              onUpdateQuantity(item.product.id, item.quantity - 1);
                            } else {
                              onRemoveItem(item.product.id);
                            }
                          }}
                          disabled={loading}
                          title={item.quantity > 1 ? "Decrease quantity" : "Remove item"}
                          aria-label="Decrease quantity"
                        >
                          &minus;
                        </button>
                        <span className="stepper-value">{item.quantity}</span>
                        <button
                          type="button"
                          className="stepper-btn"
                          onClick={() => onUpdateQuantity(item.product.id, item.quantity + 1)}
                          disabled={loading}
                          title="Increase quantity"
                          aria-label="Increase quantity"
                        >
                          +
                        </button>
                      </div>
                    </div>

                    {/* Line Total */}
                    <div className="item-line-total">
                      {formatRupees(item.line_total || item.product.price * item.quantity)}
                    </div>

                    {/* Remove Action */}
                    <button
                      type="button"
                      className="btn-remove-item"
                      onClick={() => onRemoveItem(item.product.id)}
                      disabled={loading}
                      title="Remove product"
                    >
                      <TrashIcon size={16} />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Feature 1: Multi-Product Routine Conflict Detector */}
            <ConflictWarning
              conflictData={conflictData}
              onAddAlternative={onAddProduct}
            />

            {/* Feature 2: Hyper-Local Climate Skin Adaptation */}
            <ClimateInsight onAddProduct={onAddProduct} />
          </div>

          {/* Right Column: Order Summary & Progressive Routine Action */}
          <div className="cart-summary-column">
            <div className="summary-card">
              <h3 className="summary-title">Summary & Actions</h3>

              <div className="summary-rows">
                <div className="summary-row">
                  <span>Subtotal ({cart.total_items} items)</span>
                  <span className="summary-price">{formatRupees(cart.total_price || 0)}</span>
                </div>
                <div className="summary-row">
                  <span>Standard Delivery</span>
                  <span className="text-emerald">Complimentary</span>
                </div>
                <div className="summary-row">
                  <span>Routine Synergy Check</span>
                  <span className="text-emerald">Active &bull; Passed</span>
                </div>
                <div className="summary-divider"></div>
                <div className="summary-row total-row">
                  <span>Estimated Total</span>
                  <span className="total-price">{formatRupees(cart.total_price || 0)}</span>
                </div>
              </div>

              {/* Differentiating Feature 3 Call to Action: Generate Routine */}
              <div className="routine-cta-block">
                <div className="routine-cta-badge">
                  <SparklesIcon size={14} />
                  <span>Smart Routine Integration</span>
                </div>
                <p className="routine-cta-text">
                  Transform these {items.length} formulas into a personalized, safe multi-week progressive routine.
                </p>
                <button
                  type="button"
                  className="btn-generate-routine"
                  onClick={() => onGenerateRoutine(cartProductIds)}
                  disabled={loading || items.length === 0}
                >
                  <CalendarIcon size={18} />
                  <span>Generate Progressive Routine</span>
                </button>
              </div>

              {/* Checkout Button */}
              <button
                type="button"
                className="btn-checkout-primary"
                onClick={() => setIsCheckoutOpen(true)}
              >
                <span>Proceed to Checkout</span>
                <ArrowRightIcon size={18} />
              </button>

              <div className="summary-guarantees">
                <p>&bull; 30-Day Barrier Satisfaction Guarantee</p>
                <p>&bull; Automatic Delivery Replenishment Available</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Luxury Checkout Flow Modal */}
      <CheckoutModal
        isOpen={isCheckoutOpen}
        onClose={() => setIsCheckoutOpen(false)}
        cart={cart}
        user={user}
        conflictData={conflictData}
        onOrderSuccess={onOrderSuccess}
        onGoToRoutine={onGoToRoutine}
        onGoToShop={onGoToShop}
      />
    </div>
  );
}
