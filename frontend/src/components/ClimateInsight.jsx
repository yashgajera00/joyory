import React, { useState, useEffect } from 'react';
import { SunIcon, CloudIcon, DropletIcon, WindIcon, SparklesIcon, BagIcon, RefreshCwIcon } from './Icons';
import { fetchCartClimateAnalysis } from '../services/api';
import { formatRupees } from '@/lib/utils';

export default function ClimateInsight({ onAddProduct }) {
  const [climateData, setClimateData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [locationStatus, setLocationStatus] = useState('detecting'); // 'detecting' | 'granted' | 'fallback'

  const loadClimate = async (coords = {}, city = null) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCartClimateAnalysis(coords, city);
      setClimateData(data);
    } catch (err) {
      setError(err.message || 'Unable to retrieve environmental data.');
    } finally {
      setLoading(false);
    }
  };

  const detectLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus('fallback');
      loadClimate();
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocationStatus('granted');
        loadClimate({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
        });
      },
      () => {
        // Location denied or unavailable: gracefully use backend fallback
        setLocationStatus('fallback');
        loadClimate();
      },
      { timeout: 4000 }
    );
  };

  useEffect(() => {
    detectLocation();
  }, []);

  const getUvBadgeClass = (uv) => {
    if (uv >= 8) return 'badge-uv-extreme';
    if (uv >= 6) return 'badge-uv-high';
    return 'badge-uv-mod';
  };

  const getAqiBadgeClass = (aqi) => {
    if (aqi >= 150) return 'badge-aqi-poor';
    if (aqi >= 100) return 'badge-aqi-mod';
    return 'badge-aqi-good';
  };

  return (
    <div className="climate-insight-panel">
      <div className="climate-panel-header">
        <div className="climate-title-group">
          <SunIcon size={24} className="text-amber" />
          <div>
            <h3 className="climate-heading">Hyper-Local Climate Skin Adaptation</h3>
            <p className="climate-subtext">
              Real-time temperature, humidity, UV index & air quality considerations for your routine.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="btn-refresh-climate"
          onClick={detectLocation}
          disabled={loading}
          title="Refresh weather analysis"
        >
          <RefreshCwIcon size={14} className={loading ? 'animate-spin' : ''} />
          <span>{loading ? 'Analyzing...' : 'Refresh Insights'}</span>
        </button>
      </div>

      {loading && !climateData ? (
        <div className="climate-loading-skeleton">
          <div className="skeleton-line"></div>
          <div className="skeleton-grid"></div>
        </div>
      ) : error && !climateData ? (
        <div className="climate-error-fallback">
          <p>{error}</p>
          <button className="btn-secondary btn-sm" onClick={() => loadClimate()}>
            Use Default Climate Profile
          </button>
        </div>
      ) : climateData && climateData.climate ? (
        <div className="climate-content">
          {/* Weather Metrics Strip */}
          <div className="weather-metrics-strip">
            <div className="metric-box">
              <SunIcon size={18} className="metric-icon" />
              <div className="metric-data">
                <span className="metric-val">{climateData.climate.temperature}°C</span>
                <span className="metric-label">{climateData.climate.condition || 'Clear'}</span>
              </div>
            </div>

            <div className="metric-box">
              <DropletIcon size={18} className="metric-icon text-cyan" />
              <div className="metric-data">
                <span className="metric-val">{climateData.climate.humidity}%</span>
                <span className="metric-label">Air Moisture</span>
              </div>
            </div>

            <div className="metric-box">
              <SunIcon size={18} className="metric-icon text-amber" />
              <div className="metric-data">
                <span className={`metric-badge ${getUvBadgeClass(climateData.climate.uv_index)}`}>
                  Index {climateData.climate.uv_index}
                </span>
                <span className="metric-label">UV Exposure</span>
              </div>
            </div>

            <div className="metric-box">
              <WindIcon size={18} className="metric-icon text-purple" />
              <div className="metric-data">
                <span className={`metric-badge ${getAqiBadgeClass(climateData.climate.aqi)}`}>
                  AQI {climateData.climate.aqi}
                </span>
                <span className="metric-label">Air Particulate</span>
              </div>
            </div>
          </div>

          {/* Environmental Adaptation Suggestions */}
          {climateData.suggestions && climateData.suggestions.length > 0 && (
            <div className="climate-suggestions-list">
              {climateData.suggestions.map((sug, idx) => (
                <div key={idx} className="suggestion-card">
                  <div className="sug-header">
                    <SparklesIcon size={16} className="text-amber" />
                    <strong>{sug.title}</strong>
                  </div>
                  <p className="sug-message">{sug.message}</p>
                </div>
              ))}
            </div>
          )}

          {/* Climate Recommended Formulas */}
          {climateData.alternative_products && climateData.alternative_products.length > 0 && (
            <div className="climate-recommendations-row">
              <span className="rec-header-label">Recommended for Current Climate:</span>
              <div className="rec-products-list">
                {climateData.alternative_products.map((rec) => (
                  <div key={rec.product_id} className="rec-chip">
                    <div className="rec-chip-info">
                      <span className="rec-name">{rec.name}</span>
                      <span className="rec-price">{formatRupees(rec.price)}</span>
                    </div>
                    {onAddProduct && (
                      <button
                        className="rec-add-btn"
                        onClick={() => onAddProduct(rec.product_id)}
                        title="Add recommended formula to cart"
                      >
                        <BagIcon size={12} />
                        <span>Add</span>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
