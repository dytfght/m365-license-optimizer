import React from 'react';
import { useRouter } from 'next/router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Navbar } from '../../components/Navbar';
import { reportService } from '../../services/reportService';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorMessage } from '../../components/ErrorMessage';
import { FileText, FileSpreadsheet, Download } from 'lucide-react';

const ReportsPage: React.FC = () => {
    const router = useRouter();
    const { analysisId } = router.query;
    const { t } = useTranslation();
    const queryClient = useQueryClient();

    const { data: reports, isLoading, error } = useQuery({
        queryKey: ['reports', analysisId],
        queryFn: () => reportService.getByAnalysis(analysisId as string),
        enabled: !!analysisId
    });

    const generatePdfMutation = useMutation({
        mutationFn: () => reportService.generatePdf(analysisId as string),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reports', analysisId] })
    });

    const generateExcelMutation = useMutation({
        mutationFn: () => reportService.generateExcel(analysisId as string),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reports', analysisId] })
    });

    const handleDownload = async (reportId: string) => {
        try {
            const url = await reportService.getDownloadUrl(reportId);
            window.open(url, '_blank');
        } catch (e) {
            console.error("Failed to get download URL", e);
        }
    };

    if (isLoading) return <div className="min-h-screen bg-gray-100"><Navbar /><div className="p-8 flex justify-center"><LoadingSpinner /></div></div>;
    if (error) return <div className="min-h-screen bg-gray-100"><Navbar /><div className="p-8"><ErrorMessage message="Failed to load reports" /></div></div>;

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
                                {generatePdfMutation.isPending ? <LoadingSpinner className="h-4 w-4" /> : <><FileText className="mr-2 h-4 w-4" /> Generate PDF</>}
                            </button>
                            <button
                                onClick={() => generateExcelMutation.mutate()}
                                disabled={generateExcelMutation.isPending}
                                className="inline-flex items-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50"
                            >
                                {generateExcelMutation.isPending ? <LoadingSpinner className="h-4 w-4" /> : <><FileSpreadsheet className="mr-2 h-4 w-4" /> Generate Excel</>}
                            </button>
                        </div>
                    </div>

                    <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                        {reports?.map((report) => (
                            <div key={report.id} className="overflow-hidden rounded-lg bg-white shadow">
                                <div className="px-4 py-5 sm:p-6">
                                    <div className="flex items-center">
                                        <div className="flex-shrink-0">
                                            {report.format === 'pdf' ? <FileText className="h-8 w-8 text-red-500" /> : <FileSpreadsheet className="h-8 w-8 text-green-500" />}
                                        </div>
                                        <div className="ml-5 w-0 flex-1">
                                            <dl>
                                                <dt className="truncate text-sm font-medium text-gray-500">{report.name}</dt>
                                                <dd>
                                                    <div className="text-lg font-medium text-gray-900">{report.format.toUpperCase()}</div>
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
