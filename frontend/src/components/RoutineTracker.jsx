import React, { useState, useEffect } from 'react';
import { 
  fetchRoutineProgress, 
  completeRoutineStep, 
  toggleRoutineAutoReorder, 
  completeAllRoutineSteps,
  submitDailySkinFeedback,
  deleteRoutineStep
} from '../services/api';
import { 
  CheckCircleIcon, 
  CalendarIcon, 
  SparklesIcon, 
  RefreshCwIcon, 
  ShieldCheckIcon,
  SunIcon,
  MoonIcon,
  AlertTriangleIcon,
  DropletIcon,
  WindIcon,
  TrashIcon
} from './Icons';
import SkinFeedbackModal from './SkinFeedbackModal';

const INDIAN_CITIES = [
  'Mumbai',
  'Delhi',
  'Bengaluru',
  'Chennai',
  'Kolkata',
  'Hyderabad',
  'Pune',
  'Jaipur'
];

export default function RoutineTracker({ routineId, user, onGoToTimeline, onGoToDelivery }) {
  const [progressData, setProgressData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [savingStepId, setSavingStepId] = useState(null);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);
  const [togglingReorder, setTogglingReorder] = useState(false);
  const [completingAll, setCompletingAll] = useState(false);
  const [deletingStepId, setDeletingStepId] = useState(null);

  // Live Clock for accurate time-based wishing
  const [currentTime, setCurrentTime] = useState(() => 
    new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  );

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    }, 10000);
    return () => clearInterval(timer);
  }, []);

  // Time-based wishing / greeting
  const getTimeBasedGreeting = () => {
    const hour = new Date().getHours();
    let base = 'Good Morning';
    if (hour >= 5 && hour < 12) {
      base = 'Good Morning';
    } else if (hour >= 12 && hour < 17) {
      base = 'Good Afternoon';
    } else if (hour >= 17 && hour < 22) {
      base = 'Good Evening';
    } else {
      base = 'Good Night';
    }

    const name = user?.first_name || user?.full_name || user?.username;
    return name ? `${base}, ${name}` : base;
  };

  // Feedback Modal triggered after completing a task
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState(false);
  const [feedbackTaskData, setFeedbackTaskData] = useState(null);

  // Date Simulation (0 = Today, 1 = Tomorrow / Next Day)
  const [selectedDateOffset, setSelectedDateOffset] = useState(0);

  // Time & Environmental Controls
  const [timeOfDay, setTimeOfDay] = useState(() => {
    const hour = new Date().getHours();
    return (hour >= 5 && hour < 17) ? 'morning' : 'evening';
  });
  const [selectedCity, setSelectedCity] = useState('Mumbai');
  const [selectedWeek, setSelectedWeek] = useState(null);

  const loadProgress = async (
    overrideTime = timeOfDay,
    overrideCity = selectedCity,
    overrideWeek = selectedWeek,
    overrideDateOffset = selectedDateOffset
  ) => {
    if (!routineId) return;
    setLoading(true);
    setError(null);
    try {
      const params = {
        time_of_day: overrideTime,
        city: overrideCity,
        client_hour: new Date().getHours()
      };

      if (overrideWeek !== null && overrideWeek !== undefined) {
        params.week = overrideWeek;
      }
      if (overrideDateOffset !== 0) {
        const targetDate = new Date();
        targetDate.setDate(targetDate.getDate() + overrideDateOffset);
        const yyyy = targetDate.getFullYear();
        const mm = String(targetDate.getMonth() + 1).padStart(2, '0');
        const dd = String(targetDate.getDate()).padStart(2, '0');
        params.date = `${yyyy}-${mm}-${dd}`;
      }
      const data = await fetchRoutineProgress(routineId, params);
      setProgressData(data);
    } catch (err) {
      setError(err.message || 'Failed to load routine progress.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProgress(timeOfDay, selectedCity, selectedWeek, selectedDateOffset);
  }, [routineId, timeOfDay, selectedCity, selectedWeek, selectedDateOffset]);

  // Automatically detect calendar date change (e.g. past midnight) to refresh tasks
  useEffect(() => {
    let lastDateStr = new Date().toDateString();
    const interval = setInterval(() => {
      const currentDateStr = new Date().toDateString();
      if (currentDateStr !== lastDateStr) {
        lastDateStr = currentDateStr;
        loadProgress(timeOfDay, selectedCity, selectedWeek, selectedDateOffset);
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [routineId, timeOfDay, selectedCity, selectedWeek, selectedDateOffset]);

  // Handle Delete Step from Routine
  const handleDeleteStep = async (stepId, productName) => {
    const confirmed = window.confirm(`Are you sure you want to delete "${productName}" from your routine timeline and daily tracker?`);
    if (!confirmed) return;

    try {
      setDeletingStepId(stepId);
      await deleteRoutineStep(routineId, stepId);
      await loadProgress();
    } catch (err) {
      alert(`Could not delete step: ${err.message}`);
    } finally {
      setDeletingStepId(null);
    }
  };

  // Handle Mark Complete / Step Action
  const handleToggleStep = async (stepId, currentStatus, suitability, session = 'morning') => {
    // Once a task is completed, it cannot be unchecked for the day
    if (currentStatus) {
      return;
    }

    if (suitability === 'not_recommended') {
      const proceed = window.confirm(
        '⚠️ Weather Timing Alert:\nThis formula is flagged as NOT RECOMMENDED for this time/climate due to active photosensitivity or daytime UV.\n\nAre you sure you want to mark it as applied right now?'
      );
      if (!proceed) return;
    }

    const key = `${session}-${stepId}`;
    setSavingStepId(key);
    try {
      const res = await completeRoutineStep(routineId, stepId, true, '', session);
      await loadProgress();

      // Look up task info to display in the feedback modal
      const taskList = session === 'morning' ? (progressData?.morning_routine || []) : (progressData?.evening_routine || []);
      const foundTask = taskList.find((t) => t.step_id === stepId);

      setFeedbackTaskData({
        stepId,
        productName: foundTask?.product_name || 'Joyory Formula',
        session,
      });
      setIsFeedbackModalOpen(true);

      if (res.auto_reordered_now) {
        alert(`🎉 Routine 100% Completed! Auto-reorder was triggered for your replenishments (Order: ${res.auto_reorder_order_id}).`);
      }
    } catch (err) {
      alert(`Error updating step: ${err.message}`);
    } finally {
      setSavingStepId(null);
    }
  };



  // Handle 1-Click Daily Skin Feedback
  const handleSkinFeedback = async (feel) => {
    setSubmittingFeedback(true);
    setFeedbackSuccess(false);
    try {
      const res = await submitDailySkinFeedback(routineId, feel, '');
      if (res) {
        setFeedbackSuccess(true);
        setTimeout(() => setFeedbackSuccess(false), 3000);
        await loadProgress();
      }
    } catch (err) {
      alert(`Could not record feedback: ${err.message}`);
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const handleToggleAutoReorder = async () => {
    setTogglingReorder(true);
    try {
      await toggleRoutineAutoReorder(routineId);
      await loadProgress();
    } catch (err) {
      alert(`Failed to update setting: ${err.message}`);
    } finally {
      setTogglingReorder(false);
    }
  };

  const handleCompleteAll = async () => {
    setCompletingAll(true);
    try {
      const res = await completeAllRoutineSteps(routineId);
      await loadProgress();
      if (res.auto_reordered_now) {
        alert(`🎉 All steps completed! Auto-reorder successfully dispatched (Order: ${res.auto_reorder_order_id}).`);
      }
    } catch (err) {
      alert(`Failed to complete steps: ${err.message}`);
    } finally {
      setCompletingAll(false);
    }
  };

  if (!routineId) {
    return (
      <div className="routine-empty-box">
        <CheckCircleIcon size={36} />
        <h3>No routine selected for tracking</h3>
        <p>Please generate a progressive routine first from your cart.</p>
      </div>
    );
  }

  if (loading && !progressData) {
    return (
      <div className="tracker-skeleton-wrap">
        <div className="skeleton-card"></div>
      </div>
    );
  }

  if (error && !progressData) {
    return (
      <div className="error-box">
        <h3>Tracking Error</h3>
        <p>{error}</p>
        <button className="btn-secondary" onClick={() => loadProgress()}>
          Retry
        </button>
      </div>
    );
  }

  const env = progressData?.environment || {};
  const todayProgress = progressData?.today_progress || { completed: 0, total: 0, percentage: 0, ratio_text: "0 / 0 completed" };
  const morningTasks = progressData?.morning_routine || [];
  const eveningTasks = progressData?.evening_routine || [];
  const todaySkinFeel = progressData?.today_skin_feel;
  const adaptiveGuidance = progressData?.adaptive_guidance;
  const autoReorderOn = progressData?.auto_reorder_enabled ?? true;
  const autoReordered = progressData?.auto_reordered ?? false;
  const isCompleted = progressData?.is_completed || progressData?.progress_percentage >= 100;

  return (
    <div className="tracker-page-container">
      {/* 1. TOP SECTION: Greeting, Today's Date, Today's Progress */}
      <div className="daily-tracker-hero">
        <div className="hero-top-row">
          <div>
            <div className="greeting-eyebrow">
              <SparklesIcon size={14} />
              <span>Today's Action Plan</span>
              <span className="hero-stage-tag">
                {progressData?.current_week_text || `Week ${progressData?.current_week || 1} of 6`} &bull; Stage {progressData?.current_stage || 1}
              </span>
            </div>
            <h1 className="greeting-title">
              {getTimeBasedGreeting()}
            </h1>
            <p className="today-date-text">
              {progressData?.today_date || new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' })}
              <span className="live-clock-badge" style={{ marginLeft: '10px', color: '#64748b', fontWeight: 500, fontSize: '0.85rem' }}>
                • {currentTime}
              </span>
              {selectedDateOffset > 0 && (
                <span className="tomorrow-indicator-badge" style={{ marginLeft: '10px', background: '#ede9fe', color: '#6366f1', padding: '2px 8px', borderRadius: '6px', fontSize: '0.78rem', fontWeight: 600 }}>
                  Tomorrow View (All tasks reset)
                </span>
              )}
            </p>

          </div>

          <div className="hero-controls-group">
            {/* Day Switcher: Today vs Tomorrow (Date Change Test) */}
            <div className="week-sim-pills" title="Simulate Date Change / Tomorrow Reset">
              <span className="sim-label">Day:</span>
              <button
                type="button"
                className={`sim-btn ${selectedDateOffset === 0 ? 'active' : ''}`}
                onClick={() => setSelectedDateOffset(0)}
                title="View Today"
              >
                Today
              </button>
              <button
                type="button"
                className={`sim-btn ${selectedDateOffset === 1 ? 'active' : ''}`}
                onClick={() => setSelectedDateOffset(1)}
                title="View Tomorrow (Automatic Day Change Reset)"
              >
                Tomorrow (+1d)
              </button>
            </div>

            {/* Simulation / Milestone Testing Switcher */}
            <div className="week-sim-pills" title="Filter Daily Tracker by Routine Milestone">
              <span className="sim-label">Milestone:</span>
              <button
                type="button"
                className={`sim-btn ${selectedWeek === null ? 'active' : ''}`}
                onClick={() => setSelectedWeek(null)}
                title="Real-time date"
              >
                Today
              </button>
              <button
                type="button"
                className={`sim-btn ${selectedWeek === 1 ? 'active' : ''}`}
                onClick={() => setSelectedWeek(1)}
                title="Week 1: Barrier Foundation"
              >
                Week 1
              </button>
              <button
                type="button"
                className={`sim-btn ${selectedWeek === 3 ? 'active' : ''}`}
                onClick={() => setSelectedWeek(3)}
                title="Week 3: Targeted Prep & Hydration"
              >
                Week 3
              </button>
              <button
                type="button"
                className={`sim-btn ${selectedWeek === 4 ? 'active' : ''}`}
                onClick={() => setSelectedWeek(4)}
                title="Week 4: Concentrated Active Integration"
              >
                Week 4
              </button>
            </div>


            <button
              type="button"
              className="btn-refresh-pill"
              onClick={() => loadProgress()}
              title="Refresh routine status"
            >
              <RefreshCwIcon size={14} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Today's Progress Bar */}
        <div className="today-progress-card">
          <div className="today-progress-labels">
            <span className="progress-card-title">Today's Progress</span>
            <span className="progress-ratio-tag">
              <strong>{todayProgress.completed}</strong> of <strong>{todayProgress.total}</strong> completed ({todayProgress.percentage}%)
            </span>
          </div>
          <div className="today-progress-track">
            <div
              className="today-progress-fill"
              style={{ width: `${Math.min(100, Math.max(3, todayProgress.percentage))}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* 2. COMPACT TODAY'S ENVIRONMENT CARD */}
      <div className="compact-environment-card">
        <div className="env-header-row">
          <div className="env-title-block">
            <div className="env-icon-box">
              {timeOfDay === 'morning' ? <SunIcon size={20} /> : <MoonIcon size={20} />}
            </div>
            <div>
              <h3 className="env-title">Today's Environment</h3>
              <p className="env-subtitle">
                Hyper-local climate guidance for current texture and daytime protection.
              </p>
            </div>
          </div>

          <div className="env-actions-block">
            <div className="city-pill-wrapper">
              <span className="city-label">📍 City:</span>
              <select
                className="city-select-dropdown"
                value={selectedCity}
                onChange={(e) => setSelectedCity(e.target.value)}
              >
                {INDIAN_CITIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div className="am-pm-toggle-wrap">
              <button
                type="button"
                className={`time-toggle-btn ${timeOfDay === 'morning' ? 'active' : ''}`}
                onClick={() => setTimeOfDay('morning')}
              >
                <SunIcon size={14} />
                <span>Morning</span>
              </button>
              <button
                type="button"
                className={`time-toggle-btn ${timeOfDay === 'evening' ? 'active' : ''}`}
                onClick={() => setTimeOfDay('evening')}
              >
                <MoonIcon size={14} />
                <span>Evening</span>
              </button>
            </div>
          </div>
        </div>

        {/* Environmental Metrics Trio */}
        <div className="env-metrics-trio">
          <div className="env-metric-item">
            <div className="metric-icon-wrap amber">
              <SunIcon size={18} />
            </div>
            <div>
              <span className="metric-top-val">UV Index: {env.uv_index ?? 6} &bull; {env.uv_severity || 'Moderate'}</span>
              <span className="metric-bot-label">Solar UV Exposure</span>
            </div>
          </div>

          <div className="env-metric-item">
            <div className="metric-icon-wrap cyan">
              <DropletIcon size={18} />
            </div>
            <div>
              <span className="metric-top-val">{env.humidity ?? 55}% Humidity</span>
              <span className="metric-bot-label">Air Moisture Balance</span>
            </div>
          </div>

          <div className="env-metric-item">
            <div className="metric-icon-wrap neutral">
              <WindIcon size={18} />
            </div>
            <div>
              <span className="metric-top-val">{env.temperature ?? 28}°C &bull; {env.condition || 'Clear'}</span>
              <span className="metric-bot-label">Local Ambient Temp</span>
            </div>
          </div>
        </div>

        {/* Environmental Skincare Reminder (Non-Medical) */}
        {env.reminder && (
          <div className="env-reminder-strip">
            <SparklesIcon size={16} className="reminder-icon" />
            <span className="reminder-text">{env.reminder}</span>
          </div>
        )}
      </div>

      {/* 3. ADAPTIVE ROUTINE GUIDANCE BANNER (Tolerance Feedback) */}
      {adaptiveGuidance && adaptiveGuidance.has_warning && (
        <div className="adaptive-guidance-card caution">
          <AlertTriangleIcon size={20} className="guidance-icon" />
          <div className="guidance-content">
            <h4 className="guidance-title">{adaptiveGuidance.title}</h4>
            <p className="guidance-message">{adaptiveGuidance.message}</p>
            {adaptiveGuidance.recommendation && (
              <span className="guidance-tip">💡 Recommendation: {adaptiveGuidance.recommendation}</span>
            )}
          </div>
        </div>
      )}

      {adaptiveGuidance && !adaptiveGuidance.has_warning && adaptiveGuidance.status === 'optimal' && (
        <div className="adaptive-guidance-card success">
          <ShieldCheckIcon size={18} className="guidance-icon text-emerald" />
          <div className="guidance-content">
            <h4 className="guidance-title">{adaptiveGuidance.title}</h4>
            <p className="guidance-message">{adaptiveGuidance.message}</p>
          </div>
        </div>
      )}

      {/* 4. DIVIDED TODAY'S ROUTINE: ☀️ MORNING & 🌙 EVENING */}
      <div className="today-routines-container">
        {/* MORNING ROUTINE */}
        <div className="routine-session-block">
          <div className="session-heading-row morning">
            <div className="session-heading-left">
              <SunIcon size={20} className="session-icon" />
              <div>
                <h2 className="session-title">☀️ MORNING ROUTINE</h2>
                <span className="session-subtitle">Hydrate, protect, and fortify against daytime solar exposure.</span>
              </div>
            </div>
            <span className="session-count-badge">{morningTasks.length} Tasks</span>
          </div>

          <div className="session-tasks-list">
            {morningTasks.length === 0 ? (
              <div className="empty-tasks-message">No morning formulas scheduled for today.</div>
            ) : (
              morningTasks.map((task) => (
                <TaskActionCard
                  key={`am-${task.step_id}`}
                  task={task}
                  session="morning"
                  saving={savingStepId === `morning-${task.step_id}`}
                  deleting={deletingStepId === task.step_id}
                  onToggle={() => handleToggleStep(task.step_id, task.completed, task.suitability, 'morning')}
                  onDelete={() => handleDeleteStep(task.step_id, task.product_name)}
                />
              ))
            )}
          </div>
        </div>

        {/* EVENING ROUTINE */}
        <div className="routine-session-block">
          <div className="session-heading-row evening">
            <div className="session-heading-left">
              <MoonIcon size={20} className="session-icon" />
              <div>
                <h2 className="session-title">🌙 EVENING ROUTINE</h2>
                <span className="session-subtitle">Cleanse, repair, and apply cellular renewal treatments overnight.</span>
              </div>
            </div>
            <span className="session-count-badge">{eveningTasks.length} Tasks</span>
          </div>

          <div className="session-tasks-list">
            {eveningTasks.length === 0 ? (
              <div className="empty-tasks-message">No evening formulas scheduled for today.</div>
            ) : (
              eveningTasks.map((task) => (
                <TaskActionCard
                  key={`pm-${task.step_id}`}
                  task={task}
                  session="evening"
                  saving={savingStepId === `evening-${task.step_id}`}
                  deleting={deletingStepId === task.step_id}
                  onToggle={() => handleToggleStep(task.step_id, task.completed, task.suitability, 'evening')}
                  onDelete={() => handleDeleteStep(task.step_id, task.product_name)}
                />
              ))
            )}
          </div>
        </div>

      </div>

      {/* 5. DAILY SKIN FEEDBACK (Lightweight 1-Click Interaction) */}
      <div className="daily-skin-feedback-card">
        <div className="feedback-card-header">
          <div className="feedback-title-box">
            <SparklesIcon size={18} />
            <h3>How did your skin feel today?</h3>
          </div>
          <span className="feedback-subtext">
            1-click daily feedback tunes your routine's progressive pace.
          </span>
        </div>

        <div className="feedback-options-row">
          <button
            type="button"
            className={`feedback-choice-btn ${todaySkinFeel === 'comfortable' ? 'selected' : ''}`}
            onClick={() => handleSkinFeedback('comfortable')}
            disabled={submittingFeedback}
          >
            <span className="feedback-emoji">😊</span>
            <span className="feedback-label">Comfortable</span>
          </button>

          <button
            type="button"
            className={`feedback-choice-btn ${todaySkinFeel === 'dry' ? 'selected' : ''}`}
            onClick={() => handleSkinFeedback('dry')}
            disabled={submittingFeedback}
          >
            <span className="feedback-emoji">😐</span>
            <span className="feedback-label">A little dry</span>
          </button>

          <button
            type="button"
            className={`feedback-choice-btn ${todaySkinFeel === 'irritated' ? 'selected' : ''}`}
            onClick={() => handleSkinFeedback('irritated')}
            disabled={submittingFeedback}
          >
            <span className="feedback-emoji">😣</span>
            <span className="feedback-label">Irritated</span>
          </button>
        </div>

        {feedbackSuccess && (
          <div className="feedback-saved-toast">
            <CheckCircleIcon size={14} />
            <span>Tolerance feedback logged! Your routine timeline is adapting.</span>
          </div>
        )}
      </div>

      {/* 6. AUTO-REORDER STATUS & TEST CONTROLS */}
      <div className="tracker-footer-card">
        <div className="auto-reorder-flex-row">
          <div className="auto-reorder-info">
            <h4 className="footer-card-heading">
              Automatic Replenishment on Routine Completion
            </h4>
            <p className="footer-card-sub">
              {autoReorderOn
                ? "When your multi-week routine reaches 100%, Joyory automatically schedules delivery refills."
                : "Automatic replenishment is currently off. You can toggle this setting anytime."}
            </p>
          </div>

          <div className="auto-reorder-actions">
            <span className={`setting-pill ${autoReorderOn ? 'on' : 'off'}`}>
              {autoReorderOn ? 'AUTO-REORDER: ON' : 'AUTO-REORDER: OFF'}
            </span>
            <button
              type="button"
              className="btn-toggle-reorder"
              onClick={handleToggleAutoReorder}
              disabled={togglingReorder}
            >
              {togglingReorder ? 'Updating...' : (autoReorderOn ? 'Turn Off' : 'Turn On')}
            </button>
          </div>
        </div>

        {/* Auto-reordered confirmation banner */}
        {autoReordered && (
          <div className="auto-reordered-success-strip">
            <ShieldCheckIcon size={18} />
            <span>
              🎉 Refill Order #{progressData?.auto_reorder_order_id} automatically confirmed upon completion!
            </span>
            <button
              type="button"
              className="btn-link-white"
              onClick={onGoToDelivery}
            >
              View Tracking &rarr;
            </button>
          </div>
        )}

        {/* Instant Routine Completion Test Button */}
        {!isCompleted && (
          <div className="test-action-bar">
            <span className="test-desc-text">Demonstration Helper:</span>
            <button
              type="button"
              className="btn-complete-all-test"
              onClick={handleCompleteAll}
              disabled={completingAll}
              title="Instantly mark all steps across all 3 stages complete to evaluate auto-reorder trigger"
            >
              <CheckCircleIcon size={14} />
              <span>{completingAll ? 'Completing...' : 'Complete All Steps (Test Auto-Reorder)'}</span>
            </button>
          </div>
        )}
      </div>

      {/* Skin Tolerance Feedback Modal */}
      <SkinFeedbackModal
        isOpen={isFeedbackModalOpen}
        onClose={() => setIsFeedbackModalOpen(false)}
        taskData={feedbackTaskData}
        onSubmitFeedback={async (feel, notes) => {
          await submitDailySkinFeedback(routineId, feel, notes);
          await loadProgress();
        }}
      />
    </div>
  );
}

/**
 * Individual Task Action Card for Morning / Evening Routine Lists
 */
function TaskActionCard({ task, saving, deleting, onToggle, onDelete }) {
  const isCompleted = task.completed;
  const isNotRecommended = task.suitability === 'not_recommended';

  return (
    <div className={`daily-task-action-card ${isCompleted ? 'is-completed' : ''} ${isNotRecommended ? 'is-flagged' : ''}`}>
      {/* Product Image */}
      <div className="task-img-wrap">
        {task.image_url ? (
          <img
            src={task.image_url}
            alt={task.product_name}
            className="task-thumb-img"
            loading="lazy"
          />
        ) : (
          <div className="task-thumb-fallback">
            <SparklesIcon size={18} />
          </div>
        )}
      </div>

      {/* Task Content */}
      <div className="task-body-col">
        <div className="task-tags-row">
          <span className="task-cat-badge">{task.category}</span>
          <span className="task-freq-badge">{task.frequency?.replace(/_/g, ' ')}</span>
          {task.time_of_day && (
            <span className="task-time-badge">{task.time_of_day}</span>
          )}

          {/* Environmental Suitability Indicator */}
          {task.suitability === 'optimal' && (
            <span className="suitability-pill optimal">🟢 Recommended Now</span>
          )}
          {task.suitability === 'not_recommended' && (
            <span className="suitability-pill danger">⛔ Do Not Use Now</span>
          )}
          {task.suitability === 'caution' && (
            <span className="suitability-pill caution">⚠️ Use with Caution</span>
          )}
        </div>

        <h4 className="task-product-title">{task.product_name}</h4>

        {/* Environmental reason / guidance */}
        {task.suitability_reason && (
          <p className="task-advice-text">
            {task.suitability_reason}
          </p>
        )}
      </div>

      {/* Task Completion Action */}
      <div className="task-action-col">
        {isCompleted ? (
          <div className="completed-state-badge locked" title="Completed for today — automatically resets tomorrow">
            <div className="completed-lock-icon">
              <CheckCircleIcon size={18} className="text-emerald" />
            </div>
            <div className="completed-details">
              <span className="completed-label">✓ Completed</span>
              {task.completed_at && (
                <span className="completed-time">{task.completed_at}</span>
              )}
            </div>
          </div>
        ) : (
          <button
            type="button"
            className={`btn-mark-complete ${isNotRecommended ? 'warning-btn' : ''}`}
            onClick={onToggle}
            disabled={saving || deleting}
          >
            <span>{saving ? 'Updating...' : 'Mark Complete'}</span>
          </button>
        )}


        <button
          type="button"
          className="btn-delete-tracker-task"
          onClick={onDelete}
          disabled={saving || deleting}
          title={`Delete ${task.product_name} from daily tracker & routine`}
        >
          <TrashIcon size={14} />
        </button>
      </div>
    </div>
  );
}


