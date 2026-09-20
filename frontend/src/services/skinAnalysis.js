/**
 * Joyory Skin Analysis API Service
 * Sends a captured image to the Django backend (which proxies to Ivy AI).
 * The Ivy AI API key NEVER appears here — it stays on the Django server.
 */

import { getSessionId } from './api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * Sends a captured image Blob to the Django skin analysis endpoint.
 * Returns { success, analysis, recommendations } or throws on network error.
 *
 * @param {Blob} imageBlob  - JPEG/PNG blob captured from canvas
 * @returns {Promise<{success: boolean, analysis: object, recommendations: Array}>}
 */
export async function analyzeSkin(imageBlob) {
  const formData = new FormData();
  formData.append('image', imageBlob, 'skin_capture.jpg');

  const response = await fetch(`${API_BASE_URL}/skin-analysis/`, {
    method: 'POST',
    headers: {
      'X-Session-ID': getSessionId(),
      // NOTE: Do NOT set Content-Type here — browser sets it automatically
      // with the correct multipart boundary for FormData
    },
    body: formData,
  });

  const data = await response.json().catch(() => ({
    success: false,
    error: 'Unexpected server response.',
  }));

  if (!response.ok || !data.success) {
    const message =
      data?.error ||
      `Server error (${response.status}). Please try again.`;
    throw new Error(message);
  }

  return data;
}
