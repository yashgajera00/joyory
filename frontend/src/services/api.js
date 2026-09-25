/**
 * Joyory Centralized API Service
 * Manages persistent guest session ID in localStorage and communicates with Django REST Framework backend.
 */

// Cleanly resolve API base URL:
// - Default (local dev): '/api' (proxied by Vite to http://127.0.0.1:8000/api)
// - Production (Vercel): VITE_API_BASE_URL (e.g. 'https://joyory.pythonanywhere.com/api' or 'https://joyory.pythonanywhere.com')
const rawBase = (import.meta.env.VITE_API_BASE_URL || '/api').trim().replace(/\/+$/, '');
export const API_BASE_URL = (rawBase && !rawBase.endsWith('/api') && rawBase !== '/api')
  ? `${rawBase}/api`
  : rawBase;


/**
 * Retrieves or initializes a unique session UUID for guest cart & routine persistence.
 */
export function getSessionId() {
  let sessionId = localStorage.getItem('joyory_session_id');
  if (!sessionId) {
    sessionId = 'sess_' + Math.random().toString(36).substring(2, 15) + '_' + Date.now().toString(36);
    localStorage.setItem('joyory_session_id', sessionId);
  }
  return sessionId;
}

/**
 * Resets and creates a fresh session UUID, ensuring previous guest data does not leak.
 */
export function resetSessionId() {
  localStorage.removeItem('joyory_session_id');
  return getSessionId();
}

/**
 * Core HTTP request helper with unified headers and error formatting.
 */
