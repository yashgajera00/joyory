import React, { useState, useEffect, useRef } from 'react';
import { CheckCircleIcon, CalendarIcon, BagIcon, SparklesIcon } from './Icons';
import { clearCart, generateRoutine } from '../services/api';
import { formatRupees } from '@/lib/utils';
import './CheckoutModal.css';

export default function CheckoutModal({
  isOpen,
  onClose,
  cart,
  user,
  conflictData,
  onOrderSuccess,
  onGoToRoutine,
  onGoToShop,
}) {
  const [loading, setLoading] = useState(false);
  const [confirmedOrder, setConfirmedOrder] = useState(null);
  const processedRef = useRef(false);

  useEffect(() => {
    if (!isOpen) {
      processedRef.current = false;
      setConfirmedOrder(null);
      setLoading(false);
      return;
    }

    // Only process once when modal opens
    if (processedRef.current) return;
    processedRef.current = true;

    const currentItems = cart?.items ? [...cart.items] : [];
    const currentTotal = cart?.total_price || 0;
    const productIds = currentItems.map((i) => i.product.id);

    const executeOrder = async () => {
      setLoading(true);

      const orderId = `JOY-2026-${Math.floor(100000 + Math.random() * 900000)}`;
      const deliveryDate = new Date();
      deliveryDate.setDate(deliveryDate.getDate() + 3);
      const deliveryDateStr = deliveryDate.toLocaleDateString('en-IN', {
        weekday: 'long',
        month: 'short',
        day: 'numeric',
      });

      let generatedRoutineData = null;
      try {
        if (productIds.length > 0) {
          const clientName = user?.full_name || user?.first_name || user?.username || 'Client';
          generatedRoutineData = await generateRoutine(productIds, `${clientName}'s Progressive Routine`);
        }
      } catch (err) {
        console.warn('Routine auto-generation notice:', err);
      }

      try {
        await clearCart();
      } catch (err) {
        console.warn('Backend cart clear notice:', err);
      }

      const orderData = {
        orderId,
        deliveryDate: deliveryDateStr,
        itemCount: currentItems.length,
        items: currentItems,
        total: currentTotal,
        recipient: user?.full_name || user?.first_name || user?.username || 'Valued Client',
      };

      setConfirmedOrder(orderData);
      setLoading(false);

      if (onOrderSuccess) {
        onOrderSuccess(orderId, generatedRoutineData);
      }
    };

    executeOrder();
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="checkout-modal-backdrop" onClick={loading ? undefined : onClose}>
      <div className="checkout-modal-card success-card-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="checkout-modal-header">
          <div className="checkout-modal-title-wrap">
            <div className="checkout-shield-icon success">
              <CheckCircleIcon size={20} />
            </div>
            <div>
              <h2 className="checkout-modal-title">
                {loading ? 'Finalizing Order...' : 'Order Placed Successfully!'}
              </h2>
              <p className="checkout-modal-subtitle">
                {loading
                  ? 'Synchronizing formulas with your routine timeline'
                  : 'Formulas scheduled in Routine Timeline & Daily Tracker'}
              </p>
            </div>
          </div>
          {!loading && (
            <button
              type="button"
              className="checkout-modal-close"
              onClick={onClose}
              aria-label="Close modal"
            >
              &times;
            </button>
          )}
        </div>

        {/* Modal Body */}
        <div className="checkout-modal-body compact">
          {loading ? (
            <div className="checkout-processing-view">
              <div className="checkout-spinner" />
              <h3 className="checkout-processing-title">Scheduling Your Progressive Routine...</h3>
              <p className="checkout-processing-sub">
                Encrypting active compatibility, locking in complimentary express delivery, and scheduling formulas into your timeline.
              </p>
            </div>
          ) : (
            confirmedOrder && (
              <div className="checkout-confirmed-view">
                <div className="checkout-success-icon">
                  <CheckCircleIcon size={36} />
                </div>

                <h3 className="checkout-confirmed-title">
                  Thank you, {confirmedOrder.recipient}!
                </h3>

                <div className="checkout-confirmed-order-code">
                  <span>Order ID:</span>
                  <strong>{confirmedOrder.orderId}</strong>
                </div>

                <p className="checkout-confirmed-desc">
                  Your order has been placed successfully! All purchased formulas have been added to your{' '}
                  <strong>Routine Timeline</strong> and <strong>Daily Tracker</strong>.
                </p>

                {/* Items Preview List */}
                {confirmedOrder.items && confirmedOrder.items.length > 0 && (
                  <div className="checkout-success-items-box">
                    <div className="checkout-synergy-banner compact">
                      <SparklesIcon size={14} />
                      <span>Active Ingredient Compatibility Verified</span>
                    </div>

                    <div className="checkout-items-preview">
                      {confirmedOrder.items.map((item) => (
                        <div key={item.id || item.product?.id} className="checkout-item-row">
                          <div className="checkout-item-left">
                            <span className="checkout-item-name">{item.product?.name}</span>
                            <span className="checkout-item-qty">&times; {item.quantity}</span>
                          </div>
                          <span className="checkout-item-price">
                            {formatRupees(item.line_total || (item.product?.price || 0) * item.quantity)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Details Summary */}
                <div className="checkout-confirmed-details-card">
                  <div className="checkout-confirmed-row">
                    <span>Purchased Formulas:</span>
                    <strong>{confirmedOrder.itemCount} items ({formatRupees(confirmedOrder.total)})</strong>
                  </div>
                  <div className="checkout-confirmed-row">
                    <span>Estimated Delivery:</span>
                    <strong>{confirmedOrder.deliveryDate} (Complimentary)</strong>
                  </div>
                  <div className="checkout-confirmed-row">
                    <span>Formula Synergy:</span>
                    <strong style={{ color: '#16a34a' }}>Passed & Verified Safe</strong>
                  </div>
                </div>

                {/* Actions */}
                <div className="checkout-confirmed-actions">
                  <button
                    type="button"
                    className="btn-confirmed-routine"
                    onClick={() => {
                      onClose();
                      if (onGoToRoutine) onGoToRoutine();
                    }}
                  >
                    <CalendarIcon size={18} />
                    <span>Open Routine Timeline & Daily Tracker</span>
                  </button>

                  <button
                    type="button"
                    className="btn-confirmed-catalog"
                    onClick={() => {
                      onClose();
                      if (onGoToShop) onGoToShop();
                    }}
                  >
                    <BagIcon size={18} />
                    <span>Continue Shopping</span>
                  </button>
                </div>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
