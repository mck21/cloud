# Guía T5: Mantenimiento de Bases de Datos Relacionales

## 1. Ventana de Mantenimiento

### 📋 Concepto
- Período semanal donde AWS puede aplicar actualizaciones
- Incluye: parches de seguridad, actualizaciones de motor, cambios de sistema
- Puede causar downtime o degradación del rendimiento
- Duración típica: 30 minutos, pero puede variar
- Se puede configurar para minimizar impacto en producción

---

### 📋 Paso 1: Crear RDS y Configurar Ventana de Mantenimiento

1. **Crear RDS con ventana personalizada**
   - Ir a RDS > Databases > "Create database"
   - Engine: **MySQL**
   - DB instance identifier: `rds-ventana-mantenimiento`
   - Master username: `admin`
   - Master password: Crear contraseña
   - Instance class: **db.t3.micro**
   - Storage: **20 GiB**
   - Public access: **YES**

2. **Configurar ventana de mantenimiento**
   - En "Additional configuration" (al final):
   - Database options > Maintenance:
     - **Enable auto minor version upgrade**: ☑ Activar (recomendado)
     - Maintenance window:
       - **Select window** (personalizada)
       - Day: **Sunday** (domingo - menos tráfico)
       - Start time: **03:00 UTC**
       - Duration: **0.5 hours** (30 minutos)
   - Clic en **Create database**

---

### 📋 Paso 2: Verificar y Modificar Ventana de Mantenimiento

1. **Ver ventana actual**
   - RDS > Databases > `rds-ventana-mantenimiento`
   - Pestaña "Maintenance & backups"
   - Ver:
     - Maintenance window: "sun:03:00-sun:03:30"
     - Auto minor version upgrade: Enabled
     - Pending maintenance: Ver si hay actualizaciones pendientes

2. **Modificar ventana de mantenimiento**
   - Seleccionar la instancia
   - Clic en **Modify**
   - Scroll hasta "Maintenance"
   - Cambiar ventana:
     - Day: **Saturday**
     - Start time: **04:00 UTC**
     - Duration: **1 hour**
   - Apply: **Apply immediately** o **During the next scheduled maintenance window**
   - Clic en **Continue** > **Modify DB instance**

---

### 📋 Paso 3: Gestionar Actualizaciones Pendientes

1. **Ver actualizaciones disponibles**
   - En "Maintenance & backups"
   - Si hay actualizaciones pendientes verás:
     - "Action required" o "Available"
     - Tipo de actualización (OS, DB engine, etc.)
     - Fecha programada

2. **Aplicar actualización inmediatamente**
   - Actions > **Upgrade now**
   - O esperar a la ventana de mantenimiento

3. **Posponer actualización**
   - Actions > **Defer upgrade**
   - Seleccionar nueva fecha
   - **Nota**: Actualizaciones de seguridad críticas pueden ser forzadas

---

### 📋 Paso 4: Mejores Prácticas de Ventana de Mantenimiento

**Recomendaciones:**
- ✅ Configurar en horarios de bajo tráfico (madrugada, fin de semana)
- ✅ Habilitar auto minor version upgrade (parches de seguridad)
- ✅ Probar actualizaciones primero en entorno dev/test
- ✅ Usar Multi-AZ para minimizar downtime
- ✅ Monitorear CloudWatch durante la ventana

**Ejemplo de configuración por tipo de aplicación:**
```
Aplicación 24/7 global: Domingo 04:00 UTC (madrugada tiempo local)
Aplicación B2B: Sábado 22:00 UTC
Aplicación regional: Según zona horaria del cliente
```

---

## 2. Implementación Blue/Green Deployment

### 📋 Concepto
- Estrategia de despliegue sin downtime
- **Blue** (azul): Entorno actual en producción
- **Green** (verde): Nuevo entorno con cambios/actualizaciones
- Cambio instantáneo cuando green está listo
- Rollback rápido si hay problemas
- Disponible para RDS MySQL, MariaDB, PostgreSQL

---

### 📋 Paso 1: Crear RDS Blue (Producción Actual)

