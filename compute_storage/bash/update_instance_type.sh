#!/bin/bash

# Script para cambiar el tipo de instancia EC2
# Uso: ./update_instance_type.sh <instance-id> <new-instance-type>

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar errores
error_exit() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

# Función para mostrar información
info_msg() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Función para mostrar éxito
success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Función para mostrar advertencia
warning_msg() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Validar parámetros
if [ $# -ne 2 ]; then
    error_exit "Parámetros incorrectos. Uso: $0 <instance-id> <new-instance-type>"
fi

INSTANCE_ID="$1"
NEW_INSTANCE_TYPE="$2"

info_msg "Iniciando proceso de cambio de tipo de instancia..."
info_msg "ID de instancia: $INSTANCE_ID"
info_msg "Nuevo tipo: $NEW_INSTANCE_TYPE"

# 2. Verificar que jq esté instalado (herramienta nativa para leer correctamente JSON en shell)
if ! command -v jq >/dev/null 2>&1; then
    error_exit "El comando 'jq' es necesario pero no está instalado. Instálalo con: sudo apt install jq -y"
fi

# 3. Verificar que la instancia existe
info_msg "Verificando que la instancia existe..."
INSTANCE_INFO=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" 2>&1)

if [ $? -ne 0 ]; then
    error_exit "La instancia con ID '$INSTANCE_ID' no existe o no se puede acceder."
fi

# 4. Obtener información actual de la instancia
CURRENT_TYPE=$(echo "$INSTANCE_INFO" | jq -r '.Reservations[0].Instances[0].InstanceType')
CURRENT_STATE=$(echo "$INSTANCE_INFO" | jq -r '.Reservations[0].Instances[0].State.Name')

success_msg "Instancia encontrada"
info_msg "Tipo actual: $CURRENT_TYPE"
info_msg "Estado actual: $CURRENT_STATE"

# 5. Comprobar que el tipo no sea el mismo
if [ "$CURRENT_TYPE" = "$NEW_INSTANCE_TYPE" ]; then
    error_exit "El nuevo tipo '$NEW_INSTANCE_TYPE' es igual al tipo actual '$CURRENT_TYPE'. No es necesario realizar cambios."
fi

# 6. Advertencia y confirmación del usuario
warning_msg "Se procederá a detener la instancia para cambiar su tipo."
echo -e "${YELLOW}¿Deseas continuar? (s/n):${NC}"
read -r CONFIRM

if [ "$CONFIRM" != "s" ] && [ "$CONFIRM" != "S" ]; then
    info_msg "Proceso abortado por el usuario."
    exit 0
fi

# 7. Detener la instancia si está en ejecución
if [ "$CURRENT_STATE" = "running" ]; then
    info_msg "Deteniendo la instancia..."
    aws ec2 stop-instances --instance-ids "$INSTANCE_ID" > /dev/null || error_exit "No se pudo detener la instancia."
else
    warning_msg "La instancia no está en ejecución (estado actual: $CURRENT_STATE)."
fi

# Esperar a que la instancia esté completamente detenida
info_msg "Esperando a que la instancia se detenga completamente..."
aws ec2 wait instance-stopped --instance-ids "$INSTANCE_ID" || error_exit "La instancia no se detuvo correctamente."
success_msg "Instancia detenida correctamente."

# 8. Cambiar el tipo de instancia
info_msg "Cambiando el tipo de instancia a '$NEW_INSTANCE_TYPE'..."
aws ec2 modify-instance-attribute --instance-id "$INSTANCE_ID" --instance-type "{\"Value\": \"$NEW_INSTANCE_TYPE\"}" || error_exit "No se pudo cambiar el tipo de instancia."
success_msg "Tipo de instancia cambiado correctamente."

# 9. Iniciar la instancia
info_msg "Iniciando la instancia..."
aws ec2 start-instances --instance-ids "$INSTANCE_ID" > /dev/null || error_exit "No se pudo iniciar la instancia."

info_msg "Esperando a que la instancia inicie..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" || error_exit "La instancia no inició correctamente."
success_msg "Instancia iniciada correctamente."

# 10. Verificación final
FINAL_INFO=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID")
FINAL_TYPE=$(echo "$FINAL_INFO" | jq -r '.Reservations[0].Instances[0].InstanceType')
FINAL_STATE=$(echo "$FINAL_INFO" | jq -r '.Reservations[0].Instances[0].State.Name')

echo ""
success_msg "========================================="
success_msg "¡Proceso completado exitosamente!"
success_msg "========================================="
info_msg "ID de instancia: $INSTANCE_ID"
info_msg "Tipo anterior: $CURRENT_TYPE"
info_msg "Tipo nuevo: $FINAL_TYPE"
info_msg "Estado final: $FINAL_STATE"
success_msg "========================================="
