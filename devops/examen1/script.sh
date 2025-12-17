#!/bin/bash

# Verificar que se pasó una IP como argumento
if [ -z "$1" ]; then
  echo "Uso: $0 <IP>"
  exit 1
fi

IP="$1"
COUNT=250  # Aumentado para poder probar la alarma de >200

echo "Haciendo $COUNT pings a $IP..."
ping -c $COUNT -i 0.01 "$IP"  # intervalo de 0.01 segundos entre pings