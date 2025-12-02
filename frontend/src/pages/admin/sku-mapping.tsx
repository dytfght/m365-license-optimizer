import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Navbar } from '../../components/Navbar';
import { skuMappingService } from '../../services/skuMappingService';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { RefreshCw } from 'lucide-react';

const AdminSkuMappingPage: React.FC = () => {
    const { t } = useTranslation();
    const queryClient = useQueryClient();

    const { data: summary, isLoading, error } = useQuery({
        queryKey: ['skuMappingSummary'],
        queryFn: skuMappingService.getSummary
    });

    const syncProductsMutation = useMutation({
        mutationFn: skuMappingService.syncProducts,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['skuMappingSummary'] })
    });

    const syncCompatibilityMutation = useMutation({
        mutationFn: skuMappingService.syncCompatibility,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['skuMappingSummary'] })
    });

    if (isLoading) return <div className="min-h-screen bg-gray-100"><Navbar /><div className="p-8 flex justify-center"><LoadingSpinner /></div></div>;
    if (error) return <div className="min-h-screen bg-gray-100"><Navbar /><div className="p-8"><ErrorMessage message="Failed to load SKU mapping summary" /></div></div>;

    return (
        <div className="min-h-screen bg-gray-100">
            <Navbar />
            <main className="py-10">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="md:flex md:items-center md:justify-between">
                        <div className="min-w-0 flex-1">
                            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
                                Admin SKU Mapping
                            </h2>
                        </div>
                        <div className="mt-4 flex md:ml-4 md:mt-0 space-x-3">
                            <button
                                onClick={() => syncProductsMutation.mutate()}
                                disabled={syncProductsMutation.isPending}
                                className="inline-flex items-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50"
                            >
                                {syncProductsMutation.isPending ? <LoadingSpinner className="h-4 w-4" /> : <><RefreshCw className="mr-2 h-4 w-4" /> Sync Products</>}
                            </button>
                            <button
                                onClick={() => syncCompatibilityMutation.mutate()}
                                disabled={syncCompatibilityMutation.isPending}
                                className="inline-flex items-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50"
                            >
                                {syncCompatibilityMutation.isPending ? <LoadingSpinner className="h-4 w-4" /> : <><RefreshCw className="mr-2 h-4 w-4" /> Sync Compatibility</>}
                            </button>
                        </div>
                    </div>

                    <div className="mt-8 bg-white shadow overflow-hidden sm:rounded-lg">
                        <div className="px-4 py-5 sm:px-6">
                            <h3 className="text-lg leading-6 font-medium text-gray-900">Summary Statistics</h3>
                        </div>
                        <div className="border-t border-gray-200 px-4 py-5 sm:p-0">
                            <dl className="sm:divide-y sm:divide-gray-200">
                                {Object.entries(summary || {}).map(([key, value]) => (
                                    <div key={key} className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                                        <dt className="text-sm font-medium text-gray-500 capitalize">{key.replace(/_/g, ' ')}</dt>
                                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{String(value)}</dd>
                                    </div>
                                ))}
                            </dl>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default AdminSkuMappingPage;