async function request(endpoint, options = {}) {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE_URL}${cleanEndpoint}`;
  const token = localStorage.getItem('joyory_auth_token');
  const headers = {
    'X-Session-ID': getSessionId(),
    ...(token ? { 'Authorization': `Token ${token}` } : {}),
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(options.headers || {}),
  };

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) errorMessage = errorData.detail;
        else if (errorData.error) errorMessage = errorData.error;
        else errorMessage = typeof errorData === 'string' ? errorData : JSON.stringify(errorData);
      } catch {
        // use default error message
      }
      throw new Error(errorMessage);
    }
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }
    return await response.text();
  } catch (err) {
    console.error(`API Error on [${options.method || 'GET'} ${endpoint}]:`, err);
    throw err;
  }
}

// ----------------------------------------------------
// PRODUCT APIS
// ----------------------------------------------------

export async function fetchProducts(params = {}) {
  const query = new URLSearchParams();
  if (params.category && params.category !== 'all') query.append('category', params.category);
  if (params.climate && params.climate !== 'all') query.append('climate', params.climate);
  if (params.active_level && params.active_level !== 'all') query.append('active_level', params.active_level);
  if (params.search) query.append('search', params.search);

  const qs = query.toString() ? `?${query.toString()}` : '';
  return request(`/products/${qs}`);
}

export async function fetchProductDetail(productId) {
  return request(`/products/${productId}/`);
}

// ----------------------------------------------------
// CART & CONFLICT APIS
// ----------------------------------------------------

export async function fetchCart() {
  const sessionId = getSessionId();
  return request(`/cart/?session_key=${encodeURIComponent(sessionId)}`);
}

export async function addToCart(productId, quantity = 1) {
  const sessionId = getSessionId();
  return request('/cart/add/', {
    method: 'POST',
    body: JSON.stringify({
      product_id: productId,
      quantity,
      session_key: sessionId,
    }),
  });
}

export async function updateCartItemQuantity(productId, quantity) {
  const sessionId = getSessionId();
  return request('/cart/update/', {
    method: 'POST',
    body: JSON.stringify({
      product_id: productId,
      quantity,
      session_key: sessionId,
    }),
  });
}

export async function removeFromCart(productId) {
  const sessionId = getSessionId();
  return request('/cart/remove/', {
    method: 'DELETE',
    body: JSON.stringify({
      product_id: productId,
      session_key: sessionId,
    }),
  });
}

export async function clearCart() {
  const sessionId = getSessionId();
  return request('/cart/clear/', {
    method: 'POST',
    body: JSON.stringify({
      session_key: sessionId,
    }),
  });
}

export async function checkIngredientConflicts(productId, cartProductIds = []) {
  return request('/cart/check-conflicts/', {
    method: 'POST',
    body: JSON.stringify({
      product_id: productId,
      cart_product_ids: cartProductIds,
    }),
  });
}

// ----------------------------------------------------
// CLIMATE APIS
// ----------------------------------------------------

export async function fetchCartClimateAnalysis(coords = {}, city = null) {
  const sessionId = getSessionId();
  return request('/cart/climate-analysis/', {
    method: 'POST',
    body: JSON.stringify({
      latitude: coords.latitude || null,
      longitude: coords.longitude || null,
      city: city || null,
      session_key: sessionId,
    }),
  });
}

export async function fetchClimateAnalysis(coords = {}, productIds = [], city = null) {
  return request('/climate/analyze/', {
    method: 'POST',
    body: JSON.stringify({
      latitude: coords.latitude || null,
      longitude: coords.longitude || null,
      city: city || null,
      product_ids: productIds,
    }),
  });
}

// ----------------------------------------------------
// ROUTINE & MICRO-TRACKING APIS
// ----------------------------------------------------

export async function generateRoutine(productIds, name = 'My Joyory Routine') {
  const sessionId = getSessionId();
  return request('/routines/generate/', {
    method: 'POST',
    body: JSON.stringify({
      product_ids: productIds,
      name,
      session_id: sessionId,
    }),
  });
}

export async function fetchRoutines() {
  const sessionId = getSessionId();
  return request(`/routines/?session_id=${encodeURIComponent(sessionId)}`);
}

export async function fetchRoutineDetail(routineId) {
  return request(`/routines/${routineId}/`);
}

export async function deleteRoutineStep(routineId, stepId) {
  return request(`/routines/${routineId}/steps/${stepId}/delete/`, {
    method: 'DELETE',
  });
}

export async function completeRoutineStep(routineId, stepId, completed = true, notes = '', session = 'all') {
  return request(`/routines/${routineId}/complete-step/`, {
    method: 'POST',
    body: JSON.stringify({
      step_id: stepId,
      completed,
      notes,
      session,
    }),
  });
}


export async function fetchRoutineProgress(routineId, params = {}) {
  const query = new URLSearchParams();
  if (params.time_of_day) query.append('time_of_day', params.time_of_day);
  if (params.city) query.append('city', params.city);
  if (params.latitude) query.append('latitude', params.latitude);
  if (params.longitude) query.append('longitude', params.longitude);
  if (params.week) query.append('week', params.week);
  if (params.date) query.append('date', params.date);
  if (params.client_hour !== undefined) query.append('client_hour', params.client_hour);
  const qs = query.toString() ? `?${query.toString()}` : '';
  return request(`/routines/${routineId}/progress/${qs}`);
}


export async function fetchRoutineDeliverySchedule(routineId) {
  return request(`/routines/${routineId}/delivery-schedule/`);
}

export async function toggleRoutineAutoReorder(routineId, enabled = null) {
  return request(`/routines/${routineId}/toggle-auto-reorder/`, {
    method: 'POST',
    body: JSON.stringify(enabled !== null ? { enabled } : {}),
  });
}

export async function toggleDeliveryItemAutoReorder(itemId, active = null) {
  return request(`/routines/delivery-items/${itemId}/toggle/`, {
    method: 'POST',
    body: JSON.stringify(active !== null ? { active } : {}),
  });
}

export async function completeAllRoutineSteps(routineId) {
  return request(`/routines/${routineId}/complete-all/`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

export async function submitDailySkinFeedback(routineId, skinFeel, notes = '') {
  return request(`/routines/${routineId}/feedback/`, {
    method: 'POST',
    body: JSON.stringify({
      skin_feel: skinFeel,
      notes,
    }),
  });
}

export async function fetchDailySkinFeedback(routineId) {
  return request(`/routines/${routineId}/feedback/`);
}

