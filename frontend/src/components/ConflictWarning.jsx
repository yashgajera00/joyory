import React from 'react';
import { AlertTriangleIcon, SparklesIcon, ShieldCheckIcon, BagIcon } from './Icons';
import { formatRupees } from '@/lib/utils';

export default function ConflictWarning({ conflictData, onAddAlternative }) {
  if (!conflictData || !conflictData.has_conflicts || !conflictData.warnings || conflictData.warnings.length === 0) {
    return (
      <div className="conflict-safe-badge">
        <ShieldCheckIcon size={18} className="text-emerald" />
        <span>All active ingredients in your cart are mutually compatible.</span>
      </div>
    );
  }

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'warning':
        return <span className="severity-pill pill-warning">Cautionary Pair</span>;
      case 'caution':
        return <span className="severity-pill pill-caution">Spacing Recommended</span>;
      case 'info':
      default:
        return <span className="severity-pill pill-info">Compatible Synergy</span>;
    }
  };

  return (
    <div className="conflict-card-panel">
      <div className="conflict-panel-header">
        <div className="conflict-title-group">
          <AlertTriangleIcon size={22} className="text-amber" />
          <div>
            <h3 className="conflict-title">Multi-Product Routine Compatibility Guidance</h3>
            <p className="conflict-subtitle">
              Joyory's Interaction Engine analyzed active ingredients across your cart. Non-blocking safety notice:
            </p>
          </div>
        </div>
      </div>

      {/* Warnings List */}
      <div className="conflict-warnings-list">
        {conflictData.warnings.map((w, idx) => (
          <div key={idx} className={`warning-item border-${w.severity}`}>
            <div className="warning-meta-row">
              <div className="ingredient-pair">
                <span className="ing-tag">{w.ingredient_a}</span>
                <span className="pair-separator">+</span>
                <span className="ing-tag">{w.ingredient_b}</span>
              </div>
              {getSeverityBadge(w.severity)}
            </div>

            <div className="warning-products-involved">
              Between: <strong>{w.existing_product_name || `Product #${w.existing_product_id}`}</strong> & <strong>{w.new_product_name || `Product #${w.new_product_id}`}</strong>
            </div>

            <p className="warning-explanation">{w.message}</p>
            <div className="warning-suggestion">
              <strong>Smart Action:</strong> {w.suggestion}
            </div>
          </div>
        ))}
      </div>

      {/* Alternative Recommendations if available */}
      {conflictData.alternatives && conflictData.alternatives.length > 0 && (
        <div className="conflict-alternatives-box">
          <div className="alternatives-header">
            <SparklesIcon size={18} className="text-purple" />
            <h4>Gentle Compatible Alternatives in Same Category</h4>
          </div>
          <div className="alternatives-grid">
            {conflictData.alternatives.map((alt) => (
              <div key={alt.product_id} className="alt-item-card">
                <div className="alt-info">
                  <h5 className="alt-name">{alt.name}</h5>
                  <span className="alt-price">{formatRupees(alt.price)}</span>
                  <p className="alt-reason">{alt.reason}</p>
                </div>
                {onAddAlternative && (
                  <button
                    className="btn-add-alt"
                    onClick={() => onAddAlternative(alt.product_id)}
                  >
                    <BagIcon size={14} />
                    <span>Add to Bag</span>
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