1. **Crear RDS Blue**
   - DB instance identifier: `rds-blue-production`
   - Engine: **MySQL 8.0.35** (versión actual)
   - Instance class: **db.t3.small**
   - Storage: **20 GiB**
   - Multi-AZ: **YES** (recomendado para producción)
   - Public access: **YES** (para pruebas)
   - Initial database: `bluedb`
   - Backup retention: **7 days**
   - Clic en **Create database**

2. **Poblar con datos de "producción"**
   ```bash
   mysql -h rds-blue-production.xxxxx.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   CREATE DATABASE bluedb;
   USE bluedb;
   
   CREATE TABLE clientes (
       id INT PRIMARY KEY AUTO_INCREMENT,
       nombre VARCHAR(100),
       email VARCHAR(100),
       fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   
   INSERT INTO clientes (nombre, email) VALUES 
   ('Cliente 1', 'cliente1@example.com'),
   ('Cliente 2', 'cliente2@example.com'),
   ('Cliente 3', 'cliente3@example.com'),
   ('Cliente 4', 'cliente4@example.com'),
   ('Cliente 5', 'cliente5@example.com');
   
   CREATE TABLE productos (
       id INT PRIMARY KEY AUTO_INCREMENT,
       nombre VARCHAR(100),
       precio DECIMAL(10,2)
   );
   
   INSERT INTO productos (nombre, precio) VALUES 
   ('Producto A', 99.99),
   ('Producto B', 149.99),
   ('Producto C', 199.99);
   
   SELECT * FROM clientes;
   SELECT * FROM productos;
   ```

3. **Anotar endpoint Blue**
   - Copiar: `rds-blue-production.xxxxx.us-east-1.rds.amazonaws.com`

---

### 📋 Paso 2: Crear Blue/Green Deployment

1. **Iniciar Blue/Green deployment**
   - RDS > Databases > Seleccionar `rds-blue-production`
   - Actions > **Create Blue/Green Deployment**

2. **Configurar el deployment**
   - Blue/Green Deployment identifier: `bluegreen-upgrade-mysql`
   - DB engine version target:
     - **Specify a DB engine version**: MySQL 8.0.39 (versión más nueva)
     - Esto creará el entorno Green con la nueva versión
   - DB parameter group: default o personalizado
   - Allocate storage for the green environment: Dejar por defecto

3. **Configuración del entorno Green**
   - Green DB instance identifier suffix: `-green-1`
   - El nombre final será: `rds-blue-production-green-1`

4. **Crear el deployment**
   - Clic en **Create Blue/Green Deployment**
   - Esperar ~15-30 minutos

---

### 📋 Paso 3: Verificar Entorno Green

1. **Ver el deployment**
   - RDS > Blue/Green Deployments
   - Ver el deployment `bluegreen-upgrade-mysql`
   - Estado: Creating → Available

2. **Verificar entornos**
   - **Blue environment**: 
     - `rds-blue-production` (MySQL 8.0.35)
   - **Green environment**: 
     - `rds-blue-production-green-1` (MySQL 8.0.39)
     - Tiene los mismos datos que Blue (replicados)

3. **Conectar al entorno Green**
   ```bash
   # Obtener endpoint del Green desde la consola
   mysql -h rds-blue-production-green-1.xxxxx.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   -- Verificar versión
   SELECT VERSION();
   -- Debe mostrar 8.0.39
   
   -- Verificar datos
   USE bluedb;
   SELECT * FROM clientes;
   SELECT * FROM productos;
   -- Los datos deben estar sincronizados
   ```

---

### 📋 Paso 4: Probar Cambios en Green (Opcional)

1. **Hacer cambios solo en Green**
   - Probar migraciones
   - Probar nuevas queries
   - Verificar compatibilidad de aplicación

2. **Ejemplo de test**
   ```sql
   -- En Green únicamente
   USE bluedb;
   
   -- Probar nueva funcionalidad de MySQL 8.0.39
   CREATE TABLE test_green (
       id INT PRIMARY KEY,
       datos JSON
   );
   
   INSERT INTO test_green VALUES (1, '{"version": "green", "test": true}');
   SELECT * FROM test_green;
   ```

---

### 📋 Paso 5: Realizar el Switchover (Blue → Green)

