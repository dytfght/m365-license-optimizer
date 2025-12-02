import api from './api';
import { AddonCompatibility } from '../types';

export const skuMappingService = {
    getSummary: async () => {
        const response = await api.get('/admin/sku-mapping/summary');
        return response.data;
    },

    syncProducts: async () => {
        const response = await api.post('/admin/sku-mapping/sync/products');
        return response.data;
    },

    syncCompatibility: async () => {
        const response = await api.post('/admin/sku-mapping/sync/compatibility');
        return response.data;
    },

    getCompatibleAddons: async (baseSkuId: string): Promise<AddonCompatibility[]> => {
        const response = await api.get<AddonCompatibility[]>(`/admin/sku-mapping/compatible-addons/${baseSkuId}`);
        return response.data;
    }
};
