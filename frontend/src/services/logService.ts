/**
 * Log Service for LOT 10
 * Handles admin log operations.
 */
import api from './api';

export interface LogEntry {
    id: string;
    created_at: string | null;
    level: string;
    message: string;
    endpoint: string | null;
    method: string | null;
    request_id: string | null;
    user_id: string | null;
    tenant_id: string | null;
    ip_address: string | null;
    response_status: number | null;
    duration_ms: number | null;
    action: string | null;
}

export interface LogListResponse {
    logs: LogEntry[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
}

export interface LogFilters {
    level?: string;
    tenant_id?: string;
    user_id?: string;
    endpoint?: string;
    action?: string;
    start_date?: string;
    end_date?: string;
    min_status?: number;
    max_status?: number;
    page?: number;
    page_size?: number;
}

export interface PurgeResponse {
    deleted_count: number;
    retention_days: number;
    message: string;
}

export interface LogStatistics {
    period_days: number;
    total_logs: number;
    by_level: Record<string, number>;
    error_count: number;
    error_rate_percent: number;
}

const logService = {
    /**
     * Get paginated and filtered logs.
     */
    async getLogs(filters: LogFilters = {}): Promise<LogListResponse> {
        const params = new URLSearchParams();

        if (filters.level) params.append('level', filters.level);
        if (filters.tenant_id) params.append('tenant_id', filters.tenant_id);
        if (filters.user_id) params.append('user_id', filters.user_id);
        if (filters.endpoint) params.append('endpoint', filters.endpoint);
        if (filters.action) params.append('action', filters.action);
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        if (filters.min_status) params.append('min_status', filters.min_status.toString());
        if (filters.max_status) params.append('max_status', filters.max_status.toString());
        if (filters.page) params.append('page', filters.page.toString());
        if (filters.page_size) params.append('page_size', filters.page_size.toString());

        const response = await api.get<LogListResponse>(`/admin/logs?${params.toString()}`);
        return response.data;
    },

    /**
     * Get a specific log entry by ID.
     */
    async getLogById(logId: string): Promise<LogEntry> {
        const response = await api.get<LogEntry>(`/admin/logs/${logId}`);
        return response.data;
    },

    /**
     * Purge old logs.
     */
    async purgeLogs(days?: number): Promise<PurgeResponse> {
        const params = days ? `?days=${days}` : '';
        const response = await api.post<PurgeResponse>(`/admin/logs/purge${params}`);
        return response.data;
    },

    /**
     * Get log statistics.
     */
    async getStatistics(tenantId?: string, days: number = 7): Promise<LogStatistics> {
        const params = new URLSearchParams();
        if (tenantId) params.append('tenant_id', tenantId);
        params.append('days', days.toString());

        const response = await api.get<LogStatistics>(`/admin/logs/statistics/summary?${params.toString()}`);
        return response.data;
    },

    /**
     * Get log level badge color.
     */
    getLevelColor(level: string): string {
        switch (level.toLowerCase()) {
            case 'debug':
                return 'bg-gray-100 text-gray-800';
            case 'info':
                return 'bg-blue-100 text-blue-800';
            case 'warning':
                return 'bg-yellow-100 text-yellow-800';
            case 'error':
                return 'bg-red-100 text-red-800';
            case 'critical':
                return 'bg-purple-100 text-purple-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    },

    /**
     * Get HTTP status badge color.
     */
    getStatusColor(status: number | null): string {
        if (!status) return 'bg-gray-100 text-gray-800';
        if (status >= 200 && status < 300) return 'bg-green-100 text-green-800';
        if (status >= 300 && status < 400) return 'bg-blue-100 text-blue-800';
        if (status >= 400 && status < 500) return 'bg-yellow-100 text-yellow-800';
        if (status >= 500) return 'bg-red-100 text-red-800';
        return 'bg-gray-100 text-gray-800';
    },
};

export default logService;