1. **Preparar el switchover**
   - **IMPORTANTE**: Asegurar que la aplicación puede manejar un breve downtime
   - Notificar a usuarios si es necesario
   - Tener plan de rollback preparado

2. **Ejecutar switchover**
   - RDS > Blue/Green Deployments
   - Seleccionar `bluegreen-upgrade-mysql`
   - Clic en **Switch over**

3. **Configurar timeout**
   - Switchover timeout: **300 seconds** (5 minutos)
     - Tiempo máximo para esperar que las transacciones activas terminen
     - Si se excede, el switchover se cancela
   - Clic en **Switch over**

4. **Observar el proceso**
   - Estados: Switching → Available
   - Duración típica: 1-2 minutos
   - Durante el switchover:
     - Las escrituras se pausan brevemente
     - Las conexiones existentes pueden fallar
     - Nuevas conexiones se redirigen automáticamente

---

### 📋 Paso 6: Verificar Después del Switchover

1. **Verificar cambio de roles**
   - **Nuevo Blue (antes Green)**: 
     - `rds-blue-production` ahora apunta a MySQL 8.0.39
     - Este es ahora el entorno de producción
   - **Nuevo Green (antes Blue)**: 
     - `rds-blue-production-green-1` tiene MySQL 8.0.35
     - Este es ahora el entorno de respaldo

2. **Conectar al nuevo Blue (producción)**
   ```bash
   # MISMO endpoint que antes
   mysql -h rds-blue-production.xxxxx.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   -- Verificar versión (ahora debe ser 8.0.39)
   SELECT VERSION();
   
   -- Verificar datos
   USE bluedb;
   SELECT * FROM clientes;
   SELECT * FROM productos;
   ```

3. **Características del switchover**
   - ✅ El endpoint NO cambia (transparente para la aplicación)
   - ✅ Los datos están sincronizados
   - ✅ Downtime mínimo (1-2 minutos)
   - ✅ El antiguo Blue sigue disponible como Green

---

### 📋 Paso 7: Rollback (si es necesario)

1. **Si hay problemas en producción**
   - RDS > Blue/Green Deployments
   - Seleccionar el deployment
   - Clic en **Switch over** de nuevo
   - Esto vuelve a cambiar los roles

2. **Resultado del rollback**
   - Vuelves a la versión anterior (8.0.35)
   - Mismo endpoint, sin cambios en aplicación
   - Downtime mínimo de nuevo

---

### 📋 Paso 8: Eliminar Entorno Green (Cleanup)

1. **Cuando todo está OK en producción**
   - RDS > Blue/Green Deployments
   - Seleccionar `bluegreen-upgrade-mysql`
   - Clic en **Delete**

2. **Opciones de eliminación**
   - Se puede:
     - Eliminar el deployment completo
     - Mantener el entorno Green como instancia independiente
     - Crear snapshot final del Green

3. **Eliminar instancia Green**
   - RDS > Databases
   - Seleccionar `rds-blue-production-green-1`
   - Actions > Delete
   - Desmarcar snapshots
   - Confirmar eliminación

---

### 📊 Ventajas de Blue/Green Deployment

| Ventaja | Descripción |
|---------|-------------|
| **Zero downtime** | Downtime mínimo (1-2 min vs 30+ min) |
| **Rollback rápido** | Volver atrás en minutos si hay problemas |
| **Testing seguro** | Probar en Green sin afectar Blue |
| **Sin cambios de endpoint** | Aplicación no necesita cambios |
| **Sincronización automática** | Datos replicados en tiempo real |

---

## 3. Grupos de Parámetros

### 📋 Concepto
- Configuración de base de datos (equivalente a my.cnf en MySQL)
- Controlan comportamiento del motor de BD
- Tipos:
  - **DB Parameter Group**: Para instancias individuales
  - **DB Cluster Parameter Group**: Para clusters Aurora
- Algunos parámetros requieren reinicio, otros se aplican dinámicamente

---

### 📋 Paso 1: Ver Parameter Groups por Defecto

1. **Acceder a Parameter Groups**
   - RDS > Parameter groups
   - Ver los grupos por defecto:
     - `default.mysql8.0`
     - `default.postgres14`
     - etc.

