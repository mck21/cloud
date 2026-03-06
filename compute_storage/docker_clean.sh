#!/bin/bash

echo "██████╗  ██████╗  ██████╗██╗  ██╗███████╗██████╗ "
echo "██╔══██╗██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗"
echo "██║  ██║██║   ██║██║     █████╔╝ █████╗  ██████╔╝"
echo "██║  ██║██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗"
echo "██████╔╝╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║"
echo "╚═════╝  ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝"
echo ""
echo "        🐳 LIMPIEZA TOTAL DE RECURSOS 🐳"
echo "=================================================="
echo ""

echo "🧹 Limpiando TODOS los recursos de Docker..."

echo "▶ Parando todos los contenedores en ejecución..."
docker stop $(docker ps -aq) 2>/dev/null || echo "  No hay contenedores activos"

echo "▶ Eliminando todos los contenedores..."
docker rm -f $(docker ps -aq) 2>/dev/null || echo "  No hay contenedores"

echo "▶ Eliminando todas las imágenes..."
docker rmi -f $(docker images -aq) 2>/dev/null || echo "  No hay imágenes"

echo "▶ Eliminando todos los volúmenes..."
docker volume rm $(docker volume ls -q) 2>/dev/null || echo "  No hay volúmenes"

echo "▶ Eliminando todas las networks (excepto las del sistema)..."
docker network rm $(docker network ls | grep -v "bridge\|host\|none" | awk 'NR>1 {print $1}') 2>/dev/n>

echo "▶ Limpiando caché del sistema (build cache, dangling, etc.)..."
docker system prune -a -f --volumes

echo ""
echo "✅ Limpieza completada."

