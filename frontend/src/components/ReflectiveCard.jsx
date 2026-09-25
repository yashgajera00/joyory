import React, { useCallback, useEffect, useRef, useState } from 'react';
import './ReflectiveCard.css';
import { analyzeSkin } from '../services/skinAnalysis';
import bgImage from '../assets/bg.png';

// ─── Scanning text carousel ────────────────────────────────────────────────
const SCAN_TEXTS = [
  'SCANNING FACE...',
  'ANALYZING SKIN...',
  'CHECKING SKIN TEXTURE...',
  'IDENTIFYING SKIN TYPE...',
  'DETECTING HYDRATION...',
  'GENERATING SKIN PROFILE...',
  'ALMOST THERE...',
];

// ─── Metric display helpers ────────────────────────────────────────────────
function formatMetricValue(metric) {
  if (!metric) return null;
  if (typeof metric === 'string' || typeof metric === 'number') return String(metric);
  return (
    metric.level ??
    metric.value ??
    metric.score ??
    metric.status ??
    null
  );
}

function MetricChip({ label, metric }) {
  const value = formatMetricValue(metric);
  if (!value) return null;

  const score = typeof metric === 'object' ? metric.score : null;
  const severity =
    typeof metric === 'object'
      ? (metric.level ?? metric.value ?? '').toString().toLowerCase()
      : value.toString().toLowerCase();

  let chipClass = 'metric-chip';
  if (severity === 'high' || severity === 'very high') chipClass += ' chip-high';
  else if (severity === 'low' || severity === 'very low') chipClass += ' chip-low';
  else chipClass += ' chip-moderate';

  return (
    <div className={chipClass}>
      <span className="chip-label">{label}</span>
      <span className="chip-value">{value}</span>
      {score != null && (
        <div className="chip-bar-track">
          <div
            className="chip-bar-fill"
            style={{ width: `${Math.min(100, Math.max(0, Number(score)))}%` }}
          />
        </div>
      )}
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────────
const ReflectiveCard = ({
  blurStrength = 12,
  color = 'white',
  metalness = 1,
  roughness = 0.75,
  overlayColor = 'rgba(0, 0, 0, 0.2)',
  displacementStrength = 20,
  noiseScale = 1,
  specularConstant = 0,
  grayscale = 0.15,
  glassDistortion = 30,
  className = '',
  style = {},
  user,
  onAddToCart,
  onAnalysisComplete,
  onResetAnalysis,
  onViewRecommendations,
}) => {
  const getStorageKey = (u) => (u ? `joyory_skin_analysis_${u.id || u.username}` : 'joyory_skin_analysis_guest');

  const [uiState, setUiState] = useState(() => {
    try {
      const key = getStorageKey(user);
      const saved = localStorage.getItem(key);
      return saved ? 'result' : 'idle';
    } catch {
      return 'idle';
    }
  }); // idle | camera | analyzing | result | error
  const [scanTextIdx, setScanTextIdx] = useState(0);
  const [capturedImageUrl, setCapturedImageUrl] = useState(null);
  const [capturedBlob, setCapturedBlob] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(() => {
    try {
      const key = getStorageKey(user);
      const saved = localStorage.getItem(key);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [errorMsg, setErrorMsg] = useState('');
  const [longWait, setLongWait] = useState(false);

  // Sync analysis result and card state whenever active user changes
  useEffect(() => {
    try {
      const key = getStorageKey(user);
      const saved = localStorage.getItem(key);
      const parsed = saved ? JSON.parse(saved) : null;
      setAnalysisResult(parsed);
      setUiState(parsed ? 'result' : 'idle');
    } catch {
      setAnalysisResult(null);
      setUiState('idle');
    }
  }, [user]);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const scanIntervalRef = useRef(null);
  const longWaitTimerRef = useRef(null);

  const baseFrequency = 0.03 / Math.max(0.1, noiseScale);
  const saturation = 1 - Math.max(0, Math.min(1, grayscale));

  // ── Scanning text animation ──────────────────────────────────────────────
  useEffect(() => {
    if (uiState === 'idle' || uiState === 'analyzing') {
      scanIntervalRef.current = setInterval(() => {
        setScanTextIdx(i => (i + 1) % SCAN_TEXTS.length);
      }, 1800);
    }
    return () => clearInterval(scanIntervalRef.current);
  }, [uiState]);

  // ── Camera management ────────────────────────────────────────────────────
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
  }, []);

  const startCamera = useCallback(async () => {
    stopCamera();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setUiState('camera');
      setErrorMsg('');
    } catch (err) {
      let msg = 'Camera access is required for skin analysis.';
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        msg = 'Camera access was denied. Please allow camera permission and try again.';
      } else if (err.name === 'NotFoundError') {
        msg = 'No camera found on this device.';
      }
      setErrorMsg(msg);
      setUiState('error');
    }
  }, [stopCamera]);

  // ── Capture photo ────────────────────────────────────────────────────────
  const capturePhoto = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const w = video.videoWidth || 640;
    const h = video.videoHeight || 480;
    canvas.width = w;
    canvas.height = h;

    const ctx = canvas.getContext('2d');
    // Mirror the image to match user-facing camera
    ctx.save();
    ctx.scale(-1, 1);
    ctx.drawImage(video, -w, 0, w, h);
    ctx.restore();

    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    setCapturedImageUrl(dataUrl);

    canvas.toBlob(
      blob => {
        setCapturedBlob(blob);
        stopCamera();
        setUiState('analyzing');
        sendForAnalysis(blob);
      },
      'image/jpeg',
      0.9
    );
  }, [stopCamera]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Send to Django ───────────────────────────────────────────────────────
  const sendForAnalysis = useCallback(async (blob) => {
    setLongWait(false);
    longWaitTimerRef.current = setTimeout(() => setLongWait(true), 8000);

    try {
      const result = await analyzeSkin(blob);
      clearTimeout(longWaitTimerRef.current);
      setAnalysisResult(result);
      setUiState('result');
      try {
        const key = getStorageKey(user);
        localStorage.setItem(key, JSON.stringify(result));
      } catch (e) {
        console.warn('LocalStorage save notice:', e);
      }
      if (onAnalysisComplete) {
        onAnalysisComplete(result);
      }
    } catch (err) {
      clearTimeout(longWaitTimerRef.current);
      setErrorMsg('Face not recognized. Please try again.');
      setUiState('error');
    }
  }, [onAnalysisComplete, user]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Retake flow ──────────────────────────────────────────────────────────
  const handleRetake = useCallback(() => {
    setAnalysisResult(null);
    setCapturedImageUrl(null);
    setCapturedBlob(null);
    setErrorMsg('');
    setLongWait(false);
    try {
      const key = getStorageKey(user);
      localStorage.removeItem(key);
    } catch (e) {
      console.warn('LocalStorage clear notice:', e);
    }
    if (onResetAnalysis) {
      onResetAnalysis();
    }
    startCamera();
  }, [startCamera, onResetAnalysis, user]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Cancel / Reset flow (returns to idle card) ───────────────────────────
  const handleCancel = useCallback(() => {
    stopCamera();
    setAnalysisResult(null);
    setCapturedImageUrl(null);
    setCapturedBlob(null);
    setErrorMsg('');
    setLongWait(false);
    setUiState('idle');
    try {
      const key = getStorageKey(user);
      localStorage.removeItem(key);
    } catch (e) {
      console.warn('LocalStorage clear notice:', e);
    }
    if (onResetAnalysis) {
      onResetAnalysis();
    }
  }, [stopCamera, onResetAnalysis, user]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Cleanup on unmount ───────────────────────────────────────────────────
  useEffect(() => {
    return () => {
      stopCamera();
      clearTimeout(longWaitTimerRef.current);
      clearInterval(scanIntervalRef.current);
    };
  }, [stopCamera]);

  // ── CSS variable bag ─────────────────────────────────────────────────────
  const cssVars = {
    '--blur-strength': `${blurStrength}px`,
    '--metalness': metalness,
    '--roughness': roughness,
    '--overlay-color': overlayColor,
    '--text-color': color,
    '--saturation': saturation,
  };

  const isScanning = uiState === 'analyzing';
  const showBlur = uiState === 'analyzing';
  const showNoise = uiState === 'idle' || uiState === 'analyzing';

  return (
    <div className="skin-card-wrapper">
      <div
        className={`reflective-card-container skin-card ${className}`}
        style={{ ...style, ...cssVars }}
      >
      {/* ── SVG Filters (always mounted) ──────────────────────────────── */}
      <svg className="reflective-svg-filters" aria-hidden="true">
        <defs>
          <filter id="metallic-displacement" x="-20%" y="-20%" width="140%" height="140%">
            <feTurbulence type="turbulence" baseFrequency={baseFrequency} numOctaves="2" result="noise" />
            <feColorMatrix in="noise" type="luminanceToAlpha" result="noiseAlpha" />
            <feDisplacementMap in="SourceGraphic" in2="noise" scale={displacementStrength}
              xChannelSelector="R" yChannelSelector="G" result="rippled" />
            <feSpecularLighting in="noiseAlpha" surfaceScale={displacementStrength}
              specularConstant={specularConstant} specularExponent="20"
              lightingColor="#ffffff" result="light">
              <fePointLight x="0" y="0" z="300" />
            </feSpecularLighting>
            <feComposite in="light" in2="rippled" operator="in" result="light-effect" />
            <feBlend in="light-effect" in2="rippled" mode="screen" result="metallic-result" />
            <feColorMatrix in="SourceAlpha" type="matrix"
              values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="solidAlpha" />
            <feMorphology in="solidAlpha" operator="erode" radius="45" result="erodedAlpha" />
            <feGaussianBlur in="erodedAlpha" stdDeviation="10" result="blurredMap" />
            <feComponentTransfer in="blurredMap" result="glassMap">
              <feFuncA type="linear" slope="0.5" intercept="0" />
            </feComponentTransfer>
            <feDisplacementMap in="metallic-result" in2="glassMap" scale={glassDistortion}
              xChannelSelector="A" yChannelSelector="A" result="final" />
          </filter>
        </defs>
      </svg>

      {/* ── Background layer: idle = noise+SVG, camera = clean video, analyzing = blurred capture ── */}

      {/* Live camera video (camera state only — NO blur/filter) */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className={`reflective-video skin-live-video ${uiState === 'camera' ? 'visible' : 'hidden'}`}
        style={{ transform: 'scaleX(-1)', filter: 'none' }}
      />

      {/* Captured photo (analyzing + result states) */}
      {capturedImageUrl && (uiState === 'analyzing' || uiState === 'result') && (
        <div
          className={`skin-captured-bg ${showBlur ? 'captured-blurred' : 'captured-clear'}`}
          style={{ backgroundImage: `url(${capturedImageUrl})` }}
        />
      )}

      {/* Idle background — custom AI analysis illustration from assets/bg.png */}
      {uiState === 'idle' && (
        <div
          className="skin-idle-bg"
          style={{ backgroundImage: `url(${bgImage})` }}
        />
      )}

      {/* Noise texture overlay */}
      {showNoise && <div className="reflective-noise" />}

      {/* Metallic sheen */}
      <div className={`reflective-sheen ${uiState === 'result' ? 'sheen-dim' : ''}`} />

      {/* Glass border always */}
      <div className="reflective-border" />

      {/* ── Content layers ────────────────────────────────────────────── */}
      <div className="reflective-content skin-content">

        {/* ─────────────── STATE: IDLE ─────────────────────────────── */}
        {uiState === 'idle' && (
          <div className="skin-idle-state">
            <div className="skin-ai-badge">
              <span className="skin-ai-dot" />
              <span>AI SKIN ANALYSIS</span>
            </div>

            <div className="skin-scan-text-wrapper">
              <div className="skin-scan-lines">
                <div className="scan-corner tl" />
                <div className="scan-corner tr" />
                <div className="scan-corner bl" />
                <div className="scan-corner br" />
                <div className="scan-center-dot" />
              </div>
            </div>

            <div className="skin-idle-cta">
              <button
                id="analyze-skin-btn"
                className="skin-cta-btn"
                onClick={startCamera}
              >
                <span className="btn-icon">◉</span>
                Analyze My Skin
              </button>
              <p className="skin-privacy-note">
                Your photo is analyzed to generate cosmetic skincare insights.
              </p>
            </div>
          </div>
        )}

        {/* ─────────────── STATE: CAMERA ───────────────────────────── */}
        {uiState === 'camera' && (
          <div className="skin-camera-state">
            <div className="skin-ai-badge badge-live">
              <span className="skin-ai-dot dot-live" />
              <span>LIVE CAMERA</span>
            </div>

            {/* Face oval guide */}
            <div className="face-oval-guide">
              <div className="oval-ring" />
              <p className="oval-hint">Position your face here</p>
            </div>

            <button
              id="capture-photo-btn"
              className="skin-capture-btn"
              onClick={capturePhoto}
            >
              <span className="capture-ring" />
              <span className="capture-dot" />
            </button>
            <p className="capture-label">TAP TO CAPTURE</p>
          </div>
        )}

        {/* ─────────────── STATE: ANALYZING ────────────────────────── */}
        {uiState === 'analyzing' && (
          <div className="skin-analyzing-state">
            <div className="skin-ai-badge badge-scanning">
              <span className="skin-ai-dot dot-scanning" />
              <span>ANALYZING</span>
            </div>

            {/* Scan line animation */}
            <div className="scan-overlay">
              <div className="scan-line" />
              <div className="scan-grid" />
            </div>

            <div className="scan-text-carousel">
              {SCAN_TEXTS.map((t, i) => (
                <span
                  key={t}
                  className={`scan-text-item ${i === scanTextIdx ? 'active' : ''}`}
                >
                  {t}
                </span>
              ))}
            </div>

            {longWait && (
              <p className="skin-long-wait">Still analyzing your skin...</p>
            )}
          </div>
        )}

        {/* ─────────────── STATE: RESULT ───────────────────────────── */}
        {uiState === 'result' && analysisResult && (
          <div className="skin-result-state">
            <div className="result-header">
              <div className="skin-ai-badge badge-done">
                <span className="skin-ai-dot dot-done" />
                <span>ANALYSIS COMPLETE</span>
              </div>
              {analysisResult.analysis?.overall_health_score != null && (
                <div className="health-score-circle">
                  <span className="health-score-num">
                    {Math.round(analysisResult.analysis.overall_health_score)}
                  </span>
                  <span className="health-score-label">SKIN HEALTH</span>
                </div>
              )}
            </div>

            <div className="result-section-title">YOUR SKIN ANALYSIS</div>

            <div className="metrics-grid">
              {analysisResult.analysis?.skin_type && (
                <MetricChip label="Skin Type" metric={analysisResult.analysis.skin_type} />
              )}
              {Object.entries(analysisResult.analysis?.metrics || {}).map(([key, val]) => (
                <MetricChip
                  key={key}
                  label={key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  metric={val}
                />
              ))}
            </div>
          </div>
        )}

        {/* ─────────────── STATE: ERROR ────────────────────────────── */}
        {uiState === 'error' && (
          <div className="skin-error-state">
            <div className="skin-ai-badge badge-error">
              <span className="skin-ai-dot dot-error" />
              <span>ANALYSIS FAILED</span>
            </div>

            <div className="error-icon">⚠</div>
            <p className="error-message">{errorMsg || 'Something went wrong.'}</p>

            <div className="error-actions">
              {capturedBlob && (
                <button
                  id="retry-analysis-btn"
                  className="skin-cta-btn btn-secondary"
                  onClick={() => {
                    setUiState('analyzing');
                    sendForAnalysis(capturedBlob);
                  }}
                >
                  Try Again
                </button>
              )}
              <button
                id="retake-error-btn"
                className="skin-cta-btn"
                onClick={handleRetake}
              >
                Retake Photo
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Hidden canvas for capture */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>

    {/* ── Actions below the card (result state only) ── */}
    {uiState === 'result' && analysisResult && (
      <div className="card-below-actions">
        <button
          id="view-recommendations-btn"
          className="btn-view-recommendations"
          onClick={() => {
            if (onViewRecommendations) {
              onViewRecommendations(analysisResult);
            }
          }}
        >
          <span className="reco-btn-sparkle">✦</span>
          <span>View Recommendations</span>
          <span className="reco-btn-arrow">↓</span>
        </button>
        <button
          id="cancel-scan-btn"
          className="btn-card-cancel"
          onClick={handleCancel}
        >
          ✕ Cancel
        </button>
      </div>
    )}
  </div>
  );
};

export default ReflectiveCard;
