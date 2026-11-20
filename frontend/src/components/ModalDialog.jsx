import React from 'react';
import { TrashIcon, AlertTriangleIcon, CheckCircleIcon, SparklesIcon } from './Icons';
import './ModalDialog.css';

export default function ModalDialog({
  isOpen,
  onClose,
  title,
  message,
  type = 'confirm', // 'confirm' | 'alert'
  variant = 'warning', // 'danger' | 'warning' | 'success' | 'info'
  confirmText = 'OK',
  cancelText = 'Cancel',
  onConfirm,
  loading = false,
}) {
  if (!isOpen) return null;

  const handleConfirm = async () => {
    if (onConfirm) {
      await onConfirm();
    }
  };

  const getIcon = () => {
    switch (variant) {
      case 'danger':
        return <TrashIcon size={24} />;
      case 'warning':
        return <AlertTriangleIcon size={24} />;
      case 'success':
        return <CheckCircleIcon size={24} />;
      default:
        return <SparklesIcon size={24} />;
    }
  };

  return (
    <div className="custom-modal-backdrop" onClick={loading ? undefined : onClose}>
      <div className="custom-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className={`custom-modal-icon-badge variant-${variant}`}>
          {getIcon()}
        </div>

        <h3 className="custom-modal-title">{title}</h3>
        <p className="custom-modal-message">{message}</p>

        <div className="custom-modal-actions">
          {type === 'confirm' && (
            <button
              type="button"
              className="custom-modal-btn btn-cancel"
              onClick={onClose}
              disabled={loading}
            >
              {cancelText}
            </button>
          )}
          <button
            type="button"
            className={`custom-modal-btn btn-confirm variant-${variant}`}
            onClick={handleConfirm}
            disabled={loading}
          >
            {loading ? 'Please wait...' : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
