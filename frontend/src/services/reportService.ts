import api from './api';
import { Report } from '../types';

// Get the backend base URL (without /api/v1)
const getBackendBaseUrl = () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    // Remove /api/v1 suffix to get base URL, then add it back with the file path
    return apiUrl;
};

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
        const downloadPath = response.data.download_url;
        // The backend returns a relative path like /api/v1/reports/{id}/file
        // We need to prepend the backend base URL
        const backendBase = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace('/api/v1', '');
        return `${backendBase}${downloadPath}`;
    }
};

