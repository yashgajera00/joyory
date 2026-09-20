import React, { useState, useEffect } from 'react';
import { fetchRoutineDeliverySchedule, toggleDeliveryItemAutoReorder } from '../services/api';
import { CalendarIcon, RefreshCwIcon, CheckCircleIcon, ShieldCheckIcon, SparklesIcon } from './Icons';
import { formatRupees } from '@/lib/utils';

export default function DeliverySchedule({ routineId, onGoToTimeline, onGoToTracker }) {
  const [scheduleData, setScheduleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [togglingItems, setTogglingItems] = useState({});

  const loadSchedule = async () => {
    if (!routineId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRoutineDeliverySchedule(routineId);
      setScheduleData(data);
    } catch (err) {
      setError(err.message || 'Failed to load replenishment schedule.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSchedule();
  }, [routineId]);

  const handleToggleItemAutoReorder = async (itemId, currentActive) => {
    setTogglingItems((prev) => ({ ...prev, [itemId]: true }));
    try {
      const res = await toggleDeliveryItemAutoReorder(itemId);
      setScheduleData((prev) => {
        if (!prev || !prev.items) return prev;
        return {
          ...prev,
          items: prev.items.map((item) =>
            item.id === itemId
              ? { ...item, active: res.active !== undefined ? res.active : !currentActive }
              : item
          ),
        };
      });
    } catch (err) {
      alert(`Failed to update auto-reorder for this item: ${err.message}`);
    } finally {
      setTogglingItems((prev) => ({ ...prev, [itemId]: false }));
    }
  };

  if (!routineId) {
    return (
      <div className="routine-empty-box">
        <CalendarIcon size={36} />
        <h3>No active delivery schedule</h3>
        <p>Please generate a progressive routine first from your cart.</p>
      </div>
    );
  }

  if (loading && !scheduleData) {
    return (
      <div className="schedule-skeleton">
        <div className="skeleton-card"></div>
      </div>
    );
  }

  if (error && !scheduleData) {
    return (
      <div className="error-box">
        <h3>Schedule Retrieval Error</h3>
        <p>{error}</p>
        <button className="btn-secondary" onClick={loadSchedule}>
          Retry
        </button>
      </div>
    );
  }

  const items = scheduleData?.items || [];

  return (
    <div className="schedule-page-container">
      <div className="schedule-header-card">
        <div className="schedule-eyebrow">
          <CalendarIcon size={14} />
          <span>Smart Replenishment Logistics</span>
        </div>
        <h1 className="schedule-title">Automated Replenishment Schedule</h1>
        <p className="schedule-subtext">
          Never run out of essential formulas. Reorder dates are dynamically calculated from bottle milliliters, drop dosage, and prescribed weekly frequency.
        </p>

        <div className="routine-quick-nav">
          <button className="btn-tab-action" onClick={onGoToTimeline}>
            <CalendarIcon size={16} />
            <span>Progressive Timeline</span>
          </button>
          <button className="btn-tab-action" onClick={onGoToTracker}>
            <CheckCircleIcon size={16} />
            <span>Daily Micro-Tracker</span>
          </button>
          <button className="btn-refresh-icon" onClick={loadSchedule} title="Refresh schedule">
            <RefreshCwIcon size={16} />
          </button>
        </div>
      </div>

      <div className="schedule-items-card">
        <div className="schedule-card-head">
          <h3>Formulas & Projected Refill Dates</h3>
          <span className="replenishment-badge">Auto-Calculated Engine</span>
        </div>

        <div className="schedule-items-list">
          {items.map((item) => {
            const isItemActive = item.active !== false;
            const isTogglingThisItem = !!togglingItems[item.id];

            return (
              <div
                key={item.id}
                className={`schedule-row ${!isItemActive ? 'item-reorder-paused' : ''}`}
              >
                {/* Product Info Column */}
                <div className="schedule-prod-col" style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  {item.product_image_url && (
                    <img
                      src={item.product_image_url}
                      alt={item.product_name}
                      style={{
                        width: '56px',
                        height: '56px',
                        borderRadius: '12px',
                        objectFit: 'cover',
                        border: '1px solid var(--border-light)',
                        flexShrink: 0
                      }}
                      loading="lazy"
                    />
                  )}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', flexWrap: 'wrap' }}>
                      <span className="schedule-reorder-tag">Next Delivery</span>
                      {!isItemActive && (
                        <span style={{
                          backgroundColor: '#fef3c7',
                          color: '#b45309',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '9999px'
                        }}>
                          Refill Paused
                        </span>
                      )}
                    </div>
                    <h4 className="schedule-prod-name">{item.product_name}</h4>
                    <p className="schedule-reason">{item.reason}</p>
                    {item.tracking_number && (
                      <p style={{ margin: '4px 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        Courier Tracking: <strong>{item.tracking_number}</strong>
                      </p>
                    )}
                  </div>
                </div>

                {/* Cadence & Projected Date Column */}
                <div className="schedule-date-col">
                  <div className="reorder-date-box">
                    <span className="reorder-day">
                      {new Date(item.suggested_reorder_date).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </span>
                    <span className="reorder-cadence">Every {item.frequency_weeks} Weeks</span>
                  </div>
                </div>

                {/* PARTICULAR ITEM AUTO-REORDER OPTION */}
                <div className="schedule-item-autoreorder-col">
                  <div className="item-reorder-status-row">
                    <span className={`item-reorder-indicator-pill ${isItemActive ? 'active' : 'paused'}`}>
                      <span className="status-dot"></span>
                      <span>{isItemActive ? 'Auto-Reorder: ON' : 'Auto-Reorder: OFF'}</span>
                    </span>

                    <button
                      type="button"
                      className={`btn-item-reorder-toggle ${isItemActive ? 'btn-pause' : 'btn-resume'}`}
                      onClick={() => handleToggleItemAutoReorder(item.id, isItemActive)}
                      disabled={isTogglingThisItem}
                      title={isItemActive ? `Pause auto-reorder for ${item.product_name}` : `Enable auto-reorder for ${item.product_name}`}
                    >
                      {isTogglingThisItem
                        ? 'Updating...'
                        : (isItemActive ? 'Turn Off' : 'Turn On')}
                    </button>
                  </div>
                  <span className="item-reorder-hint">
                    {isItemActive
                      ? 'Refills automatically upon routine completion'
                      : 'Paused: Formula will not reorder automatically'}
                  </span>
                </div>

                {/* Status Badge & Price Column */}
                <div className="schedule-status-col">
                  <span className={item.status === 'auto_reordered' ? 'status-badge-active' : (isItemActive ? 'status-badge-active' : 'status-badge-paused')}>
                    {item.status === 'auto_reordered' ? 'Order Dispatched' : (isItemActive ? 'Scheduled Refill' : 'Refill Paused')}
                  </span>
                  {item.product_price && (
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginTop: '4px' }}>
                      {formatRupees(item.product_price)}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
