import React from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';
import { Navbar } from '../components/Navbar';
import { tenantService } from '../services/tenantService';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';

const DashboardPage: React.FC = () => {
    const { t } = useTranslation();
    const { data: tenants, isLoading, error } = useQuery({
        queryKey: ['tenants'],
        queryFn: tenantService.getAll
    });

    if (isLoading) return (
        <div className="min-h-screen bg-gray-100">
            <Navbar />
            <div className="p-8 flex justify-center">
                <LoadingSpinner />
            </div>
        </div>
    );

    if (error) return (
        <div className="min-h-screen bg-gray-100">
            <Navbar />
            <div className="p-8">
                <ErrorMessage message="Failed to load tenants" />
            </div>
        </div>
    );

    return (
        <div className="min-h-screen bg-gray-100">
            <Navbar />
            <main className="py-10">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <h1 className="text-3xl font-bold leading-tight tracking-tight text-gray-900">
                        {t('Tenants')}
                    </h1>
                    <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                        {tenants?.map((tenant) => (
                            <div key={tenant.id} className="overflow-hidden rounded-lg bg-white shadow hover:shadow-md transition-shadow">
                                <div className="px-4 py-5 sm:p-6">
                                    <h3 className="text-lg font-medium leading-6 text-gray-900">{tenant.name}</h3>
                                    <p className="mt-1 text-sm text-gray-500">{tenant.domain_name}</p>
                                    <p className="mt-2 text-xs text-gray-400">ID: {tenant.tenant_id}</p>
                                    <div className="mt-4 flex space-x-3">
                                        <Link
                                            href={`/tenants/${tenant.id}`}
                                            className="inline-flex items-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                                        >
                                            Details
                                        </Link>
                                        <Link
                                            href={`/analyses/${tenant.id}`}
                                            className="inline-flex items-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-600"
                                        >
                                            {t('Analyses')}
                                        </Link>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default DashboardPage;
