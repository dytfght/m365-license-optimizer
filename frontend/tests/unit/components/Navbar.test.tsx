import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Navbar } from '@/components/Navbar';
import { authService } from '@/services/authService';

jest.mock('@/services/authService');

describe('Navbar', () => {
    it('renders links', () => {
        render(<Navbar />);
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Admin')).toBeInTheDocument();
    });

    it('logout calls service', () => {
        render(<Navbar />);
        fireEvent.click(screen.getByTitle('Logout'));
        expect(authService.logout).toHaveBeenCalled();
    });
});
