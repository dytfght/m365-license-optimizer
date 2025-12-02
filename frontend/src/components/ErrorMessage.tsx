import React from 'react';
import { AlertCircle } from 'lucide-react';

interface ErrorMessageProps {
    message: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message }) => {
    return (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative flex items-center gap-2" role="alert">
            <AlertCircle className="h-5 w-5" />
            <span className="block sm:inline">{message}</span>
        </div>
    );
};
