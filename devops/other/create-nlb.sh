#!/bin/bash

# ==============================================================================
#                             CONFIGURACIÓN INICIAL Y PARÁMETROS FIJOS
# ==============================================================================

# Parámetros fijos basados en los comandos de ejemplo proporcionados
LB_NAME="nlb-mck21"
TG_NAME="tg-mck21"
LB_PORT=80
REGION="us-east-1" 
VPC_ID="vpc-04bd82e2dea9abf35" # ID de VPC fijo
SUBNET_LIST="subnet-056cadb032106905e subnet-0f1791c1ad8fd8463" # Subnets fijas
TARGET_IDS_FORMATTED="git  # IDs de Instancia fijas

echo "Iniciando la configuración de Network Load Balancer (NLB) con parámetros fijos..."

# ==============================================================================
#                                   CREACIÓN DE TARGET GROUP
# ==============================================================================

echo "🎯 Creando Target Group: $TG_NAME..."

# 1. Crear Target Group con parámetros de Health Check explícitos.
TG_ARN=$(aws elbv2 create-target-group \
    --region $REGION \
    --name "$TG_NAME" \
    --protocol TCP \
    --port "$LB_PORT" \
    --vpc-id "$VPC_ID" \
    --target-type instance \
    --health-check-protocol TCP \
    --health-check-interval-seconds 30 \
    --healthy-threshold-count 3 \
    --unhealthy-threshold-count 3 \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)
echo "   > Target Group ARN generado: $TG_ARN"


echo "🔗 Registrando targets en el Target Group..."

# 2. Registrar targets (Instancias) en el Target Group (usando el ARN generado)
aws elbv2 register-targets \
    --region $REGION \
    --target-group-arn "$TG_ARN" \
    --targets $TARGET_IDS_FORMATTED
echo "   > Targets registrados: $TARGET_IDS_FORMATTED"

# ==============================================================================
#                           CREACIÓN DE NETWORK LOAD BALANCER
# ==============================================================================

echo "🚀 Creando Network Load Balancer: $LB_NAME..."

# 3. Crear Network Load Balancer (NLB) con IP address type ipv4
NLB_ARN=$(aws elbv2 create-load-balancer \
    --region $REGION \
    --name "$LB_NAME" \
    --subnets $SUBNET_LIST \
    --scheme internet-facing \
    --type network \
    --ip-address-type ipv4 \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)
echo "   > Network Load Balancer ARN generado: $NLB_ARN"


echo "👂 Creando Listener para el NLB..."

# 4. Crear Listener para el NLB y asociarlo al Target Group (usando ARNs generados)
aws elbv2 create-listener \
    --region $REGION \
    --load-balancer-arn "$NLB_ARN" \
    --protocol TCP \
    --port "$LB_PORT" \
    --default-actions Type=forward,TargetGroupArn="$TG_ARN"
echo "   > Listener creado en TCP:$LB_PORT."

# ==============================================================================
#                              VERIFICACIÓN Y DESCRIPCIÓN FINAL
# ==============================================================================

echo "ℹ️ Consultando el DNS Name y Estado del Load Balancer..."

# 5. Describir Load Balancers, mostrando el DNSName y el State.Code
aws elbv2 describe-load-balancers \
    --region $REGION \
    --load-balancer-arns "$NLB_ARN" \
    --query 'LoadBalancers[0].[DNSName,State.Code]' \
    --output table

echo ""
# 6. Describir Load Balancers, extrayendo solo el DNSName
echo "🌐 DNS Name del Load Balancer:"
aws elbv2 describe-load-balancers \
    --region $REGION \
    --names "$LB_NAME" \
    --query 'LoadBalancers[0].DNSName' \
    --output text

echo ""
echo "✅ Proceso de configuración y verificación de NLB completado."