import React from 'react';
import { BagIcon, CalendarIcon, CheckCircleIcon, RefreshCwIcon, UserIcon, LogOutIcon } from './Icons';

export default function Header({ currentView, setCurrentView, cartItemCount = 0, user, onLogout }) {
  return (
    <header className="site-header">
      <div className="header-container">
        {/* Brand */}
        <div className="brand-wrapper" onClick={() => setCurrentView('home')} style={{ cursor: 'pointer' }}>
          <div className="brand-logo">JOYORY</div>
          <span className="brand-subtext">SMART SKINCARE</span>
        </div>

        {/* Navigation - Always show all tabs */}
        <nav className="header-nav">
          <button
            className={`nav-link ${currentView === 'home' ? 'active' : ''}`}
            onClick={() => setCurrentView('home')}
          >
            Home
          </button>
          <button
            className={`nav-link ${currentView === 'products' || currentView === 'product-detail' ? 'active' : ''}`}
            onClick={() => setCurrentView('products')}
          >
            Catalog
          </button>
          <button
            className={`nav-link ${currentView === 'routine' ? 'active' : ''}`}
            onClick={() => {
              if (!user) {
                setCurrentView('auth');
              } else {
                setCurrentView('routine');
              }
            }}
          >
            <CalendarIcon size={16} className="inline-icon" />
            Routine Timeline
          </button>
          <button
            className={`nav-link ${currentView === 'tracker' ? 'active' : ''}`}
            onClick={() => {
              if (!user) {
                setCurrentView('auth');
              } else {
                setCurrentView('tracker');
              }
            }}
          >
            <CheckCircleIcon size={16} className="inline-icon" />
            Daily Tracker
          </button>
          <button
            className={`nav-link ${currentView === 'delivery' ? 'active' : ''}`}
            onClick={() => {
              if (!user) {
                setCurrentView('auth');
              } else {
                setCurrentView('delivery');
              }
            }}
          >
            <RefreshCwIcon size={16} className="inline-icon" />
            Replenishment
          </button>
        </nav>

        {/* Action Buttons: Cart & Auth */}
        <div className="header-actions">
          <button
            className={`cart-btn ${currentView === 'cart' ? 'active' : ''}`}
            onClick={() => setCurrentView('cart')}
            aria-label="View Shopping Cart"
          >
            <BagIcon size={20} />
            <span className="cart-text">Cart</span>
            {cartItemCount > 0 && (
              <span className="cart-count-badge animate-pop">{cartItemCount}</span>
            )}
          </button>

          {user ? (
            <div className="header-user-menu">
              <button
                className={`user-profile-btn ${currentView === 'auth' ? 'active' : ''}`}
                onClick={() => setCurrentView('auth')}
                title="View My Account Profile"
              >
                <span className="user-avatar-tiny">
                  {(user.first_name?.[0] || user.username?.[0] || 'U').toUpperCase()}
                </span>
                <span className="user-name-text">
                  {user.first_name || user.username}
                </span>
              </button>
              <button
                className="header-logout-icon-btn"
                onClick={onLogout}
                title="Sign Out"
                aria-label="Sign Out"
              >
                <LogOutIcon size={15} />
              </button>
            </div>
          ) : (
            <button
              className={`nav-auth-btn ${currentView === 'auth' ? 'active' : ''}`}
              onClick={() => setCurrentView('auth')}
            >
              <UserIcon size={16} />
              <span>Sign In</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
