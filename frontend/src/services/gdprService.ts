/**
 * GDPR Service for LOT 10
 * Handles consent management and data export operations.
 */
import api from './api';

export interface ConsentResponse {
    tenant_id: string;
    gdpr_consent: boolean;
    gdpr_consent_date: string | null;
    message: string;
}

export interface ConsentStatus {
    tenant_id: string;
    has_consent: boolean;
}

export interface UserDataExport {
    export_date: string;
    export_type: string;
    user: {
        id: string;
        graph_id: string;
        user_principal_name: string;
        display_name: string | null;
        department: string | null;
        job_title: string | null;
        account_enabled: boolean;
        created_at: string | null;
    };
    license_assignments: Array<{
        sku_id: string;
        assignment_date: string | null;
        status: string | null;
        source: string | null;
    }>;
    usage_metrics: Array<{
        service_name: string;
        activity_date: string | null;
        is_active: boolean;
    }>;
    recommendations: Array<{
        id: string;
        recommendation_type: string | null;
        status: string | null;
        current_sku_id: string | null;
        recommended_sku_id: string | null;
        estimated_savings: number | null;
    }>;
}

export interface DeletionResponse {
    user_id: string;
    action: string;
    timestamp: string;
    data_affected: Record<string, string>;
}

const gdprService = {
    /**
     * Record GDPR consent for a tenant.
     */
    async recordConsent(tenantId: string, consentGiven: boolean = true): Promise<ConsentResponse> {
        const response = await api.post<ConsentResponse>(`/gdpr/consent/${tenantId}`, {
            consent_given: consentGiven,
        });
        return response.data;
    },

    /**
     * Check GDPR consent status for a tenant.
     */
    async checkConsent(tenantId: string): Promise<ConsentStatus> {
        const response = await api.get<ConsentStatus>(`/gdpr/consent/${tenantId}`);
        return response.data;
    },

    /**
     * Revoke GDPR consent for a tenant.
     */
    async revokeConsent(tenantId: string): Promise<ConsentResponse> {
        return this.recordConsent(tenantId, false);
    },

    /**
     * Export all personal data for a user.
     */
    async exportUserData(userId: string): Promise<UserDataExport> {
        const response = await api.get<UserDataExport>(`/gdpr/export/${userId}`);
        return response.data;
    },

    /**
     * Delete or anonymize user data.
     */
    async deleteUserData(userId: string, anonymize: boolean = false): Promise<DeletionResponse> {
        const response = await api.delete<DeletionResponse>(`/gdpr/delete/${userId}`, {
            params: { anonymize },
        });
        return response.data;
    },

    /**
     * Download GDPR registry PDF.
     */
    async downloadRegistry(): Promise<Blob> {
        const response = await api.post('/gdpr/admin/registry', {}, {
            responseType: 'blob',
        });
        return response.data;
    },

    /**
     * Download and save registry PDF as file.
     */
    async saveRegistryAsPdf(): Promise<void> {
        const blob = await this.downloadRegistry();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'gdpr_registry.pdf';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    },
};

export default gdprService;