2. **Ver parámetros de un grupo**
   - Clic en `default.mysql8.0`
   - Ver lista de parámetros configurables:
     - `max_connections`
     - `innodb_buffer_pool_size`
     - `slow_query_log`
     - `log_bin_trust_function_creators`
     - etc.

---

### 📋 Paso 2: Crear Parameter Group Personalizado

1. **Crear nuevo Parameter Group**
   - RDS > Parameter groups
   - Clic en **Create parameter group**

2. **Configurar el grupo**
   - Parameter group family: **mysql8.0**
   - Type: **DB Parameter Group**
   - Group name: `mysql-custom-params`
   - Description: `Configuración personalizada para MySQL`
   - Clic en **Create**

---

### 📋 Paso 3: Modificar Parámetros

1. **Editar el parameter group**
   - Clic en `mysql-custom-params`
   - Clic en **Edit**

2. **Modificar parámetros comunes**

   **Aumentar conexiones máximas:**
   - Buscar: `max_connections`
   - Cambiar de `{DBInstanceClassMemory/12582880}` a: `200`
   - **Requiere reinicio**: ❌ No (dinámico)

   **Habilitar slow query log:**
   - Buscar: `slow_query_log`
   - Cambiar a: `1` (habilitado)
   - **Requiere reinicio**: ❌ No

   - Buscar: `long_query_time`
   - Cambiar a: `2` (queries > 2 segundos)
   - **Requiere reinicio**: ❌ No

   **Configurar buffer pool de InnoDB:**
   - Buscar: `innodb_buffer_pool_size`
   - Cambiar de `{DBInstanceClassMemory*3/4}` a: `{DBInstanceClassMemory/2}`
   - **Requiere reinicio**: ✅ Sí

   **Habilitar binary logging:**
   - Buscar: `log_bin_trust_function_creators`
   - Cambiar a: `1`
   - **Requiere reinicio**: ❌ No

   **Configurar timezone:**
   - Buscar: `time_zone`
   - Cambiar a: `Europe/Madrid`
   - **Requiere reinicio**: ❌ No

3. **Guardar cambios**
   - Clic en **Save changes**

---

### 📋 Paso 4: Aplicar Parameter Group a RDS

1. **Crear RDS nueva con parameter group personalizado**
   - DB instance identifier: `rds-custom-params`
   - Engine: **MySQL 8.0**
   - Instance class: **db.t3.micro**
   - En "Additional configuration":
     - DB parameter group: **mysql-custom-params**
   - Clic en **Create database**

2. **O modificar RDS existente**
   - Seleccionar instancia existente
   - Clic en **Modify**
   - Database options:
     - DB parameter group: Cambiar a `mysql-custom-params`
   - Apply: **Immediately** o **During next maintenance window**
   - Clic en **Continue** > **Modify DB instance**

3. **Reiniciar si es necesario**
   - Si cambiaste parámetros que requieren reinicio:
   - Actions > **Reboot**
   - Confirmar

---

### 📋 Paso 5: Verificar Parámetros Aplicados

1. **Conectar a RDS**
   ```bash
   mysql -h rds-custom-params.xxxxx.rds.amazonaws.com -u admin -p
   ```

2. **Verificar parámetros**
   ```sql
   -- Ver conexiones máximas
   SHOW VARIABLES LIKE 'max_connections';
   -- Debe mostrar: 200
   
   -- Ver slow query log
   SHOW VARIABLES LIKE 'slow_query_log';
   -- Debe mostrar: ON
   
   SHOW VARIABLES LIKE 'long_query_time';
   -- Debe mostrar: 2.000000
   
   -- Ver timezone
   SHOW VARIABLES LIKE 'time_zone';
   -- Debe mostrar: Europe/Madrid
   
   -- Ver buffer pool
   SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
   
   -- Ver binary logging
   SHOW VARIABLES LIKE 'log_bin_trust_function_creators';
   -- Debe mostrar: ON
   ```

---

### 📋 Paso 6: Comparar Parameter Groups

