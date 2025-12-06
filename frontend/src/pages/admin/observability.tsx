/**
 * Admin Observability Dashboard (LOT 11)
 * Displays system metrics, health status, and backup controls
 */
import React, { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { Navbar } from '@/components/Navbar';
import {
    SystemMetrics,
    ExtendedHealthCheck,
    BackupResponse,
    getSystemMetrics,
    getExtendedHealthCheck,
    triggerBackup,
} from '@/services/observabilityService';

// Gauge component for displaying percentage values
interface GaugeProps {
    value: number;
    label: string;
    color?: string;
    size?: number;
}

const Gauge: React.FC<GaugeProps> = ({ value, label, color = '#3b82f6', size = 120 }) => {
    const strokeWidth = 10;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (value / 100) * circumference;

    return (
        <div className="gauge-container">
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
                {/* Background circle */}
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth={strokeWidth}
                />
                {/* Progress circle */}
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="none"
                    stroke={color}
                    strokeWidth={strokeWidth}
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    transform={`rotate(-90 ${size / 2} ${size / 2})`}
                    style={{ transition: 'stroke-dashoffset 0.5s ease' }}
                />
                {/* Center text */}
                <text
                    x="50%"
                    y="45%"
                    textAnchor="middle"
                    className="gauge-value"
                    style={{ fontSize: '1.5rem', fontWeight: 'bold', fill: '#1f2937' }}
                >
                    {value.toFixed(1)}%
                </text>
                <text
                    x="50%"
                    y="60%"
                    textAnchor="middle"
                    className="gauge-label"
                    style={{ fontSize: '0.75rem', fill: '#6b7280' }}
                >
                    {label}
                </text>
            </svg>
        </div>
    );
};

// Status badge component
interface StatusBadgeProps {
    status: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
    const getStatusColor = (s: string) => {
        switch (s.toLowerCase()) {
            case 'ok':
            case 'healthy':
                return 'bg-green-100 text-green-800';
            case 'unhealthy':
            case 'error':
                return 'bg-red-100 text-red-800';
            case 'not_configured':
                return 'bg-gray-100 text-gray-800';
            default:
                return 'bg-yellow-100 text-yellow-800';
        }
    };

    return (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
            {status}
        </span>
    );
};

const ObservabilityPage: React.FC = () => {
    const router = useRouter();
    const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
    const [health, setHealth] = useState<ExtendedHealthCheck | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [backupStatus, setBackupStatus] = useState<BackupResponse | null>(null);
    const [backupLoading, setBackupLoading] = useState(false);
    const [autoRefresh, setAutoRefresh] = useState(true);

    const fetchData = useCallback(async () => {
        try {
            const [metricsData, healthData] = await Promise.all([
                getSystemMetrics(),
                getExtendedHealthCheck(),
            ]);
            setMetrics(metricsData);
            setHealth(healthData);
            setError(null);
        } catch (err: any) {
            console.error('Failed to fetch observability data:', err);
            if (err.response?.status === 401) {
                router.push('/login');
                return;
            }
            setError(err.message || 'Failed to load metrics');
        } finally {
            setLoading(false);
        }
    }, [router]);

    useEffect(() => {
        fetchData();

        // Auto-refresh every 10 seconds if enabled
        let interval: NodeJS.Timeout | null = null;
        if (autoRefresh) {
            interval = setInterval(fetchData, 10000);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [fetchData, autoRefresh]);

    const handleBackup = async () => {
        setBackupLoading(true);
        try {
            const result = await triggerBackup({
                include_logs: false,
                description: 'Manual backup from admin dashboard',
            });
            setBackupStatus(result);
        } catch (err: any) {
            setBackupStatus({
                success: false,
                timestamp: new Date().toISOString(),
                message: 'Backup failed',
                error: err.message,
            });
        } finally {
            setBackupLoading(false);
        }
    };

    const formatUptime = (seconds: number): string => {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);

        if (days > 0) return `${days}d ${hours}h ${minutes}m`;
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    };

    const formatBytes = (bytes?: number): string => {
        if (!bytes) return 'N/A';
        const gb = bytes / (1024 * 1024 * 1024);
        if (gb >= 1) return `${gb.toFixed(2)} GB`;
        const mb = bytes / (1024 * 1024);
        return `${mb.toFixed(2)} MB`;
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50">
                <Navbar />
                <div className="flex items-center justify-center h-96">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
            </div>
        );
    }

    return (
        <>
            <Head>
                <title>Observability | M365 License Optimizer</title>
            </Head>
            <div className="min-h-screen bg-gray-50">
                <Navbar />

                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    {/* Header */}
                    <div className="mb-8 flex justify-between items-center">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">Observability Dashboard</h1>
                            <p className="mt-2 text-sm text-gray-600">
                                System metrics and health monitoring
                            </p>
                        </div>
                        <div className="flex items-center space-x-4">
                            <label className="flex items-center space-x-2 text-sm">
                                <input
                                    type="checkbox"
                                    checked={autoRefresh}
                                    onChange={(e) => setAutoRefresh(e.target.checked)}
                                    className="rounded border-gray-300"
                                />
                                <span>Auto-refresh (10s)</span>
                            </label>
                            <button
                                onClick={fetchData}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                Refresh
                            </button>
                        </div>
                    </div>

                    {error && (
                        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
                            <p className="text-red-800">{error}</p>
                        </div>
                    )}

                    {/* Health Status Card */}
                    {health && (
                        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                            <h2 className="text-xl font-semibold mb-4">System Health</h2>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                    <span className="text-gray-600">Overall</span>
                                    <StatusBadge status={health.status} />
                                </div>
                                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                    <span className="text-gray-600">Database</span>
                                    <StatusBadge status={health.database} />
                                </div>
                                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                    <span className="text-gray-600">Redis</span>
                                    <StatusBadge status={health.redis} />
                                </div>
                                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                    <span className="text-gray-600">Azure Storage</span>
                                    <StatusBadge status={health.azure_storage} />
                                </div>
                            </div>
                            <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                                <div>
                                    <span className="text-gray-500">Version:</span>{' '}
                                    <span className="font-medium">{health.version}</span>
                                </div>
                                <div>
                                    <span className="text-gray-500">Environment:</span>{' '}
                                    <span className="font-medium capitalize">{health.environment}</span>
                                </div>
                                <div>
                                    <span className="text-gray-500">Uptime:</span>{' '}
                                    <span className="font-medium">{formatUptime(health.uptime_seconds)}</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Metrics Grid */}
                    {metrics && (
                        <>
                            {/* Resource Gauges */}
                            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                                <h2 className="text-xl font-semibold mb-4">Resource Usage</h2>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 justify-items-center">
                                    <Gauge
                                        value={metrics.cpu.percent || 0}
                                        label="CPU"
                                        color={metrics.cpu.percent > 80 ? '#ef4444' : metrics.cpu.percent > 60 ? '#f59e0b' : '#22c55e'}
                                    />
                                    <Gauge
                                        value={metrics.memory.percent || 0}
                                        label="Memory"
                                        color={metrics.memory.percent && metrics.memory.percent > 80 ? '#ef4444' : metrics.memory.percent && metrics.memory.percent > 60 ? '#f59e0b' : '#22c55e'}
                                    />
                                    <Gauge
                                        value={metrics.disk.percent || 0}
                                        label="Disk"
                                        color={metrics.disk.percent && metrics.disk.percent > 80 ? '#ef4444' : metrics.disk.percent && metrics.disk.percent > 60 ? '#f59e0b' : '#22c55e'}
                                    />
                                </div>
                            </div>

                            {/* Detailed Metrics */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                                {/* Memory Details */}
                                <div className="bg-white rounded-lg shadow-md p-6">
                                    <h3 className="text-lg font-semibold mb-4">Memory Details</h3>
                                    <dl className="space-y-2">
                                        <div className="flex justify-between">
                                            <dt className="text-gray-500">Total</dt>
                                            <dd className="font-medium">{formatBytes(metrics.memory.total_bytes)}</dd>
                                        </div>
                                        <div className="flex justify-between">
                                            <dt className="text-gray-500">Used</dt>
                                            <dd className="font-medium">{formatBytes(metrics.memory.used_bytes)}</dd>
                                        </div>
                                        <div className="flex justify-between">
                                            <dt className="text-gray-500">Available</dt>
                                            <dd className="font-medium">{formatBytes(metrics.memory.available_bytes)}</dd>
                                        </div>
                                    </dl>
                                </div>

                                {/* Disk Details */}
                                <div className="bg-white rounded-lg shadow-md p-6">
                                    <h3 className="text-lg font-semibold mb-4">Disk Details</h3>
                                    <dl className="space-y-2">
                                        <div className="flex justify-between">
                                            <dt className="text-gray-500">Path</dt>
                                            <dd className="font-medium font-mono">{metrics.disk.path}</dd>
                                        </div>
                                        <div className="flex justify-between">
                                            <dt className="text-gray-500">Total</dt>
                                            <dd className="font-medium">{formatBytes(metrics.disk.total_bytes)}</dd>
                                        </div>
                                        <div className="flex justify-between">
                                            <dt className="text-gray-500">Free</dt>
                                            <dd className="font-medium">{formatBytes(metrics.disk.free_bytes)}</dd>
                                        </div>
                                    </dl>
                                </div>

                                {/* Network */}
                                <div className="bg-white rounded-lg shadow-md p-6">
                                    <h3 className="text-lg font-semibold mb-4">Network I/O</h3>
                                    <dl className="space-y-2">
                                        <div className="flex justify-between">
                                            <dt className="text-gray-500">Bytes Sent</dt>
                                            <dd className="font-medium">{metrics.network.bytes_sent_mb?.toFixed(2)} MB</dd>
                                        </div>
                                        <div className="flex justify-between">
                                            <dt className="text-gray-500">Bytes Received</dt>
                                            <dd className="font-medium">{metrics.network.bytes_recv_mb?.toFixed(2)} MB</dd>
                                        </div>
                                        <div className="flex justify-between">
                                            <dt className="text-gray-500">Packets Sent</dt>
                                            <dd className="font-medium">{metrics.network.packets_sent?.toLocaleString()}</dd>
                                        </div>
                                        <div className="flex justify-between">
                                            <dt className="text-gray-500">Packets Received</dt>
                                            <dd className="font-medium">{metrics.network.packets_recv?.toLocaleString()}</dd>
                                        </div>
                                    </dl>
                                </div>

                                {/* Process */}
                                <div className="bg-white rounded-lg shadow-md p-6">
                                    <h3 className="text-lg font-semibold mb-4">Process Info</h3>
                                    <dl className="space-y-2">
                                        <div className="flex justify-between">
                                            <dt className="text-gray-500">PID</dt>
                                            <dd className="font-medium font-mono">{metrics.process.pid}</dd>
                                        </div>
                                        <div className="flex justify-between">
                                            <dt className="text-gray-500">Memory (RSS)</dt>
                                            <dd className="font-medium">{metrics.process.memory_rss_mb?.toFixed(2)} MB</dd>
                                        </div>
                                        <div className="flex justify-between">
                                            <dt className="text-gray-500">Threads</dt>
                                            <dd className="font-medium">{metrics.process.num_threads}</dd>
                                        </div>
                                        <div className="flex justify-between">
                                            <dt className="text-gray-500">CPU</dt>
                                            <dd className="font-medium">{metrics.process.cpu_percent?.toFixed(1)}%</dd>
                                        </div>
                                    </dl>
                                </div>
                            </div>

                            {/* System Info */}
                            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                                <h3 className="text-lg font-semibold mb-4">System Information</h3>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                    <div>
                                        <span className="text-gray-500">Platform:</span>{' '}
                                        <span className="font-medium">{metrics.system.platform}</span>
                                    </div>
                                    <div>
                                        <span className="text-gray-500">Release:</span>{' '}
                                        <span className="font-medium">{metrics.system.platform_release}</span>
                                    </div>
                                    <div>
                                        <span className="text-gray-500">Architecture:</span>{' '}
                                        <span className="font-medium">{metrics.system.architecture}</span>
                                    </div>
                                    <div>
                                        <span className="text-gray-500">Python:</span>{' '}
                                        <span className="font-medium">{metrics.system.python_version}</span>
                                    </div>
                                </div>
                            </div>
                        </>
                    )}

                    {/* Backup Section */}
                    <div className="bg-white rounded-lg shadow-md p-6">
                        <h2 className="text-xl font-semibold mb-4">Database Backup</h2>
                        <div className="flex items-center space-x-4">
                            <button
                                onClick={handleBackup}
                                disabled={backupLoading}
                                className={`px-6 py-2 rounded-lg font-medium transition-colors ${backupLoading
                                    ? 'bg-gray-400 cursor-not-allowed'
                                    : 'bg-green-600 hover:bg-green-700 text-white'
                                    }`}
                            >
                                {backupLoading ? 'Creating Backup...' : 'Trigger Backup'}
                            </button>
                            {backupStatus && (
                                <div className={`p-3 rounded-lg ${backupStatus.success ? 'bg-green-50' : 'bg-red-50'}`}>
                                    <p className={backupStatus.success ? 'text-green-800' : 'text-red-800'}>
                                        {backupStatus.message}
                                    </p>
                                    {backupStatus.filename && (
                                        <p className="text-sm text-gray-600 mt-1">
                                            File: {backupStatus.filename}
                                        </p>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Last Updated */}
                    {metrics && (
                        <div className="mt-4 text-center text-sm text-gray-500">
                            Last updated: {new Date(metrics.timestamp).toLocaleString()}
                        </div>
                    )}
                </main>
            </div>
        </>
    );
};

export default ObservabilityPage;
