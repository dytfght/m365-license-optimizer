import { tenantService } from '@/services/tenantService';
import api from '@/services/api';

jest.mock('@/services/api');

describe('tenantService', () => {
    it('getAll calls api', async () => {
        (api.get as jest.Mock).mockResolvedValue({ data: [] });
        await tenantService.getAll();
        expect(api.get).toHaveBeenCalledWith('/tenants');
    });

    it('getById calls api', async () => {
        (api.get as jest.Mock).mockResolvedValue({ data: {} });
        await tenantService.getById('1');
        expect(api.get).toHaveBeenCalledWith('/tenants/1');
    });

    it('syncUsers calls api', async () => {
        (api.post as jest.Mock).mockResolvedValue({ data: {} });
        await tenantService.syncUsers('1');
        expect(api.post).toHaveBeenCalledWith('/tenants/1/sync_users');
    });

    it('syncLicenses calls api', async () => {
        (api.post as jest.Mock).mockResolvedValue({ data: {} });
        await tenantService.syncLicenses('1');
        expect(api.post).toHaveBeenCalledWith('/tenants/1/sync_licenses');
    });

    it('syncUsage calls api', async () => {
        (api.post as jest.Mock).mockResolvedValue({ data: {} });
        await tenantService.syncUsage('1');
        expect(api.post).toHaveBeenCalledWith('/tenants/1/sync_usage');
    });
});
