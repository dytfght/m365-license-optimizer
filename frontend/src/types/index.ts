export interface Tenant {
    id: string;
    name: string;
    domain_name: string;
    tenant_id: string;
    client_id?: string;
    client_secret?: string;
    created_at: string;
    updated_at: string;
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

export interface Analysis {
    id: string;
    tenant_id: string;
    name: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    created_at: string;
    recommendations?: Recommendation[];
}

export interface Recommendation {
    id: string;
    analysis_id: string;
    user_id?: string;
    user_email?: string;
    action: 'downgrade' | 'remove' | 'upsell';
    sku_from?: string;
    sku_to?: string;
    savings: number;
    status: 'pending' | 'applied' | 'rejected';
}

export interface Report {
    id: string;
    analysis_id: string;
    name: string;
    format: 'pdf' | 'excel';
    status: 'generated' | 'failed';
    download_url?: string;
    created_at: string;
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
