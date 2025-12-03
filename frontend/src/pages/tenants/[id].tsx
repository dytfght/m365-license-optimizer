import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Navbar } from '../../components/Navbar';
import { tenantService } from '../../services/tenantService';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { CheckCircle, AlertCircle } from 'lucide-react';
import { useRequireAuth } from '../../hooks/useRequireAuth';

const TenantDetailPage: React.FC = () => {
    const router = useRouter();
    const { id } = router.query;
    const { t } = useTranslation();
    const { user, loading: authLoading } = useRequireAuth();
    const [syncMessage, setSyncMessage] = useState<string | null>(null);
    const [syncError, setSyncError] = useState<string | null>(null);

    const { data: tenant, isLoading, error } = useQuery({
        queryKey: ['tenant', id],
        queryFn: () => tenantService.getById(id as string),
        enabled: !!id
    });

    const syncUsersMutation = useMutation({
        mutationFn: () => tenantService.syncUsers(id as string),
        onSuccess: () => {
            setSyncMessage(t('Users synced successfully'));
            setSyncError(null);
        },
        onError: (error: Error) => {
            setSyncError(t('Failed to sync users'));
            setSyncMessage(null);
        }
    });

    const syncLicensesMutation = useMutation({
        mutationFn: () => tenantService.syncLicenses(id as string),
        onSuccess: () => {
            setSyncMessage(t('Licenses synced successfully'));
            setSyncError(null);
        },
        onError: (error: Error) => {
            setSyncError(t('Failed to sync licenses'));
            setSyncMessage(null);
        }
    });

    const syncUsageMutation = useMutation({
        mutationFn: () => tenantService.syncUsage(id as string),
        onSuccess: () => {
            setSyncMessage(t('Usage synced successfully'));
            setSyncError(null);
        },
        onError: (error: Error) => {
            setSyncError(t('Failed to sync usage'));
            setSyncMessage(null);
        }
    });

    if (authLoading || isLoading) return <div className="min-h-screen bg-gray-100"><Navbar /><div className="p-8 flex justify-center"><LoadingSpinner /></div></div>;
    if (error) return <div className="min-h-screen bg-gray-100"><Navbar /><div className="p-8"><ErrorMessage message={t('Failed to load tenant')} /></div></div>;
    if (!user) return null;

    return (
        <div className="min-h-screen bg-gray-100">
            <Navbar />
            <main className="py-10">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="md:flex md:items-center md:justify-between">
                        <div className="min-w-0 flex-1">
                            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
                                {tenant?.name}
                            </h2>
                            <p className="mt-1 text-sm text-gray-500">{tenant?.domain_name}</p>
                        </div>
                    </div>

                    {syncMessage && (
                        <div className="mt-4 rounded-md bg-green-50 p-4">
                            <div className="flex">
                                <div className="flex-shrink-0">
                                    <CheckCircle className="h-5 w-5 text-green-400" aria-hidden="true" />
                                </div>
                                <div className="ml-3">
                                    <p className="text-sm font-medium text-green-800">{syncMessage}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {syncError && (
                        <div className="mt-4 rounded-md bg-red-50 p-4">
                            <div className="flex">
                                <div className="flex-shrink-0">
                                    <AlertCircle className="h-5 w-5 text-red-400" aria-hidden="true" />
                                </div>
                                <div className="ml-3">
                                    <p className="text-sm font-medium text-red-800">{syncError}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-3">
                        <div className="bg-white overflow-hidden shadow rounded-lg p-6">
                            <h3 className="text-lg font-medium text-gray-900">{t('Sync Users')}</h3>
                            <p className="mt-2 text-sm text-gray-500">{t('Fetch latest users from Microsoft Graph')}</p>
                            <button
                                onClick={() => syncUsersMutation.mutate()}
                                disabled={syncUsersMutation.isPending}
                                className="mt-4 w-full inline-flex justify-center items-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-600 disabled:opacity-50"
                            >
                                {syncUsersMutation.isPending ? <LoadingSpinner className="h-4 w-4 text-white" /> : t('Sync Users')}
                            </button>
                        </div>

                        <div className="bg-white overflow-hidden shadow rounded-lg p-6">
                            <h3 className="text-lg font-medium text-gray-900">{t('Sync Licenses')}</h3>
                            <p className="mt-2 text-sm text-gray-500">{t('Fetch assigned licenses')}</p>
                            <button
                                onClick={() => syncLicensesMutation.mutate()}
                                disabled={syncLicensesMutation.isPending}
                                className="mt-4 w-full inline-flex justify-center items-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-600 disabled:opacity-50"
                            >
                                {syncLicensesMutation.isPending ? <LoadingSpinner className="h-4 w-4 text-white" /> : t('Sync Licenses')}
                            </button>
                        </div>

                        <div className="bg-white overflow-hidden shadow rounded-lg p-6">
                            <h3 className="text-lg font-medium text-gray-900">{t('Sync Usage')}</h3>
                            <p className="mt-2 text-sm text-gray-500">{t('Fetch activity reports')}</p>
                            <button
                                onClick={() => syncUsageMutation.mutate()}
                                disabled={syncUsageMutation.isPending}
                                className="mt-4 w-full inline-flex justify-center items-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-600 disabled:opacity-50"
                            >
                                {syncUsageMutation.isPending ? <LoadingSpinner className="h-4 w-4 text-white" /> : t('Sync Usage')}
                            </button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default TenantDetailPage;
