// TypeScript types aligned with backend Pydantic schemas

export interface Tenant {
    id: string;
    name: string;
    tenant_id: string;
    country: string;
    default_language: string;
    onboarding_status: 'pending' | 'active' | 'suspended' | 'error';
    csp_customer_id?: string;
    created_at: string;
    updated_at?: string;
    app_registration?: AppRegistration;
}

export interface AppRegistration {
    client_id: string;
    authority_url?: string;
    scopes: string[];
    consent_status: 'pending' | 'granted' | 'expired' | 'revoked';
}

export interface User {
    id: string;
    email: string;
    full_name: string;
    is_active: boolean;
    is_superuser: boolean;
}

export interface Token {
    access_token: string;
    token_type: string;
}

export interface AnalysisSummary {
    total_users: number;
    total_current_cost: number;
    total_optimized_cost: number;
    potential_savings_monthly: number;
    potential_savings_annual: number;
    recommendations_count: number;
    breakdown: Record<string, number>;
}

export interface Analysis {
    id: string;
    tenant_client_id: string;
    analysis_date: string;
    status: 'PENDING' | 'COMPLETED' | 'FAILED';
    summary: AnalysisSummary | Record<string, unknown>;
    error_message?: string;
    created_at: string;
    updated_at?: string;
    recommendations?: Recommendation[];
}

export interface Recommendation {
    id: string;
    analysis_id: string;
    user_id: string;
    current_sku?: string;
    recommended_sku?: string;
    savings_monthly: number;
    reason: string;
    status: 'PENDING' | 'ACCEPTED' | 'REJECTED';
    created_at: string;
    updated_at?: string;
}

// Helper type for frontend display
export type RecommendationAction = 'remove' | 'downgrade' | 'upgrade' | 'no_change';

// Helper function to derive action from recommendation
export function getRecommendationAction(rec: Recommendation): RecommendationAction {
    if (!rec.recommended_sku) return 'remove';
    if (!rec.current_sku) return 'upgrade';
    // Default - could be refined with price comparison
    return rec.savings_monthly > 0 ? 'downgrade' : 'upgrade';
}

export interface Report {
    id: string;
    analysis_id: string;
    tenant_client_id: string;
    report_type: 'PDF' | 'EXCEL';
    file_name: string;
    file_size: number;
    mime_type: string;
    report_metadata: Record<string, unknown>;
    generated_by: string;
    created_at: string;
    expires_at?: string;
    download_url?: string;
}

export interface SkuMapping {
    id: string;
    graph_sku_id: string;
    partner_sku_id: string;
    name: string;
}

export interface AddonCompatibility {
    id: string;
    base_sku_id: string;
    addon_sku_id: string;
    is_compatible: boolean;
}
