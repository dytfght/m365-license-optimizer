import React from 'react';
import { useRouter } from 'next/router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';
import { Navbar } from '../../components/Navbar';
import { analysisService } from '../../services/analysisService';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';

const AnalysesPage: React.FC = () => {
    const router = useRouter();
    const { tenantId } = router.query;
    const { t } = useTranslation();
    const queryClient = useQueryClient();

    const { data: analyses, isLoading, error } = useQuery({
        queryKey: ['analyses', tenantId],
        queryFn: () => analysisService.getByTenant(tenantId as string),
        enabled: !!tenantId
    });

    const createAnalysisMutation = useMutation({
        mutationFn: () => analysisService.create(tenantId as string),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['analyses', tenantId] });
        }
    });

    if (isLoading) return <div className="min-h-screen bg-gray-100"><Navbar /><div className="p-8 flex justify-center"><LoadingSpinner /></div></div>;
    if (error) return <div className="min-h-screen bg-gray-100"><Navbar /><div className="p-8"><ErrorMessage message="Failed to load analyses" /></div></div>;

    return (
        <div className="min-h-screen bg-gray-100">
            <Navbar />
            <main className="py-10">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="md:flex md:items-center md:justify-between">
                        <div className="min-w-0 flex-1">
                            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
                                {t('Analyses')}
                            </h2>
                        </div>
                        <div className="mt-4 flex md:ml-4 md:mt-0">
                            <button
                                onClick={() => createAnalysisMutation.mutate()}
                                disabled={createAnalysisMutation.isPending}
                                className="ml-3 inline-flex items-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50"
                            >
                                {createAnalysisMutation.isPending ? <LoadingSpinner className="h-4 w-4 text-white" /> : t('Run Analysis')}
                            </button>
                        </div>
                    </div>

                    <div className="mt-8 flow-root">
                        <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                            <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
                                <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
                                    <table className="min-w-full divide-y divide-gray-300">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">ID</th>
                                                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Date</th>
                                                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Status</th>
                                                <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                                                    <span className="sr-only">Actions</span>
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-200 bg-white">
                                            {analyses?.map((analysis) => (
                                                <tr key={analysis.id}>
                                                    <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">{analysis.id.substring(0, 8)}...</td>
                                                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{new Date(analysis.created_at).toLocaleDateString()}</td>
                                                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                                                        <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${analysis.status === 'completed' ? 'bg-green-50 text-green-700 ring-green-600/20' :
                                                                analysis.status === 'failed' ? 'bg-red-50 text-red-700 ring-red-600/20' :
                                                                    'bg-yellow-50 text-yellow-800 ring-yellow-600/20'
                                                            }`}>
                                                            {analysis.status}
                                                        </span>
                                                    </td>
                                                    <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                                                        <Link href={`/reports/${analysis.id}`} className="text-primary hover:text-blue-900">
                                                            {t('Reports')}
                                                        </Link>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default AnalysesPage;
