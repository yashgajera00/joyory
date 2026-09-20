import React, { useState } from 'react';
import { UserIcon, LockIcon, MailIcon, LogOutIcon, SparklesIcon, ArrowRightIcon, CheckCircleIcon } from './Icons';
import { loginUser, registerUser, logoutUser } from '../services/auth';

export default function AuthPage({
  user,
  onAuthSuccess,
  onLogoutSuccess,
  onGoToShop,
  onGoToRoutine,
  onGoToCart,
}) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Login form state
  const [loginIdentifier, setLoginIdentifier] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Register form state
  const [regFirstName, setRegFirstName] = useState('');
  const [regLastName, setRegLastName] = useState('');
  const [regUsername, setRegUsername] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');

  // Quick fill demo account
  const handleFillDemo = () => {
    setLoginIdentifier('demouser');
    setLoginPassword('demopassword123');
    setError('');
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    if (!loginIdentifier.trim() || !loginPassword) {
      setError('Please enter your username or email and password.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const data = await loginUser(loginIdentifier.trim(), loginPassword);
      if (onAuthSuccess) {
        onAuthSuccess(data.user, data.message || 'Logged in successfully.');
      }
    } catch (err) {
      setError(err.message || 'Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    if (!regUsername.trim()) {
      setError('Please choose a username.');
      return;
    }
    if (!regEmail.trim()) {
      setError('Please enter your email address.');
      return;
    }
    if (!regPassword || regPassword.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const data = await registerUser({
        username: regUsername.trim(),
        email: regEmail.trim(),
        password: regPassword,
        first_name: regFirstName.trim(),
        last_name: regLastName.trim(),
      });
      if (onAuthSuccess) {
        onAuthSuccess(data.user, data.message || 'Account created successfully!');
      }
    } catch (err) {
      setError(err.message || 'Registration failed. Please check your information.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogoutClick = async () => {
    setLoading(true);
    try {
      await logoutUser();
      if (onLogoutSuccess) {
        onLogoutSuccess();
      }
    } finally {
      setLoading(false);
    }
  };

  // ── If user is already authenticated: Show Account Profile Card with Logout ──
  if (user) {
    const initials = (user.first_name?.[0] || user.username?.[0] || 'J').toUpperCase();

    return (
      <section className="auth-section">
        <div className="auth-card-container logged-in-card">
          <div className="profile-header-box">
            <div className="profile-avatar-circle">
              <span>{initials}</span>
            </div>
            <div className="profile-badge-row">
              <span className="profile-vip-pill">
                <SparklesIcon size={13} />
                <span>Joyory VIP Member</span>
              </span>
            </div>
            <h2 className="profile-name-heading">
              {user.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : user.username}
            </h2>
            <p className="profile-email-sub">{user.email || `@${user.username}`}</p>
          </div>

          <div className="profile-details-grid">
            <div className="profile-detail-item">
              <span className="profile-detail-label">Username</span>
              <span className="profile-detail-value">@{user.username}</span>
            </div>
            <div className="profile-detail-item">
              <span className="profile-detail-label">Email</span>
              <span className="profile-detail-value">{user.email || 'Not provided'}</span>
            </div>
            <div className="profile-detail-item">
              <span className="profile-detail-label">Routine Safety Status</span>
              <span className="profile-detail-value active-synergy-text">
                <CheckCircleIcon size={14} />
                <span>Active Conflict Defense</span>
              </span>
            </div>
            <div className="profile-detail-item">
              <span className="profile-detail-label">Member ID</span>
              <span className="profile-detail-value">#JOY-{user.id?.toString().padStart(4, '0')}</span>
            </div>
          </div>

          <div className="profile-quick-actions">
            <button className="btn-profile-action" onClick={onGoToShop}>
              <span>Shop Smart Catalog</span>
              <ArrowRightIcon size={16} />
            </button>
            {onGoToRoutine && (
              <button className="btn-profile-action btn-profile-secondary" onClick={onGoToRoutine}>
                <span>View Routine Timeline</span>
              </button>
            )}
            {onGoToCart && (
              <button className="btn-profile-action btn-profile-secondary" onClick={onGoToCart}>
                <span>Review Shopping Bag</span>
              </button>
            )}
          </div>

          <div className="profile-logout-divider" />

          <button
            id="logout-btn"
            className="btn-auth-logout"
            onClick={handleLogoutClick}
            disabled={loading}
          >
            <LogOutIcon size={18} />
            <span>{loading ? 'Signing out...' : 'Sign Out of Joyory'}</span>
          </button>
        </div>
      </section>
    );
  }

  // ── Not authenticated: Show Login / Register Tabs & Forms ──
  return (
    <section className="auth-section">
      <div className="auth-card-container">
        {/* Brand header */}
        <div className="auth-brand-header">
          <div className="auth-brand-pill">
            <SparklesIcon size={14} />
            <span>Intelligent Skincare Portal</span>
          </div>
          <h1 className="auth-title">
            {mode === 'login' ? 'Welcome Back to Joyory' : 'Create Your Joyory Profile'}
          </h1>
          <p className="auth-subtitle">
            {mode === 'login'
              ? 'Sign in to access your customized routines, saved biomarker analysis, and active conflict defense.'
              : 'Join Joyory to unlock progressive habit building, hyper-local climate adaptation, and clinical synergy.'}
          </p>
        </div>

        {/* Mode Switch Tabs */}
        <div className="auth-tabs-bar">
          <button
            type="button"
            className={`auth-tab-btn ${mode === 'login' ? 'active' : ''}`}
            onClick={() => {
              setMode('login');
              setError('');
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab-btn ${mode === 'register' ? 'active' : ''}`}
            onClick={() => {
              setMode('register');
              setError('');
            }}
          >
            Create Account
          </button>
        </div>

        {/* Error Callout */}
        {error && (
          <div className="auth-error-banner" role="alert">
            <span className="auth-error-icon">⚠️</span>
            <span className="auth-error-text">{error}</span>
          </div>
        )}

        {/* ─────────────── FORM: LOGIN ────────────────────────────── */}
        {mode === 'login' ? (
          <form className="auth-form" onSubmit={handleLoginSubmit}>
            <div className="auth-field-group">
              <label className="auth-label" htmlFor="login-identifier">
                Username or Email
              </label>
              <div className="auth-input-wrapper">
                <UserIcon size={18} className="auth-field-icon" />
                <input
                  id="login-identifier"
                  type="text"
                  className="auth-input"
                  placeholder="e.g. demouser or user@example.com"
                  value={loginIdentifier}
                  onChange={(e) => setLoginIdentifier(e.target.value)}
                  autoComplete="username"
                  required
                />
              </div>
            </div>

            <div className="auth-field-group">
              <div className="auth-label-row">
                <label className="auth-label" htmlFor="login-password">
                  Password
                </label>
              </div>
              <div className="auth-input-wrapper">
                <LockIcon size={18} className="auth-field-icon" />
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  className="auth-input"
                  placeholder="Enter your password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="auth-pw-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex="-1"
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            <button
              id="login-submit-btn"
              type="submit"
              className="btn-auth-primary"
              disabled={loading}
            >
              <span>{loading ? 'Signing In...' : 'Sign In'}</span>
              <ArrowRightIcon size={18} />
            </button>

            {/* Quick Demo Fill Helper */}
            <div className="auth-demo-box">
              <span className="auth-demo-label">Testing Demo Account:</span>
              <button
                type="button"
                className="auth-demo-btn"
                onClick={handleFillDemo}
              >
                Auto-fill demo user (Aria Vance)
              </button>
            </div>
          </form>
        ) : (
          /* ─────────────── FORM: REGISTER ─────────────────────────── */
          <form className="auth-form" onSubmit={handleRegisterSubmit}>
            <div className="auth-form-row">
              <div className="auth-field-group">
                <label className="auth-label" htmlFor="reg-first-name">
                  First Name
                </label>
                <div className="auth-input-wrapper">
                  <input
                    id="reg-first-name"
                    type="text"
                    className="auth-input no-icon"
                    placeholder="e.g. Aria"
                    value={regFirstName}
                    onChange={(e) => setRegFirstName(e.target.value)}
                  />
                </div>
              </div>

              <div className="auth-field-group">
                <label className="auth-label" htmlFor="reg-last-name">
                  Last Name
                </label>
                <div className="auth-input-wrapper">
                  <input
                    id="reg-last-name"
                    type="text"
                    className="auth-input no-icon"
                    placeholder="e.g. Vance"
                    value={regLastName}
                    onChange={(e) => setRegLastName(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="auth-field-group">
              <label className="auth-label" htmlFor="reg-username">
                Username <span className="req-star">*</span>
              </label>
              <div className="auth-input-wrapper">
                <UserIcon size={18} className="auth-field-icon" />
                <input
                  id="reg-username"
                  type="text"
                  className="auth-input"
                  placeholder="Choose a unique username"
                  value={regUsername}
                  onChange={(e) => setRegUsername(e.target.value)}
                  autoComplete="username"
                  required
                />
              </div>
            </div>

            <div className="auth-field-group">
              <label className="auth-label" htmlFor="reg-email">
                Email Address <span className="req-star">*</span>
              </label>
              <div className="auth-input-wrapper">
                <MailIcon size={18} className="auth-field-icon" />
                <input
                  id="reg-email"
                  type="email"
                  className="auth-input"
                  placeholder="name@example.com"
                  value={regEmail}
                  onChange={(e) => setRegEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="auth-field-group">
              <label className="auth-label" htmlFor="reg-password">
                Password <span className="req-star">* (min 6 characters)</span>
              </label>
              <div className="auth-input-wrapper">
                <LockIcon size={18} className="auth-field-icon" />
                <input
                  id="reg-password"
                  type={showPassword ? 'text' : 'password'}
                  className="auth-input"
                  placeholder="Create a strong password"
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  autoComplete="new-password"
                  required
                />
                <button
                  type="button"
                  className="auth-pw-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex="-1"
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            <button
              id="register-submit-btn"
              type="submit"
              className="btn-auth-primary"
              disabled={loading}
            >
              <span>{loading ? 'Creating Account...' : 'Create Account'}</span>
              <ArrowRightIcon size={18} />
            </button>

            <p className="auth-privacy-text">
              By joining, your profile and skin diagnostics are securely saved to harmonize with active conflict detection and progressive routine scheduling.
            </p>
          </form>
        )}
      </div>
    </section>
  );
}
