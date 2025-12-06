#!/bin/bash
# =============================================================================
# Blue-Green Deployment Script for M365 License Optimizer
# Zero-downtime deployment using Docker tag switching
# =============================================================================

set -e

# Configuration
ACR_NAME="${ACR_NAME:-m365optimizeracr}"
IMAGE_NAME="${IMAGE_NAME:-m365-backend}"
RESOURCE_GROUP="${RESOURCE_GROUP:-m365-optimizer-prod}"
WEBAPP_NAME="${WEBAPP_NAME:-m365-optimizer-backend}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/health}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-60}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get current active slot (blue or green)
get_active_slot() {
    local current_tag=$(az webapp config container show \
        -g "$RESOURCE_GROUP" -n "$WEBAPP_NAME" \
        --query "[?name=='DOCKER_CUSTOM_IMAGE_NAME'].value" -o tsv 2>/dev/null | grep -oE ':(blue|green)$' | tr -d ':')
    
    if [[ "$current_tag" == "blue" ]]; then
        echo "blue"
    elif [[ "$current_tag" == "green" ]]; then
        echo "green"
    else
        echo "blue"  # Default to blue if unknown
    fi
}

# Health check function
health_check() {
    local url="$1"
    local timeout="$2"
    local start_time=$(date +%s)
    
    log_info "Waiting for health check at $url..."
    
    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [[ $elapsed -ge $timeout ]]; then
            log_error "Health check timed out after ${timeout}s"
            return 1
        fi
        
        local status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        
        if [[ "$status" == "200" ]]; then
            log_success "Health check passed (HTTP $status)"
            return 0
        fi
        
        log_info "Health check returned HTTP $status, retrying... (${elapsed}s/${timeout}s)"
        sleep 5
    done
}

# Build and push Docker image with specific tag
build_and_push() {
    local tag="$1"
    local image_uri="${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${tag}"
    
    log_info "Building Docker image: $image_uri"
    
    # Login to ACR
    az acr login --name "$ACR_NAME"
    
    # Build and push
    docker build -f backend/Dockerfile -t "$image_uri" backend/
    docker push "$image_uri"
    
    log_success "Image pushed: $image_uri"
}

# Deploy to specific slot
deploy_slot() {
    local slot="$1"
    local image_uri="${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${slot}"
    
    log_info "Deploying $image_uri to $WEBAPP_NAME"
    
    # Update container settings
    az webapp config container set \
        -g "$RESOURCE_GROUP" \
        -n "$WEBAPP_NAME" \
        --docker-custom-image-name "$image_uri" \
        --docker-registry-server-url "https://${ACR_NAME}.azurecr.io"
    
    # Restart the app
    az webapp restart -g "$RESOURCE_GROUP" -n "$WEBAPP_NAME"
    
    log_success "Deployment initiated for $slot slot"
}

# Rollback to previous slot
rollback() {
    local active_slot=$(get_active_slot)
    local rollback_slot
    
    if [[ "$active_slot" == "blue" ]]; then
        rollback_slot="green"
    else
        rollback_slot="blue"
    fi
    
    log_warning "Rolling back from $active_slot to $rollback_slot"
    deploy_slot "$rollback_slot"
    
    log_success "Rollback complete"
}

# Main deployment function
deploy() {
    local active_slot=$(get_active_slot)
    local target_slot
    
    if [[ "$active_slot" == "blue" ]]; then
        target_slot="green"
    else
        target_slot="blue"
    fi
    
    log_info "Current active slot: $active_slot"
    log_info "Target deployment slot: $target_slot"
    
    # Build and push new image
    build_and_push "$target_slot"
    
    # Deploy to target slot
    deploy_slot "$target_slot"
    
    # Wait for deployment and health check
    local webapp_url="https://${WEBAPP_NAME}.azurewebsites.net${HEALTH_ENDPOINT}"
    
    if health_check "$webapp_url" "$HEALTH_TIMEOUT"; then
        log_success "Deployment to $target_slot complete!"
        echo ""
        log_info "Application URL: https://${WEBAPP_NAME}.azurewebsites.net"
        log_info "Active slot: $target_slot"
    else
        log_error "Deployment failed health check, initiating rollback..."
        rollback
        exit 1
    fi
}

# Print usage
usage() {
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  deploy    - Build and deploy to inactive slot (blue-green)"
    echo "  rollback  - Rollback to previous slot"
    echo "  status    - Show current deployment status"
    echo ""
    echo "Environment variables:"
    echo "  ACR_NAME         - Azure Container Registry name (default: m365optimizeracr)"
    echo "  IMAGE_NAME       - Docker image name (default: m365-backend)"
    echo "  RESOURCE_GROUP   - Azure resource group (default: m365-optimizer-prod)"
    echo "  WEBAPP_NAME      - Azure Web App name (default: m365-optimizer-backend)"
    echo "  HEALTH_ENDPOINT  - Health check endpoint (default: /health)"
    echo "  HEALTH_TIMEOUT   - Health check timeout in seconds (default: 60)"
}

# Status command
status() {
    local active_slot=$(get_active_slot)
    log_info "Current Configuration:"
    echo "  ACR:           $ACR_NAME"
    echo "  Image:         $IMAGE_NAME"
    echo "  Resource Group: $RESOURCE_GROUP"
    echo "  Web App:       $WEBAPP_NAME"
    echo "  Active Slot:   $active_slot"
    echo ""
    log_info "Web App URL: https://${WEBAPP_NAME}.azurewebsites.net"
}

# Main entry point
case "${1:-}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    status)
        status
        ;;
    *)
        usage
        exit 1
        ;;
esac
