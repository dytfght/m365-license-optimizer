import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText, Trash2, RefreshCw, ChevronLeft, ChevronRight, Filter, Download } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Navbar } from '../../components/Navbar';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import logService, { LogFilters, LogEntry } from '../../services/logService';

const AdminLogsPage: React.FC = () => {
    const { t } = useTranslation();
    const queryClient = useQueryClient();

    // Filter state
    const [filters, setFilters] = useState<LogFilters>({
        page: 1,
        page_size: 50,
    });
    const [showFilters, setShowFilters] = useState(false);

    // Query for logs
    const {
        data: logsData,
        isLoading,
        error,
        refetch,
    } = useQuery({
        queryKey: ['admin-logs', filters],
        queryFn: () => logService.getLogs(filters),
    });

    // Query for statistics
    const { data: stats } = useQuery({
        queryKey: ['log-statistics'],
        queryFn: () => logService.getStatistics(),
    });

    // Purge mutation
    const purgeMutation = useMutation({
        mutationFn: () => logService.purgeLogs(90),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-logs'] });
            queryClient.invalidateQueries({ queryKey: ['log-statistics'] });
        },
    });

    const handleFilterChange = (key: keyof LogFilters, value: string | number | undefined) => {
        setFilters((prev) => ({
            ...prev,
            [key]: value || undefined,
            page: 1, // Reset to first page on filter change
        }));
    };

    const handlePageChange = (newPage: number) => {
        setFilters((prev) => ({ ...prev, page: newPage }));
    };

    const formatDate = (dateStr: string | null): string => {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleString();
    };

    const truncateMessage = (message: string, maxLength: number = 80): string => {
        if (message.length <= maxLength) return message;
        return message.substring(0, maxLength) + '...';
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">
                            {t('logs.title', 'Audit Logs')}
                        </h1>
                        <p className="text-gray-600 mt-1">
                            {t('logs.subtitle', 'View and manage system audit logs')}
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => refetch()}
                            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                        >
                            <RefreshCw className="w-4 h-4" />
                            {t('common.refresh', 'Refresh')}
                        </button>
                        <button
                            onClick={() => purgeMutation.mutate()}
                            disabled={purgeMutation.isPending}
                            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50"
                        >
                            {purgeMutation.isPending ? <LoadingSpinner /> : <Trash2 className="w-4 h-4" />}
                            {t('logs.purgeOld', 'Purge Old Logs')}
                        </button>
                    </div>
                </div>

                {/* Statistics Cards */}
                {stats && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                        <div className="bg-white rounded-lg shadow p-4">
                            <p className="text-sm text-gray-500">{t('logs.totalLogs', 'Total Logs (7d)')}</p>
                            <p className="text-2xl font-bold text-gray-900">{stats.total_logs.toLocaleString()}</p>
                        </div>
                        <div className="bg-white rounded-lg shadow p-4">
                            <p className="text-sm text-gray-500">{t('logs.errorCount', 'Errors')}</p>
                            <p className="text-2xl font-bold text-red-600">{stats.error_count.toLocaleString()}</p>
                        </div>
                        <div className="bg-white rounded-lg shadow p-4">
                            <p className="text-sm text-gray-500">{t('logs.errorRate', 'Error Rate')}</p>
                            <p className="text-2xl font-bold text-yellow-600">{stats.error_rate_percent}%</p>
                        </div>
                        <div className="bg-white rounded-lg shadow p-4">
                            <p className="text-sm text-gray-500">{t('logs.infoLogs', 'Info Logs')}</p>
                            <p className="text-2xl font-bold text-blue-600">{(stats.by_level.info || 0).toLocaleString()}</p>
                        </div>
                    </div>
                )}

                {/* Filters */}
                <div className="bg-white rounded-lg shadow mb-6">
                    <div className="p-4 border-b flex items-center justify-between">
                        <button
                            onClick={() => setShowFilters(!showFilters)}
                            className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
                        >
                            <Filter className="w-4 h-4" />
                            {t('logs.filters', 'Filters')}
                        </button>
                        {logsData && (
                            <span className="text-sm text-gray-500">
                                {t('logs.showing', 'Showing')} {logsData.logs.length} {t('logs.of', 'of')}{' '}
                                {logsData.total.toLocaleString()} {t('logs.logs', 'logs')}
                            </span>
                        )}
                    </div>

                    {showFilters && (
                        <div className="p-4 grid grid-cols-1 md:grid-cols-4 gap-4 bg-gray-50">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('logs.level', 'Level')}
                                </label>
                                <select
                                    value={filters.level || ''}
                                    onChange={(e) => handleFilterChange('level', e.target.value)}
                                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
                                >
                                    <option value="">{t('common.all', 'All')}</option>
                                    <option value="debug">Debug</option>
                                    <option value="info">Info</option>
                                    <option value="warning">Warning</option>
                                    <option value="error">Error</option>
                                    <option value="critical">Critical</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('logs.endpoint', 'Endpoint')}
                                </label>
                                <input
                                    type="text"
                                    value={filters.endpoint || ''}
                                    onChange={(e) => handleFilterChange('endpoint', e.target.value)}
                                    placeholder="/api/..."
                                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('logs.action', 'Action')}
                                </label>
                                <select
                                    value={filters.action || ''}
                                    onChange={(e) => handleFilterChange('action', e.target.value)}
                                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
                                >
                                    <option value="">{t('common.all', 'All')}</option>
                                    <option value="auth">Auth</option>
                                    <option value="sync">Sync</option>
                                    <option value="analysis">Analysis</option>
                                    <option value="gdpr">GDPR</option>
                                    <option value="report">Report</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('logs.statusRange', 'Status')}
                                </label>
                                <select
                                    value={`${filters.min_status || ''}-${filters.max_status || ''}`}
                                    onChange={(e) => {
                                        const [min, max] = e.target.value.split('-').map((v) => v ? parseInt(v) : undefined);
                                        handleFilterChange('min_status', min);
                                        handleFilterChange('max_status', max);
                                    }}
                                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
                                >
                                    <option value="-">{t('common.all', 'All')}</option>
                                    <option value="200-299">2xx Success</option>
                                    <option value="400-499">4xx Client Error</option>
                                    <option value="500-599">5xx Server Error</option>
                                </select>
                            </div>
                        </div>
                    )}
                </div>

                {/* Error */}
                {error && <ErrorMessage message={String(error)} />}

                {/* Loading */}
                {isLoading && (
                    <div className="flex justify-center py-12">
                        <LoadingSpinner />
                    </div>
                )}

                {/* Logs Table */}
                {logsData && !isLoading && (
                    <div className="bg-white rounded-lg shadow overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            {t('logs.timestamp', 'Timestamp')}
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            {t('logs.level', 'Level')}
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            {t('logs.endpoint', 'Endpoint')}
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            {t('logs.message', 'Message')}
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            {t('logs.status', 'Status')}
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            {t('logs.duration', 'Duration')}
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {logsData.logs.map((log: LogEntry) => (
                                        <tr key={log.id} className="hover:bg-gray-50">
                                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                                                {formatDate(log.created_at)}
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap">
                                                <span
                                                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${logService.getLevelColor(
                                                        log.level
                                                    )}`}
                                                >
                                                    {log.level.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-sm text-gray-500">
                                                <span className="font-mono text-xs">
                                                    {log.method && <span className="text-primary font-medium">{log.method} </span>}
                                                    {log.endpoint || '-'}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-sm text-gray-900">
                                                {truncateMessage(log.message)}
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap">
                                                {log.response_status && (
                                                    <span
                                                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${logService.getStatusColor(
                                                            log.response_status
                                                        )}`}
                                                    >
                                                        {log.response_status}
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                                                {log.duration_ms ? `${log.duration_ms}ms` : '-'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Pagination */}
                        {logsData.total > logsData.page_size && (
                            <div className="px-4 py-3 border-t flex items-center justify-between">
                                <div className="text-sm text-gray-500">
                                    {t('logs.page', 'Page')} {logsData.page} {t('logs.of', 'of')}{' '}
                                    {Math.ceil(logsData.total / logsData.page_size)}
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => handlePageChange(logsData.page - 1)}
                                        disabled={logsData.page <= 1}
                                        className="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <ChevronLeft className="w-5 h-5" />
                                    </button>
                                    <button
                                        onClick={() => handlePageChange(logsData.page + 1)}
                                        disabled={!logsData.has_more}
                                        className="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <ChevronRight className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Empty state */}
                {logsData && logsData.logs.length === 0 && (
                    <div className="bg-white rounded-lg shadow p-12 text-center">
                        <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">
                            {t('logs.empty', 'No logs found')}
                        </h3>
                        <p className="text-gray-500">
                            {t('logs.emptyDescription', 'No audit logs match your current filters.')}
                        </p>
                    </div>
                )}
            </main>
        </div>
    );
};

export default AdminLogsPage;
