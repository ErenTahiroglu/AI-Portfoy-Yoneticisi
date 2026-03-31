import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock Worker for api.js tests
class MockWorker {
    addEventListener(type, listener) {
        if (type === 'message') this.messageHandler = listener;
    }
    removeEventListener() {}
    postMessage(data) {
        setTimeout(() => {
            this.messageHandler({
                data: {
                    type: 'EXTRAS_RESULT',
                    extras: { correlation: { matrix: [[1.0]] } }
                }
            });
        }, 0);
    }
}
vi.stubGlobal('Worker', MockWorker);

// Mock HttpClient
vi.mock('../../frontend/js/network/HttpClient.js', () => ({
    http: { get: vi.fn(), post: vi.fn() }
}));

import { checkServerHealth, pollJobResult } from '../../frontend/js/network/api.js';

describe('Refactored API Logic', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should use HttpClient for health check', async () => {
        const { http } = await import('../../frontend/js/network/HttpClient.js');
        http.get.mockResolvedValueOnce({ message: 'OK' });

        const result = await checkServerHealth();
        expect(http.get).toHaveBeenCalledWith('/api/health');
        expect(result.online).toBe(true);
    });

    it('should use HttpClient for job polling', async () => {
        const { http } = await import('../../frontend/js/network/HttpClient.js');
        http.get.mockResolvedValueOnce({ status: 'COMPLETED', result: { data: 123 } });

        const result = await pollJobResult('job-123');
        expect(http.get).toHaveBeenCalledWith('/api/status/job-123');
        expect(result.data).toBe(123);
    });
});
