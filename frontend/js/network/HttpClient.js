/**
 * 📡 HttpClient - Centralized & Resilient Network Layer
 * ===================================================
 * Features:
 * - ESM (ES Modules) support
 * - Automatic X-Correlation-ID injection
 * - Exponential Backoff Retries (429, 50x)
 * - Timeout support via AbortController
 * - Supabase Auth Interceptor (JWT injection)
 * - Standardized Error Handling
 */

export class HttpClient {
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || window.API_BASE || '';
        this.timeout = options.timeout || 30000; // 30s default
        this.maxRetries = options.maxRetries || 3;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            ...options.headers
        };
    }

    /**
     * Core request method with retry logic and interceptors
     */
    async request(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
        const correlationId = crypto.randomUUID ? crypto.randomUUID() : this._generateUUID();
        
        let lastError = null;
        let attempt = 0;

        while (attempt <= this.maxRetries) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);

            try {
                // 1. Auth Interceptor: Inject Supabase Token if available
                const authHeaders = await this._getAuthHeaders();
                
                const fetchOptions = {
                    ...options,
                    headers: {
                        ...this.defaultHeaders,
                        'X-Correlation-ID': correlationId,
                        ...authHeaders,
                        ...options.headers
                    },
                    signal: controller.signal
                };

                const response = await fetch(url, fetchOptions);
                clearTimeout(timeoutId);

                // 2. Handle Success
                if (response.ok) {
                    // Return parsed JSON or raw response if needed
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        return await response.json();
                    }
                    return response;
                }

                // 3. Handle Retriable Errors (429, 500, 502, 503, 504)
                const isRetriable = [429, 500, 502, 503, 504].includes(response.status);
                if (isRetriable && attempt < this.maxRetries) {
                    const backoff = Math.pow(2, attempt) * 1000;
                    console.warn(`[HttpClient] Request failed (${response.status}). Retrying in ${backoff}ms... (Attempt ${attempt + 1}/${this.maxRetries})`);
                    await new Promise(r => setTimeout(r, backoff));
                    attempt++;
                    continue;
                }

                // 4. Standardized Error Throw
                let errorData;
                try {
                    errorData = await response.json();
                } catch (e) {
                    errorData = { detail: response.statusText };
                }

                throw {
                    status: response.status,
                    message: errorData.detail || errorData.message || 'Unknown API Error',
                    correlationId: correlationId,
                    data: errorData
                };

            } catch (err) {
                clearTimeout(timeoutId);
                
                if (err.name === 'AbortError') {
                    throw { status: 408, message: 'Request Timeout', correlationId };
                }

                // If it's already our standardized error, rethrow it
                if (err.status) throw err;

                // Network errors or other exceptions
                if (attempt < this.maxRetries) {
                    attempt++;
                    const backoff = Math.pow(2, attempt) * 1000;
                    await new Promise(r => setTimeout(r, backoff));
                    continue;
                }

                throw { status: 0, message: err.message || 'Network Error', correlationId };
            }
        }
    }

    async get(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'GET' });
    }

    async post(endpoint, body, options = {}) {
        return this.request(endpoint, { 
            ...options, 
            method: 'POST', 
            body: JSON.stringify(body) 
        });
    }

    async put(endpoint, body, options = {}) {
        return this.request(endpoint, { 
            ...options, 
            method: 'PUT', 
            body: JSON.stringify(body) 
        });
    }

    async delete(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'DELETE' });
    }

    /**
     * Interceptor to get active Supabase session
     */
    async _getAuthHeaders() {
        if (window.SupabaseAuth && typeof window.SupabaseAuth.getValidSession === 'function') {
            try {
                const session = await window.SupabaseAuth.getValidSession();
                if (session && session.access_token) {
                    return { 'Authorization': `Bearer ${session.access_token}` };
                }
            } catch (e) {
                console.warn('[HttpClient] Auth Interceptor Error:', e);
            }
        }
        return {};
    }

    /**
     * Fallback UUID generator if crypto.randomUUID is not available
     */
    _generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
}

// Export singleton instance for global use
export const http = new HttpClient();
window.http = http;
