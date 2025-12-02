import api from './api';
import { Analysis } from '../types';

export const analysisService = {
    getByTenant: async (tenantId: string): Promise<Analysis[]> => {
        const response = await api.get<{ analyses?: Analysis[] } | Analysis[]>(`/analyses/tenants/${tenantId}/analyses`);
        // Handle both array and object responses
        return Array.isArray(response.data) ? response.data : (response.data.analyses || []);
    },

    getById: async (id: string): Promise<Analysis> => {
        const response = await api.get<Analysis>(`/analyses/analyses/${id}`);
        return response.data;
    },

    create: async (tenantId: string): Promise<Analysis> => {
        const response = await api.post<Analysis>(`/analyses/tenants/${tenantId}/analyses`);
        return response.data;
    },

    applyRecommendation: async (recommendationId: string): Promise<void> => {
        await api.post(`/analyses/recommendations/${recommendationId}/apply`);
    }
};
