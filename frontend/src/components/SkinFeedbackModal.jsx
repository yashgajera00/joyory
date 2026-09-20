import React, { useState } from 'react';
import { SparklesIcon, CheckCircleIcon } from './Icons';
import './SkinFeedbackModal.css';

export default function SkinFeedbackModal({
  isOpen,
  onClose,
  taskData,
  onSubmitFeedback,
}) {
  const [selectedFeel, setSelectedFeel] = useState(null);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSelectFeel = async (feel) => {
    setSelectedFeel(feel);
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!selectedFeel) return;

    setSubmitting(true);
    try {
      if (onSubmitFeedback) {
        await onSubmitFeedback(selectedFeel, notes);
      }
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setSelectedFeel(null);
        setNotes('');
        onClose();
      }, 1400);
    } catch (err) {
      alert(`Could not record feedback: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="feedback-modal-backdrop" onClick={submitting ? undefined : onClose}>
      <div className="feedback-modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="feedback-modal-header">
          <div className="feedback-modal-title-group">
            <div className="feedback-sparkle-icon">
              <SparklesIcon size={18} />
            </div>
            <div>
              <h2 className="feedback-modal-title">How did your skin feel today?</h2>
              <p className="feedback-modal-subtitle">
                1-click daily feedback tunes your routine's progressive pace.
              </p>
            </div>
          </div>
          {!submitting && (
            <button
              type="button"
              className="feedback-modal-close"
              onClick={onClose}
              aria-label="Close modal"
            >
              &times;
            </button>
          )}
        </div>

        {/* Modal Body */}
        <div className="feedback-modal-body">
          {success ? (
            <div className="feedback-success-banner">
              <div className="feedback-success-icon-wrap">
                <CheckCircleIcon size={32} />
              </div>
              <h3>Tolerance Feedback Recorded!</h3>
              <p>Your personalized routine is dynamically adapting to keep your skin barrier calm and thriving.</p>
            </div>
          ) : (
            <>
              {taskData && (
                <div className="feedback-task-pill">
                  <span className="pill-session-icon">
                    {taskData.session === 'morning' ? '☀️' : '🌙'}
                  </span>
                  <span className="pill-task-label">
                    Just applied: <strong>{taskData.productName}</strong>
                  </span>
                </div>
              )}

              {/* 3 Main Skin Feel Options */}
              <div className="feedback-cards-grid">
                <button
                  type="button"
                  className={`feedback-card-choice ${selectedFeel === 'comfortable' ? 'selected comfortable' : ''}`}
                  onClick={() => handleSelectFeel('comfortable')}
                  disabled={submitting}
                >
                  <span className="feedback-card-emoji">😊</span>
                  <span className="feedback-card-name">Comfortable</span>
                  <span className="feedback-card-tagline">Calm, hydrated, and zero irritation</span>
                </button>

                <button
                  type="button"
                  className={`feedback-card-choice ${selectedFeel === 'dry' ? 'selected dry' : ''}`}
                  onClick={() => handleSelectFeel('dry')}
                  disabled={submitting}
                >
                  <span className="feedback-card-emoji">😐</span>
                  <span className="feedback-card-name">A little dry</span>
                  <span className="feedback-card-tagline">Mild tightness or barrier needs moisture</span>
                </button>

                <button
                  type="button"
                  className={`feedback-card-choice ${selectedFeel === 'irritated' ? 'selected irritated' : ''}`}
                  onClick={() => handleSelectFeel('irritated')}
                  disabled={submitting}
                >
                  <span className="feedback-card-emoji">😣</span>
                  <span className="feedback-card-name">Irritated</span>
                  <span className="feedback-card-tagline">Stinging, redness, or burning sensation</span>
                </button>
              </div>

              {/* Optional Notes */}
              <div className="feedback-notes-wrap">
                <label className="feedback-notes-label">
                  Skin tolerance notes (optional):
                </label>
                <textarea
                  className="feedback-notes-textarea"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. slight tingling around nose, absorbed quickly..."
                  rows={2}
                  disabled={submitting}
                />
              </div>

              {/* Actions Footer */}
              <div className="feedback-modal-actions">
                <button
                  type="button"
                  className="btn-feedback-submit"
                  disabled={!selectedFeel || submitting}
                  onClick={handleSubmit}
                >
                  {submitting ? 'Saving...' : 'Submit Feedback'}
                </button>

                <button
                  type="button"
                  className="btn-feedback-skip"
                  onClick={onClose}
                  disabled={submitting}
                >
                  Skip for Now
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
