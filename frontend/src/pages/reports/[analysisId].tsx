import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Navbar } from '../../components/Navbar';
import { reportService } from '../../services/reportService';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { FileText, FileSpreadsheet, Download, CheckCircle, AlertCircle } from 'lucide-react';
import { useRequireAuth } from '../../hooks/useRequireAuth';

const ReportsPage: React.FC = () => {
    const router = useRouter();
    const { analysisId } = router.query;
    const { t } = useTranslation();
    const queryClient = useQueryClient();
    const { user, loading: authLoading } = useRequireAuth();
    const [reportMessage, setReportMessage] = useState<string | null>(null);
    const [reportError, setReportError] = useState<string | null>(null);

    const { data: reports, isLoading, error } = useQuery({
        queryKey: ['reports', analysisId],
        queryFn: () => reportService.getByAnalysis(analysisId as string),
        enabled: !!analysisId
    });

    const generatePdfMutation = useMutation({
        mutationFn: () => reportService.generatePdf(analysisId as string),
        onSuccess: () => {
            setReportMessage(t('Report generated successfully'));
            setReportError(null);
            queryClient.invalidateQueries({ queryKey: ['reports', analysisId] });
        },
        onError: (error: Error) => {
            setReportError(t('Failed to generate report'));
            setReportMessage(null);
        }
    });

    const generateExcelMutation = useMutation({
        mutationFn: () => reportService.generateExcel(analysisId as string),
        onSuccess: () => {
            setReportMessage(t('Report generated successfully'));
            setReportError(null);
            queryClient.invalidateQueries({ queryKey: ['reports', analysisId] });
        },
        onError: (error: Error) => {
            setReportError(t('Failed to generate report'));
            setReportMessage(null);
        }
    });

    const handleDownload = async (reportId: string) => {
        try {
            const url = await reportService.getDownloadUrl(reportId);
            const token = localStorage.getItem('token');

            // Fetch the file with authentication
            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error(`Download failed: ${response.status}`);
            }

            // Get the filename from Content-Disposition header or use a default
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'report';
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="?(.+)"?/);
                if (match) filename = match[1];
            }

            // Create blob and trigger download
            const blob = await response.blob();
            const blobUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(blobUrl);
        } catch (e) {
            console.error("Failed to download report", e);
            setReportError(t('Failed to download report'));
        }
    };

    if (authLoading || isLoading) return <div className="min-h-screen bg-gray-100"><Navbar /><div className="p-8 flex justify-center"><LoadingSpinner /></div></div>;
    if (error) return <div className="min-h-screen bg-gray-100"><Navbar /><div className="p-8"><ErrorMessage message={t('Failed to load reports')} /></div></div>;
    if (!user) return null;

    return (
        <div className="min-h-screen bg-gray-100">
            <Navbar />
            <main className="py-10">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="md:flex md:items-center md:justify-between">
                        <div className="min-w-0 flex-1">
                            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
                                {t('Reports')}
                            </h2>
                        </div>
                        <div className="mt-4 flex md:ml-4 md:mt-0 space-x-3">
                            <button
                                onClick={() => generatePdfMutation.mutate()}
                                disabled={generatePdfMutation.isPending}
                                className="inline-flex items-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50"
                            >
                                {generatePdfMutation.isPending ? <LoadingSpinner className="h-4 w-4" /> : <><FileText className="mr-2 h-4 w-4" /> {t('Generate PDF')}</>}
                            </button>
                            <button
                                onClick={() => generateExcelMutation.mutate()}
                                disabled={generateExcelMutation.isPending}
                                className="inline-flex items-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50"
                            >
                                {generateExcelMutation.isPending ? <LoadingSpinner className="h-4 w-4" /> : <><FileSpreadsheet className="mr-2 h-4 w-4" /> {t('Generate Excel')}</>}
                            </button>
                        </div>
                    </div>

                    {reportMessage && (
                        <div className="mt-4 rounded-md bg-green-50 p-4">
                            <div className="flex">
                                <div className="flex-shrink-0">
                                    <CheckCircle className="h-5 w-5 text-green-400" aria-hidden="true" />
                                </div>
                                <div className="ml-3">
                                    <p className="text-sm font-medium text-green-800">{reportMessage}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {reportError && (
                        <div className="mt-4 rounded-md bg-red-50 p-4">
                            <div className="flex">
                                <div className="flex-shrink-0">
                                    <AlertCircle className="h-5 w-5 text-red-400" aria-hidden="true" />
                                </div>
                                <div className="ml-3">
                                    <p className="text-sm font-medium text-red-800">{reportError}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                        {reports?.map((report) => (
                            <div key={report.id} className="overflow-hidden rounded-lg bg-white shadow">
                                <div className="px-4 py-5 sm:p-6">
                                    <div className="flex items-center">
                                        <div className="flex-shrink-0">
                                            {report.report_type?.toUpperCase() === 'PDF' ? <FileText className="h-8 w-8 text-red-500" /> : <FileSpreadsheet className="h-8 w-8 text-green-500" />}
                                        </div>
                                        <div className="ml-5 w-0 flex-1">
                                            <dl>
                                                <dt className="truncate text-sm font-medium text-gray-500">{report.file_name || 'Report'}</dt>
                                                <dd>
                                                    <div className="text-lg font-medium text-gray-900">{report.report_type || 'Unknown'}</div>
                                                </dd>
                                            </dl>
                                        </div>
                                    </div>
                                </div>
                                <div className="bg-gray-50 px-4 py-4 sm:px-6">
                                    <div className="text-sm">
                                        <button onClick={() => handleDownload(report.id)} className="font-medium text-primary hover:text-blue-900 flex items-center">
                                            <Download className="mr-2 h-4 w-4" /> {t('Download Report')}
                                        </button>
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

export default ReportsPage;