1. **Comparar dos parameter groups**
   - RDS > Parameter groups
   - Seleccionar `mysql-custom-params`
   - Actions > **Compare**
   - Select target: `default.mysql8.0`
   - Ver diferencias resaltadas

2. **Exportar parámetros**
   - Útil para documentación o migración
   - Se pueden exportar a JSON/CSV

---

### 📋 Paso 7: Parámetros Comunes y Recomendados

**Para Rendimiento:**
```
max_connections = Según carga esperada
innodb_buffer_pool_size = 50-75% de RAM (requiere reinicio)
innodb_log_file_size = 256M o mayor
query_cache_size = 0 (deshabilitado en MySQL 8.0)
```

**Para Logging y Debugging:**
```
slow_query_log = 1
long_query_time = 2
general_log = 0 (solo para debugging temporal)
log_queries_not_using_indexes = 1
```

**Para Replicación:**
```
log_bin_trust_function_creators = 1
binlog_format = ROW
```

**Para Seguridad:**
```
require_secure_transport = 1 (fuerza SSL)
```

---

### 📋 Paso 8: Parameter Groups para Aurora

1. **Crear Cluster Parameter Group**
   - RDS > Parameter groups > Create
   - Parameter group family: **aurora-mysql8.0**
   - Type: **DB Cluster Parameter Group**
   - Group name: `aurora-cluster-custom`
   - Clic en **Create**

2. **Diferencia con DB Parameter Group**
   - **Cluster Parameter Group**: Afecta a todo el cluster
   - **DB Parameter Group**: Afecta a instancias individuales
   - Aurora requiere AMBOS tipos

3. **Aplicar a cluster Aurora**
   - Al crear cluster, seleccionar:
     - DB cluster parameter group: `aurora-cluster-custom`
     - DB parameter group: `default.aurora-mysql8.0` o personalizado

---

### 📊 Tipos de Parámetros

| Tipo | Aplicación | Requiere Reinicio | Ejemplo |
|------|-----------|-------------------|---------|
| **Estático** | Al reiniciar | ✅ Sí | `innodb_buffer_pool_size` |
| **Dinámico** | Inmediato | ❌ No | `max_connections`, `slow_query_log` |
| **Cluster (Aurora)** | Al cluster | Depende | `binlog_format` |

---

## 🧹 Limpieza de Recursos

### Ventana de Mantenimiento:
```
1. No requiere limpieza específica
2. Eliminar RDS si ya no se necesita
```

### Blue/Green Deployment:
```
1. RDS > Blue/Green Deployments > Seleccionar > Delete
2. RDS > Databases > Eliminar instancias Green residuales
```

### Parameter Groups:
```
1. Primero: Desvincular de todas las instancias RDS
2. RDS > Parameter groups > Seleccionar > Delete
3. No se pueden eliminar parameter groups por defecto
```

---

## ⚠️ Notas Importantes

### Ventana de Mantenimiento:
- ✅ Siempre configurar en horarios de bajo tráfico
- ✅ Combinar con Multi-AZ para reducir downtime
- ⚠️ Actualizaciones major version NO se aplican automáticamente
- 💡 Probar primero en dev/test antes de producción

### Blue/Green Deployment:
- ✅ Ideal para actualizaciones de versión sin downtime
- ✅ Requiere mismo tipo de instancia y almacenamiento
- ⚠️ Green consume recursos adicionales (costo doble temporal)
- ⚠️ Solo para MySQL, MariaDB, PostgreSQL (NO Aurora)
- 💡 Mantener Green activo hasta confirmar que todo funciona
- ⏱️ Switchover típico: 1-2 minutos de downtime

### Parameter Groups:
- ✅ Crear copias de los por defecto antes de modificar
- ✅ Documentar todos los cambios realizados
- ⚠️ Parámetros estáticos requieren reinicio (downtime)
- ⚠️ Cambios incorrectos pueden degradar rendimiento
- 💡 Usar Compare para ver diferencias
- 💡 Aurora necesita cluster + instance parameter groups
- 🔧 Testear cambios en dev antes de aplicar en producción

### Costos:
- Ventana de mantenimiento: Sin costo adicional
- Blue/Green: Costo doble mientras ambos entornos están activos
- Parameter Groups: Sin costo adicional