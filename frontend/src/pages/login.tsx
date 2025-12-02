import React from 'react';
import { LoginForm } from '../components/LoginForm';

const LoginPage: React.FC = () => {
    return (
        <div className="flex min-h-screen flex-col justify-center py-12 sm:px-6 lg:px-8 bg-gray-50">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <h1 className="text-center text-3xl font-bold tracking-tight text-primary">
                    M365 License Optimizer
                </h1>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
                    <LoginForm />
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
