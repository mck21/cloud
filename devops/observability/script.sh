# Definimos la hora actual (end) y la hora de hace una hora (start) en formato UTC
END_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
START_TIME=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)

# 1. Ejecutamos el comando curl.
# 2. El output JSON se pasa a 'jq'
# 3. 'jq' extrae los valores de tiempo (columna 1) y de CPU (columna 2),
#    los formatea como CSV (separados por comas)
# 4. Finalmente, la salida CSV se redirige al archivo deseado.
curl -G "http://3.82.198.154:9090/api/v1/query_range" \
    --data-urlencode 'query=avg(rate(node_cpu_seconds_total{mode!="idle"}[5m])) * 100' \
    --data-urlencode "start=$START_TIME" \
    --data-urlencode "end=$END_TIME" \
    --data-urlencode 'step=60' \
| jq -r '.data.result[0].values[] | .[0] as $timestamp | ([$timestamp, .[1]]) | @csv' \
> cpu_usage_prometheus.csv