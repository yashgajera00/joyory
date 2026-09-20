import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Home from './components/Home';
import ProductGrid from './components/ProductGrid';
import ProductDetail from './components/ProductDetail';
import Cart from './components/Cart';
import RoutineTimeline from './components/RoutineTimeline';
import RoutineTracker from './components/RoutineTracker';
import DeliverySchedule from './components/DeliverySchedule';
import AuthPage from './components/AuthPage';
import { fetchCart, addToCart, updateCartItemQuantity, removeFromCart, generateRoutine, fetchRoutines, checkIngredientConflicts, resetSessionId } from './services/api';
import { fetchCurrentUser, logoutUser, getStoredUser } from './services/auth';
import './App.css';

export default function App() {
  const [currentView, setCurrentView] = useState('home'); // 'home' | 'products' | 'product-detail' | 'cart' | 'routine' | 'tracker' | 'delivery' | 'auth'
  const [selectedProductId, setSelectedProductId] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [user, setUser] = useState(getStoredUser);
  const [cart, setCart] = useState(null);
  const [conflictData, setConflictData] = useState(null);
  const [cartLoading, setCartLoading] = useState(false);
  const [activeRoutine, setActiveRoutine] = useState(null);
  const [routineLoading, setRoutineLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  // Show auto-dismiss toast notification
  const showToast = (message, type = 'info') => {
    setNotification({ message, type, id: Date.now() });
    setTimeout(() => {
      setNotification((curr) => (curr?.message === message ? null : curr));
    }, 4000);
  };

  // Initial cart & existing routine load
  const refreshCart = async () => {
    try {
      setCartLoading(true);
      const cartData = await fetchCart();
      setCart(cartData);

      // Re-check conflicts across current cart products
      const pids = (cartData?.items || []).map((i) => i.product.id);
      if (pids.length > 1) {
        const firstPid = pids[0];
        const otherPids = pids.slice(1);
        const conflicts = await checkIngredientConflicts(firstPid, otherPids);
        setConflictData(conflicts);
      } else {
        setConflictData(null);
      }
    } catch (err) {
      console.warn("Cart refresh notice:", err.message);
      setCart(null);
    } finally {
      setCartLoading(false);
    }
  };

  const loadExistingRoutines = async () => {
    try {
      setRoutineLoading(true);
      const routines = await fetchRoutines();
      if (routines && routines.length > 0) {
        // Pick the latest routine
        const latest = routines[routines.length - 1];
        setActiveRoutine(latest);
      } else {
        // Clear routine state if this user has no routines
        setActiveRoutine(null);
      }
    } catch (err) {
      console.warn("Routines load notice:", err.message);
      setActiveRoutine(null);
    } finally {
      setRoutineLoading(false);
    }
  };

  // Initial load check
  useEffect(() => {
    fetchCurrentUser().then((u) => {
      if (u) setUser(u);
    });
  }, []);

  // Reload cart and routines whenever user authentication state changes
  useEffect(() => {
    refreshCart();
    loadExistingRoutines();
  }, [user]);

  const handleAuthSuccess = (userData, message) => {
    // Clear out in-memory state before setting new user
    setCart(null);
    setActiveRoutine(null);
    setConflictData(null);
    resetSessionId();
    setUser(userData);
    showToast(message || `Welcome, ${userData.first_name || userData.username}!`, 'success');
    setCurrentView('home');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLogout = async () => {
    await logoutUser();
    // Clear out in-memory state and rotate session
    setCart(null);
    setActiveRoutine(null);
    setConflictData(null);
    resetSessionId();
    setUser(null);
    showToast('You have been signed out of your Joyory account.', 'info');
    if (currentView === 'auth') {
      // Stay on auth page so user sees sign-in interface
    } else {
      setCurrentView('home');
    }
  };

  // Handle Add to Cart (Requires Sign In)
  const handleAddToCart = async (productId, quantity = 1) => {
    if (!user) {
      showToast('Please sign in to add products to your bag.', 'warning');
      setCurrentView('auth');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    try {
      const result = await addToCart(productId, quantity);
      setCart(result.cart);

      // Inspect conflict result from backend
      if (result.conflict_analysis && result.conflict_analysis.has_conflicts) {
        setConflictData(result.conflict_analysis);
        showToast(
          `Added to bag with active synergy notice! Check cart review.`,
          'warning'
        );
      } else {
        setConflictData(null);
        showToast(`Item added to your shopping bag.`, 'success');
      }
    } catch (err) {
      showToast(`Could not add item: ${err.message}`, 'error');
    }
  };

  // Handle Update Quantity in Cart
  const handleUpdateQuantity = async (productId, newQuantity) => {
    try {
      if (newQuantity <= 0) {
        await handleRemoveFromCart(productId);
        return;
      }
      const result = await updateCartItemQuantity(productId, newQuantity);
      if (result && result.cart) {
        setCart(result.cart);
        if (result.conflict_analysis) {
          setConflictData(result.conflict_analysis);
        }
      }
      await refreshCart();
    } catch (err) {
      showToast(`Failed to update quantity: ${err.message}`, 'error');
    }
  };

  // Handle Remove from Cart
  const handleRemoveFromCart = async (productId) => {
    try {
      const result = await removeFromCart(productId);
      setCart(result.cart);
      showToast(`Item removed from bag.`, 'info');
      await refreshCart();
    } catch (err) {
      showToast(`Failed to remove item: ${err.message}`, 'error');
    }
  };

  // Handle Generate Progressive Routine from Cart
  const handleGenerateRoutine = async (productIds) => {
    if (!user) {
      showToast('Please sign in to generate and save your routine.', 'warning');
      setCurrentView('auth');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    if (!productIds || productIds.length === 0) {
      showToast(`Please add products to your cart first.`, 'warning');
      return;
    }

    setRoutineLoading(true);
    try {
      const routine = await generateRoutine(productIds, 'My Personalized Joyory Routine');
      setActiveRoutine(routine);
      setCurrentView('routine');
      showToast(`Progressive routine successfully generated!`, 'success');
    } catch (err) {
      showToast(`Failed to generate routine: ${err.message}`, 'error');
    } finally {
      setRoutineLoading(false);
    }
  };

  const handleSelectProduct = (id) => {
    setSelectedProductId(id);
    setCurrentView('product-detail');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const cartItemCount = cart?.total_items || (cart?.items || []).reduce((acc, i) => acc + i.quantity, 0);
  const cartProductIds = (cart?.items || []).map((i) => i.product.id);

  return (
    <div className="app-layout">
      {/* Toast Notification */}
      {notification && (
        <div className={`toast-banner toast-${notification.type}`}>
          <span className="toast-text">{notification.message}</span>
          <button
            className="toast-close"
            onClick={() => setNotification(null)}
          >
            &times;
          </button>
        </div>
      )}

      {/* Global Luxury Header */}
      <Header
        currentView={currentView}
        setCurrentView={(view) => {
          setCurrentView(view);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
        cartItemCount={cartItemCount}
        user={user}
        onLogout={handleLogout}
      />

      {/* Main View Router */}
      <main className="main-viewport">
        {currentView === 'home' && (
          <Home
            user={user}
            onGoToShop={(cat = 'all') => {
              setSelectedCategory(cat);
              setCurrentView('products');
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            onSelectProduct={handleSelectProduct}
            onAddToCart={handleAddToCart}
          />
        )}

        {currentView === 'products' && (
          <ProductGrid
            initialCategory={selectedCategory}
            onSelectCategory={(cat) => setSelectedCategory(cat)}
            onSelectProduct={handleSelectProduct}
            onAddToCart={handleAddToCart}
          />
        )}

        {currentView === 'product-detail' && (
          <ProductDetail
            productId={selectedProductId}
            cartProductIds={cartProductIds}
            onBack={() => setCurrentView('products')}
            onAddToCart={handleAddToCart}
            onGoToCart={() => setCurrentView('cart')}
          />
        )}

        {currentView === 'cart' && (
          <Cart
            cart={cart}
            conflictData={conflictData}
            loading={cartLoading || routineLoading}
            user={user}
            onUpdateQuantity={handleUpdateQuantity}
            onRemoveItem={handleRemoveFromCart}
            onAddProduct={(pid) => handleAddToCart(pid, 1)}
            onGenerateRoutine={handleGenerateRoutine}
            onGoToShop={() => {
              setCurrentView('products');
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            onGoToRoutine={() => {
              setCurrentView('routine');
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            onOrderSuccess={async (orderId, newRoutine) => {
              setCart(null);
              setConflictData(null);
              if (newRoutine) {
                setActiveRoutine(newRoutine.routine || newRoutine);
              } else {
                await loadExistingRoutines();
              }
              await refreshCart();
              showToast(`Order #${orderId} confirmed! Formulas added to your Routine Timeline & Tracker.`, 'success');
            }}
          />
        )}

        {currentView === 'routine' && (
          user ? (
            <RoutineTimeline
              routineData={activeRoutine}
              routineId={activeRoutine?.routine_id || activeRoutine?.id}
              onGoToTracker={() => setCurrentView('tracker')}
              onGoToDelivery={() => setCurrentView('delivery')}
              onRoutineUpdated={(updated) => setActiveRoutine(updated)}
            />
          ) : (
            <AuthPage
              user={user}
              onAuthSuccess={handleAuthSuccess}
              onLogoutSuccess={handleLogout}
              onGoToShop={() => {
                setCurrentView('products');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              onGoToRoutine={() => {
                setCurrentView('routine');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              onGoToCart={() => {
                setCurrentView('cart');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            />
          )
        )}

        {currentView === 'tracker' && (
          user ? (
            <RoutineTracker
              routineId={activeRoutine?.routine_id || activeRoutine?.id}
              user={user}
              onGoToTimeline={() => setCurrentView('routine')}
              onGoToDelivery={() => setCurrentView('delivery')}
            />

          ) : (
            <AuthPage
              user={user}
              onAuthSuccess={handleAuthSuccess}
              onLogoutSuccess={handleLogout}
              onGoToShop={() => {
                setCurrentView('products');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              onGoToRoutine={() => {
                setCurrentView('tracker');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              onGoToCart={() => {
                setCurrentView('cart');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            />
          )
        )}

        {currentView === 'delivery' && (
          user ? (
            <DeliverySchedule
              routineId={activeRoutine?.routine_id || activeRoutine?.id}
              onGoToTimeline={() => setCurrentView('routine')}
              onGoToTracker={() => setCurrentView('tracker')}
            />
          ) : (
            <AuthPage
              user={user}
              onAuthSuccess={handleAuthSuccess}
              onLogoutSuccess={handleLogout}
              onGoToShop={() => {
                setCurrentView('products');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              onGoToRoutine={() => {
                setCurrentView('delivery');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              onGoToCart={() => {
                setCurrentView('cart');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            />
          )
        )}

        {currentView === 'auth' && (
          <AuthPage
            user={user}
            onAuthSuccess={handleAuthSuccess}
            onLogoutSuccess={handleLogout}
            onGoToShop={() => {
              setCurrentView('products');
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            onGoToRoutine={() => {
              setCurrentView('routine');
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            onGoToCart={() => {
              setCurrentView('cart');
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
          />
        )}
      </main>

      {/* Global Luxury Footer */}
      <footer className="site-footer">
        <div className="footer-content">
          <div className="footer-brand-column">
            <span className="footer-logo">JOYORY</span>
            <p className="footer-tagline">
              Smart Shopping Experience &bull; Hackathon Task 02
            </p>
            <p className="footer-copy">
              Decoupled architecture with Django REST Framework & React 19. Formulated for epidermal synergy.
            </p>
          </div>
          <div className="footer-nav-column">
            <h5>Key Features</h5>
            <ul>
              <li onClick={() => setCurrentView('products')}>Smart Catalog</li>
              <li onClick={() => setCurrentView('cart')}>Conflict Engine & Climate Insight</li>
              <li onClick={() => {
                if (!user) setCurrentView('auth');
                else setCurrentView('routine');
              }}>
                Progressive Routine Timeline
              </li>
              <li onClick={() => {
                if (!user) setCurrentView('auth');
                else setCurrentView('tracker');
              }}>
                Daily Habit Micro-Tracker
              </li>
              <li onClick={() => {
                if (!user) setCurrentView('auth');
                else setCurrentView('delivery');
              }}>
                Smart Replenishment Schedule
              </li>
              <li onClick={() => setCurrentView('auth')}>{user ? 'My VIP Account' : 'Sign In / Register'}</li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  );
}
