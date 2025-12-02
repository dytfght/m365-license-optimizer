import api from './api';
import { Report } from '../types';

export const reportService = {
    generatePdf: async (analysisId: string): Promise<Report> => {
        const response = await api.post<Report>(`/reports/analyses/${analysisId}/pdf`);
        return response.data;
    },

    generateExcel: async (analysisId: string): Promise<Report> => {
        const response = await api.post<Report>(`/reports/analyses/${analysisId}/excel`);
        return response.data;
    },

    getByAnalysis: async (analysisId: string): Promise<Report[]> => {
        const response = await api.get<{ reports?: Report[] } | Report[]>(`/reports/analyses/${analysisId}`);
        // Handle both array and object responses
        return Array.isArray(response.data) ? response.data : (response.data.reports || []);
    },

    getDownloadUrl: async (reportId: string): Promise<string> => {
        const response = await api.get<{ download_url: string }>(`/reports/${reportId}/download`);
        return response.data.download_url;
    }
};
