import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LoginForm } from '@/components/LoginForm';
import { authService } from '@/services/authService';

jest.mock('@/services/authService');

describe('LoginForm', () => {
    it('renders login form', () => {
        render(<LoginForm />);
        expect(screen.getByLabelText('Username')).toBeInTheDocument();
        expect(screen.getByLabelText('Password')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
    });

    it('handles submission', async () => {
        (authService.login as jest.Mock).mockResolvedValue({ access_token: 'token' });
        render(<LoginForm />);

        fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
        fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } });
        fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

        await waitFor(() => {
            expect(authService.login).toHaveBeenCalledWith('user', 'pass');
        });
    });

    it('displays error on failure', async () => {
        (authService.login as jest.Mock).mockRejectedValue(new Error('Failed'));
        render(<LoginForm />);

        fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'user' } });
        fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pass' } });
        fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

        await waitFor(() => {
            expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
        });
    });
});
