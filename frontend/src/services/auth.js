/**
 * Joyory Authentication Service
 * Manages user authentication token and profile storage in localStorage,
 * and communicates with the Django auth endpoints.
 */

import { API_BASE_URL } from './api';

export function getAuthToken() {
  return localStorage.getItem('joyory_auth_token');
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem('joyory_auth_token', token);
  } else {
    localStorage.removeItem('joyory_auth_token');
  }
}

export function getStoredUser() {
  try {
    const data = localStorage.getItem('joyory_user');
    return data ? JSON.parse(data) : null;
  } catch {
    return null;
  }
}

export function setStoredUser(user) {
  if (user) {
    localStorage.setItem('joyory_user', JSON.stringify(user));
  } else {
    localStorage.removeItem('joyory_user');
  }
}

export async function loginUser(identifier, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username: identifier, password }),
  });

  const data = await response.json().catch(() => ({ success: false, error: 'Network communication error.' }));
  if (!response.ok || !data.success) {
    throw new Error(data.error || 'Login failed. Please check your credentials.');
  }

  setAuthToken(data.token);
  setStoredUser(data.user);
  return data;
}

export async function registerUser(userData) {
  const response = await fetch(`${API_BASE_URL}/auth/register/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });

  const data = await response.json().catch(() => ({ success: false, error: 'Network communication error.' }));
  if (!response.ok || !data.success) {
    throw new Error(data.error || 'Registration failed. Please check your inputs.');
  }

  setAuthToken(data.token);
  setStoredUser(data.user);
  return data;
}

export async function logoutUser() {
  const token = getAuthToken();
  try {
    if (token) {
      await fetch(`${API_BASE_URL}/auth/logout/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });
    }
  } catch (err) {
    console.warn('Logout notice:', err);
  } finally {
    setAuthToken(null);
    setStoredUser(null);
  }
  return { success: true };
}

export async function fetchCurrentUser() {
  const token = getAuthToken();
  if (!token) return null;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/me/`, {
      headers: {
        'Authorization': `Token ${token}`,
      },
    });
    if (response.ok) {
      const data = await response.json();
      if (data.authenticated && data.user) {
        setStoredUser(data.user);
        return data.user;
      }
    }
    setAuthToken(null);
    setStoredUser(null);
    return null;
  } catch {
    return getStoredUser();
  }
}
