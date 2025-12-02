import { authService } from '@/services/authService';
import api from '@/services/api';

jest.mock('@/services/api');

describe('authService', () => {
    it('login calls api', async () => {
        (api.post as jest.Mock).mockResolvedValue({ data: { access_token: 'token' } });
        const result = await authService.login('user', 'pass');
        expect(api.post).toHaveBeenCalledWith('/auth/login', expect.any(FormData), expect.any(Object));
        expect(result).toEqual({ access_token: 'token' });
    });

    it('logout removes token', () => {
        const removeItemSpy = jest.spyOn(Storage.prototype, 'removeItem');
        // Mock window.location
        Object.defineProperty(window, 'location', {
            value: { href: '' },
            writable: true
        });

        authService.logout();
        expect(removeItemSpy).toHaveBeenCalledWith('token');
        expect(window.location.href).toBe('/login');
    });
});
