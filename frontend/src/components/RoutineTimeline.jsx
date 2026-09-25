import React, { useState, useEffect } from 'react';
import { CalendarIcon, SparklesIcon, CheckCircleIcon, ArrowRightIcon, AlertTriangleIcon, ShieldCheckIcon, TrashIcon } from './Icons';
import { fetchRoutineDetail, deleteRoutineStep } from '../services/api';

export default function RoutineTimeline({ routineData: initialRoutineData, routineId, onGoToTracker, onGoToDelivery, onRoutineUpdated }) {
  const [routineData, setRoutineData] = useState(initialRoutineData);
  const [loading, setLoading] = useState(false);
  const [deletingStepId, setDeletingStepId] = useState(null);

  // Sync or reload routine detail to ensure timeline has latest tracker completions
  const effectiveRoutineId = routineId || initialRoutineData?.routine_id || initialRoutineData?.id;

  const refreshTimelineData = async () => {
    if (!effectiveRoutineId) return;
    try {
      setLoading(true);
      const data = await fetchRoutineDetail(effectiveRoutineId);
      if (data) {
        setRoutineData(data);
        if (onRoutineUpdated) onRoutineUpdated(data);
      }
    } catch (err) {
      console.warn("Could not refresh timeline data:", err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteStep = async (stepId, productName) => {
    const confirmed = window.confirm(`Are you sure you want to delete "${productName}" from your routine timeline and daily tracker?`);
    if (!confirmed) return;

    try {
      setDeletingStepId(stepId);
      await deleteRoutineStep(effectiveRoutineId, stepId);
      await refreshTimelineData();
    } catch (err) {
      alert(`Could not delete step: ${err.message}`);
    } finally {
      setDeletingStepId(null);
    }
  };

  useEffect(() => {
    if (initialRoutineData) {
      setRoutineData(initialRoutineData);
    }
  }, [initialRoutineData]);

  useEffect(() => {
    refreshTimelineData();
  }, [effectiveRoutineId]);

  if (!routineData) {
    return (
      <div className="routine-empty-box">
        <CalendarIcon size={36} />
        <h3>No active routine generated yet</h3>
        <p>Add products to your cart and click "Generate Progressive Routine" to create your personalized multi-week timeline.</p>
      </div>
    );
  }

  const stages = routineData.stages || [];
  const journey = routineData.journey_summary || {
    title: "Your Skincare Journey",
    current_stage_number: routineData.current_stage || 1,
    current_stage_name: "Barrier Foundation",
    current_stage_full: `Stage ${routineData.current_stage || 1} — Barrier Foundation`,
    current_week_text: "Week 1 of 6",
    overall_progress: routineData.progress_percentage || 0,
    total_stages: 3,
    total_weeks: 6,
    total_products: routineData.total_steps_count || routineData.total_steps || 0,
    next_stage_name: "Stage 2 — Targeted Prep & Hydration",
    days_remaining_in_stage: 14,
    days_remaining_text: "14 days remaining"
  };

  const adaptiveGuidance = routineData.adaptive_guidance;
  const overallPct = routineData.progress_percentage ?? journey.overall_progress ?? 0;

  return (
    <div className="routine-timeline-container">
      {/* 1. TOP SUMMARY SECTION: "Your Skincare Journey" */}
      <div className="timeline-summary-card">
        <div className="summary-card-top">
          <div className="summary-title-group">
            <div className="timeline-eyebrow">
              <SparklesIcon size={14} />
              <span>Personalized Clinical Roadmap</span>
            </div>
            <h1 className="timeline-main-title">{journey.title || "Your Skincare Journey"}</h1>
            <p className="timeline-subtitle">
              Engineered to systematically introduce high-potency actives across 3 staged phases without triggering epidermal barrier shock.
            </p>
          </div>

          <div className="summary-stage-pillbox">
            <span className="pill-current-stage">
              {journey.current_stage_full || `Stage ${journey.current_stage_number} — ${journey.current_stage_name}`}
            </span>
            <span className="pill-week-indicator">
              {journey.current_week_text || "Week 1 of 6"}
            </span>
          </div>
        </div>

        {/* Overall Progress Bar */}
        <div className="timeline-progress-section">
          <div className="progress-metrics-row">
            <span className="metric-title">Overall Roadmap Progress</span>
            <span className="metric-pct"><strong>{overallPct}%</strong> Completed</span>
          </div>
          <div className="timeline-progress-track">
            <div
              className="timeline-progress-fill"
              style={{ width: `${Math.min(100, Math.max(4, overallPct))}%` }}
            ></div>
          </div>
        </div>

        {/* Roadmap Specs Grid */}
        <div className="journey-specs-grid">
          <div className="spec-item">
            <span className="spec-number">{journey.total_stages || 3}</span>
            <span className="spec-label">Progressive Stages</span>
          </div>
          <div className="spec-item">
            <span className="spec-number">{journey.total_weeks || 6}</span>
            <span className="spec-label">Adaptation Weeks</span>
          </div>
          <div className="spec-item">
            <span className="spec-number">{journey.total_products || routineData.total_steps || 0}</span>
            <span className="spec-label">Scheduled Formulas</span>
          </div>
          <div className="spec-item highlight">
            <span className="spec-sublabel">Next Phase Transition</span>
            <span className="spec-value-text">{journey.days_remaining_text || "In Progress"}</span>
          </div>
        </div>

        {/* Adaptive Routine Guidance Notice if present */}
        {adaptiveGuidance && adaptiveGuidance.has_warning && (
          <div className="adaptive-guidance-banner caution">
            <AlertTriangleIcon size={18} className="banner-icon" />
            <div>
              <strong>{adaptiveGuidance.title}</strong>
              <p>{adaptiveGuidance.message}</p>
              {adaptiveGuidance.recommendation && (
                <div className="banner-rec">Tip: {adaptiveGuidance.recommendation}</div>
              )}
            </div>
          </div>
        )}

      </div>

      {/* 2. PROGRESSIVE STAGES (Stage 1, Stage 2, Stage 3) */}
      <div className="timeline-stages-flow">
        {stages.map((stage) => {
          const isCurrent = stage.status === 'current';
          const isCompleted = stage.status === 'completed';
          const isUpcoming = stage.status === 'upcoming';

          return (
            <div
              key={stage.stage_number || stage.stage}
              className={`stage-timeline-card ${stage.status}`}
            >
              {/* Stage Header Banner */}
              <div className="stage-card-banner">
                <div className="stage-header-left">
                  <div className="stage-number-badge">
                    <span>STAGE {stage.stage_number || stage.stage}</span>
                  </div>
                  <div>
                    <h2 className="stage-header-title">{stage.stage_name}</h2>
                    <span className="stage-duration-label">{stage.duration}</span>
                  </div>
                </div>

                <div className="stage-header-right">
                  <span className={`stage-status-badge ${stage.status}`}>
                    {isCurrent && 'CURRENT STAGE'}
                    {isCompleted && '✓ COMPLETED'}
                    {isUpcoming && 'UPCOMING'}
                  </span>
                </div>
              </div>

              {/* Stage Dates & Days Progress */}
              <div className="stage-meta-row">
                <div className="stage-date-range">
                  <span className="date-icon">🗓</span>
                  <span>{stage.start_date} &ndash; {stage.expected_completion_date}</span>
                </div>

                <div className="stage-progress-box">
                  <div className="stage-progress-label">
                    <span>Stage Progress:</span>
                    <strong>{stage.progress_ratio || `${stage.days_progress} / ${stage.days_total} days`}</strong>
                  </div>
                  <div className="stage-progress-track">
                    <div
                      className="stage-progress-fill"
                      style={{ width: `${Math.min(100, Math.max(3, stage.progress_percentage || 0))}%` }}
                    ></div>
                  </div>
                </div>

                <div className="stage-next-countdown">
                  <span className="countdown-pill">{stage.next_stage_text}</span>
                </div>
              </div>

              {/* "Why this stage?" Clinical Rationale Box */}
              {stage.why_this_stage && (
                <div className="why-stage-callout">
                  <div className="callout-header">
                    <SparklesIcon size={14} />
                    <span>Why this stage?</span>
                  </div>
                  <p className="callout-body">{stage.why_this_stage}</p>
                  {stage.description && (
                    <p className="callout-sub">{stage.description}</p>
                  )}
                </div>
              )}

              {/* Products Introduced in this Stage */}
              <div className="stage-products-section">
                <div className="products-section-heading">
                  <span>Formulas Scheduled in Stage {stage.stage_number || stage.stage}</span>
                  <span className="products-count-tag">{stage.products?.length || 0} Products</span>
                </div>

                <div className="stage-products-grid">
                  {stage.products?.map((prod) => (
                    <div
                      key={prod.step_id || prod.product_id}
                      className={`timeline-product-card ${prod.completed ? 'is-completed' : ''}`}
                    >
                      {/* Product Thumbnail */}
                      <div className="timeline-prod-image-col">
                        {prod.image_url ? (
                          <img
                            src={prod.image_url}
                            alt={prod.product_name}
                            className="timeline-prod-img"
                            loading="lazy"
                          />
                        ) : (
                          <div className="timeline-prod-placeholder">
                            <SparklesIcon size={20} />
                          </div>
                        )}
                      </div>

                      {/* Product Info */}
                      <div className="timeline-prod-info-col">
                        <div className="prod-card-top-tags">
                          <span className="prod-category-tag">{prod.category}</span>
                          <span className="prod-time-tag">
                            {prod.time_display || prod.time_of_day}
                          </span>
                          <button
                            type="button"
                            className="btn-timeline-delete-step"
                            title={`Remove ${prod.product_name} from routine`}
                            disabled={deletingStepId === (prod.step_id || prod.id)}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteStep(prod.step_id || prod.id, prod.product_name);
                            }}
                          >
                            <TrashIcon size={12} />
                            <span>Delete</span>
                          </button>
                        </div>

                        <h4 className="prod-card-name">{prod.product_name}</h4>

                        <div className="prod-schedule-details">
                          <span className="detail-item">
                            <strong>Frequency:</strong> {prod.frequency_display || prod.frequency}
                          </span>
                          <span className="detail-item">
                            <strong>Starts:</strong> {prod.start_date}
                          </span>
                          {prod.expected_completion_date && (
                            <span className="detail-item">
                              <strong>Until:</strong> {prod.expected_completion_date}
                            </span>
                          )}
                        </div>

                        {/* Status (Read-Only on Timeline, driven by Tracker) */}
                        <div className="prod-card-status-row">
                          {prod.completed ? (
                            <span className="timeline-status-badge completed" title="Completed via Daily Tracker">
                              <CheckCircleIcon size={14} />
                              <span>Completed</span>
                              {prod.completed_at && <small>({prod.completed_at})</small>}
                            </span>
                          ) : (
                            <span className="timeline-status-badge scheduled">
                              <span>Scheduled</span>
                            </span>
                          )}
                          <span className="status-note-hint">Logged via Daily Tracker</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

