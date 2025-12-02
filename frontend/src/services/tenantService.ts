import api from './api';
import { Tenant } from '../types';

export const tenantService = {
    getAll: async (): Promise<Tenant[]> => {
        const response = await api.get<{ tenants: Tenant[]; total: number }>('/tenants');
        return response.data.tenants; // Extract tenants array from TenantList object
    },

    getById: async (id: string): Promise<Tenant> => {
        const response = await api.get<Tenant>(`/tenants/${id}`);
        return response.data;
    },

    create: async (data: Partial<Tenant>): Promise<Tenant> => {
        const response = await api.post<Tenant>('/tenants', data);
        return response.data;
    },

    syncUsers: async (id: string) => {
        const response = await api.post(`/tenants/${id}/sync_users`);
        return response.data;
    },

    syncLicenses: async (id: string) => {
        const response = await api.post(`/tenants/${id}/sync_licenses`);
        return response.data;
    },

    syncUsage: async (id: string) => {
        const response = await api.post(`/tenants/${id}/sync_usage`);
        return response.data;
    }
};
