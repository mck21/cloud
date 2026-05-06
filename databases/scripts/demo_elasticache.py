import pymysql
import memcache
import time

# Configuración
RDS_HOST = "db-mck21.csmikdkirvsq.us-east-1.rds.amazonaws.com"
RDS_USER = "admin"
RDS_PASSWORD = "12345678"
RDS_DB = "db-mck21"

ELASTICACHE_HOST = "cache-mck21-jjnst5.serverless.use1.cache.amazonaws.com:11211"
ELASTICACHE_PORT = 11211

# Conexiones
db = pymysql.connect(host=RDS_HOST, user=RDS_USER, password=RDS_PASSWORD, database=RDS_DB)
cache = memcache.Client([f"{ELASTICACHE_HOST}:{ELASTICACHE_PORT}"], debug=0)

def get_product_count():
    # Intenta obtener el valor del caché
    cached = cache.get("product_count")
    if cached:
        print(" Resultado desde CACHE:", cached)
        return cached
    else:
        # Si no está en caché, consulta MySQL
        print(" Consultando MySQL...")
        with db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM productos;")
            result = cursor.fetchone()[0]
            cache.set("product_count", result, time=30)  # guarda por 30 segundos
            return result

# Ejecutar la prueba
start = time.time()
print("Productos totales:", get_product_count())
print("Tiempo:", round(time.time() - start, 3), "segundos")

# Segunda llamada (debería venir del caché)
start = time.time()
print("Productos totales:", get_product_count())
print("Tiempo:", round(time.time() - start, 3), "segundos")
