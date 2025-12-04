import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Shield, X, AlertTriangle, CheckCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import gdprService from '../services/gdprService';
import { LoadingSpinner } from './LoadingSpinner';

interface GdprConsentModalProps {
    tenantId: string;
    tenantName: string;
    isOpen: boolean;
    onClose: () => void;
    onConsentGiven: () => void;
}

const GdprConsentModal: React.FC<GdprConsentModalProps> = ({
    tenantId,
    tenantName,
    isOpen,
    onClose,
    onConsentGiven,
}) => {
    const { t } = useTranslation();
    const [isChecked, setIsChecked] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const consentMutation = useMutation({
        mutationFn: () => gdprService.recordConsent(tenantId, true),
        onSuccess: () => {
            onConsentGiven();
            onClose();
        },
        onError: (err: Error) => {
            setError(err.message || 'Failed to record consent');
        },
    });

    if (!isOpen) return null;

    const handleAccept = () => {
        if (!isChecked) {
            setError('Please accept the terms to continue');
            return;
        }
        setError(null);
        consentMutation.mutate();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b">
                    <div className="flex items-center gap-2">
                        <Shield className="w-6 h-6 text-primary" />
                        <h2 className="text-xl font-semibold text-gray-900">
                            {t('gdpr.consentTitle', 'GDPR Data Processing Consent')}
                        </h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <p className="text-sm text-blue-800">
                            {t(
                                'gdpr.tenantInfo',
                                `You are about to process data for tenant: `
                            )}
                            <strong>{tenantName}</strong>
                        </p>
                    </div>

                    <div className="space-y-3">
                        <h3 className="font-medium text-gray-900">
                            {t('gdpr.processingPurposes', 'Data Processing Purposes')}
                        </h3>
                        <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                            <li>{t('gdpr.purpose1', 'License usage analysis and optimization')}</li>
                            <li>{t('gdpr.purpose2', 'Cost reduction recommendations')}</li>
                            <li>{t('gdpr.purpose3', 'User activity monitoring for license assignment')}</li>
                            <li>{t('gdpr.purpose4', 'Report generation and export')}</li>
                        </ul>
                    </div>

                    <div className="space-y-3">
                        <h3 className="font-medium text-gray-900">
                            {t('gdpr.dataCategories', 'Data Categories Processed')}
                        </h3>
                        <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                            <li>{t('gdpr.data1', 'User principal names (email addresses)')}</li>
                            <li>{t('gdpr.data2', 'License assignments and SKUs')}</li>
                            <li>{t('gdpr.data3', 'Service usage metrics')}</li>
                            <li>{t('gdpr.data4', 'Department and job information')}</li>
                        </ul>
                    </div>

                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <div className="flex items-start gap-2">
                            <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                            <div className="text-sm text-yellow-800">
                                <p className="font-medium">
                                    {t('gdpr.retentionNotice', 'Data Retention')}
                                </p>
                                <p>
                                    {t(
                                        'gdpr.retentionText',
                                        'Usage data is retained for 90 days. You can request data export or deletion at any time.'
                                    )}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-3">
                        <h3 className="font-medium text-gray-900">
                            {t('gdpr.yourRights', 'Your Rights')}
                        </h3>
                        <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                            <li>{t('gdpr.right1', 'Right to access your data')}</li>
                            <li>{t('gdpr.right2', 'Right to data portability (export)')}</li>
                            <li>{t('gdpr.right3', 'Right to erasure (right to be forgotten)')}</li>
                            <li>{t('gdpr.right4', 'Right to withdraw consent at any time')}</li>
                        </ul>
                    </div>

                    {/* Checkbox */}
                    <div className="flex items-start gap-3 pt-4 border-t">
                        <input
                            type="checkbox"
                            id="gdpr-consent"
                            checked={isChecked}
                            onChange={(e) => setIsChecked(e.target.checked)}
                            className="mt-1 h-4 w-4 text-primary border-gray-300 rounded focus:ring-primary"
                        />
                        <label htmlFor="gdpr-consent" className="text-sm text-gray-700">
                            {t(
                                'gdpr.consentCheckbox',
                                'I consent to the processing of personal data as described above. I understand I can withdraw consent at any time.'
                            )}
                        </label>
                    </div>

                    {/* Error message */}
                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                            {error}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end gap-3 p-4 border-t bg-gray-50">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                    >
                        {t('common.cancel', 'Cancel')}
                    </button>
                    <button
                        onClick={handleAccept}
                        disabled={!isChecked || consentMutation.isPending}
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        {consentMutation.isPending ? (
                            <LoadingSpinner />
                        ) : (
                            <CheckCircle className="w-4 h-4" />
                        )}
                        {t('gdpr.acceptAndContinue', 'Accept & Continue')}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default GdprConsentModal;
