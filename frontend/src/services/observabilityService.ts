/**
 * Observability API Service (LOT 11)
 * Service for fetching system metrics and health data from backend
 */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface SystemInfo {
    platform: string;
    platform_release: string;
    platform_version: string;
    architecture: string;
    hostname: string;
    python_version: string;
    psutil_available: boolean;
}

export interface CpuMetrics {
    percent: number;
    count_physical?: number;
    count_logical?: number;
    frequency_mhz?: number;
    frequency_max_mhz?: number;
    error?: string;
}

export interface MemoryMetrics {
    total_bytes?: number;
    available_bytes?: number;
    used_bytes?: number;
    percent?: number;
    total_gb?: number;
    available_gb?: number;
    used_gb?: number;
    error?: string;
}

export interface DiskMetrics {
    path: string;
    total_bytes?: number;
    used_bytes?: number;
    free_bytes?: number;
    percent?: number;
    total_gb?: number;
    used_gb?: number;
    free_gb?: number;
    error?: string;
}

export interface NetworkMetrics {
    bytes_sent?: number;
    bytes_recv?: number;
    packets_sent?: number;
    packets_recv?: number;
    bytes_sent_mb?: number;
    bytes_recv_mb?: number;
    error?: string;
}

export interface ProcessMetrics {
    pid?: number;
    memory_rss_bytes?: number;
    memory_rss_mb?: number;
    memory_vms_bytes?: number;
    memory_vms_mb?: number;
    cpu_percent?: number;
    num_threads?: number;
    create_time?: string;
    error?: string;
}

export interface SystemMetrics {
    timestamp: string;
    uptime_seconds: number;
    system: SystemInfo;
    cpu: CpuMetrics;
    memory: MemoryMetrics;
    disk: DiskMetrics;
    network: NetworkMetrics;
    process: ProcessMetrics;
}

export interface ExtendedHealthCheck {
    status: string;
    database: string;
    redis: string;
    azure_storage: string;
    version: string;
    environment: string;
    uptime_seconds: number;
    timestamp: string;
    checks: Record<string, boolean>;
}

export interface BackupRequest {
    include_logs?: boolean;
    description?: string;
}

export interface BackupResponse {
    success: boolean;
    backup_id?: string;
    filename?: string;
    size_bytes?: number;
    storage_path?: string;
    timestamp: string;
    message: string;
    error?: string;
}

/**
 * Get authentication headers from localStorage
 */
function getAuthHeaders(): Record<string, string> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Fetch system metrics from the backend
 */
export async function getSystemMetrics(): Promise<SystemMetrics> {
    const response = await axios.get<SystemMetrics>(
        `${API_BASE_URL}/admin/metrics`,
        { headers: getAuthHeaders() }
    );
    return response.data;
}

/**
 * Fetch extended health check from the backend
 */
export async function getExtendedHealthCheck(): Promise<ExtendedHealthCheck> {
    const response = await axios.get<ExtendedHealthCheck>(
        `${API_BASE_URL}/admin/health/extended`,
        { headers: getAuthHeaders() }
    );
    return response.data;
}

/**
 * Trigger a manual database backup
 */
export async function triggerBackup(request: BackupRequest = {}): Promise<BackupResponse> {
    const response = await axios.post<BackupResponse>(
        `${API_BASE_URL}/admin/backup`,
        request,
        { headers: getAuthHeaders() }
    );
    return response.data;
}

export const observabilityService = {
    getSystemMetrics,
    getExtendedHealthCheck,
    triggerBackup,
};

export default observabilityService;
