# Guía T4: Recuperación ante Desastres

## 1. RDS Proxy

### 📋 Concepto
- Proxy entre aplicación y base de datos
- Pool de conexiones reutilizables
- Reduce overhead de abrir/cerrar conexiones
- Failover más rápido y transparente
- Compatible con Lambda y aplicaciones serverless

---

### 📋 Paso 1: Crear RDS para usar con Proxy

1. **Crear RDS**
   - Ir a RDS > Databases > "Create database"
   - Engine: **MySQL** o **PostgreSQL**
   - DB instance identifier: `rds-con-proxy`
   - Master username: `admin`
   - Master password: Crear contraseña segura (guardarla)
   - Instance class: **db.t3.micro**
   - Storage: **20 GiB**
   - **IMPORTANTE** en Connectivity:
     - Public access: **NO** (el proxy sí puede ser público)
     - VPC: Usar VPC por defecto
   - Initial database: `proxydb`
   - Clic en **Create database**

---

### 📋 Paso 2: Guardar Credenciales en Secrets Manager

1. **Crear Secret**
   - Ir a **AWS Secrets Manager**
   - Clic en "Store a new secret"
   - Secret type: **Credentials for RDS database**
   - User name: `admin`
   - Password: La contraseña del RDS
   - Database: Seleccionar `rds-con-proxy`
   - Clic en **Next**

2. **Configurar el secret**
   - Secret name: `rds-proxy-credentials`
   - Description: `Credenciales para RDS Proxy`
   - Clic en **Next**

3. **Configuración de rotación**
   - Disable automatic rotation (para pruebas)
   - Clic en **Next**

4. **Revisar y crear**
   - Clic en **Store**
   - **Copiar el ARN del secret** (lo necesitaremos)

---

### 📋 Paso 3: Crear RDS Proxy

1. **Crear el Proxy**
   - Ir a RDS > Proxies
   - Clic en **Create proxy**

2. **Configuración del proxy**
   - Proxy identifier: `my-rds-proxy`
   - Engine compatibility: **MySQL** (debe coincidir con tu RDS)
   - Target group configuration:
     - Database: Seleccionar `rds-con-proxy`
     - Connection pool maximum connections: **100%** (usar máximo disponible)
   
3. **Connectivity**
   - Secrets Manager secrets: 
     - Clic en **Add secret**
     - Seleccionar `rds-proxy-credentials`
   - IAM role: 
     - **Create a new IAM role** (se crea automáticamente)
     - Role name: `RDSProxyRole-my-rds-proxy`
   - IAM authentication: **Disabled** (para simplificar)
   - Subnets: Seleccionar al menos 2 subnets de diferentes AZs
   - VPC security groups: 
     - Crear nuevo o usar existente
     - Debe permitir conexiones desde tu aplicación/EC2

4. **Configuración adicional**
   - Connection borrow timeout: **120 seconds**
   - Initialization query: Dejar vacío
   - Require Transport Layer Security: **No** (para pruebas)
   - Idle client connection timeout: **1800 seconds** (30 min)

5. **Crear el proxy**
   - Clic en **Create proxy**
   - Esperar ~5 minutos hasta que esté "Available"

---

### 📋 Paso 4: Configurar Security Groups

1. **Security Group del Proxy**
   - Ir a EC2 > Security Groups
   - Buscar el SG del proxy (creado automáticamente)
   - Inbound rules > Edit inbound rules
   - Add rule:
     - Type: **MySQL/Aurora**
     - Port: **3306**
     - Source: 
       - Si conectas desde EC2: Security Group de la EC2
       - Si conectas desde tu PC: **My IP** o **Anywhere** (solo pruebas)

2. **Security Group del RDS**
   - Buscar el SG del RDS
   - Inbound rules > Edit inbound rules
   - Add rule:
     - Type: **MySQL/Aurora**
     - Port: **3306**
     - Source: **Security Group del Proxy**

---

### 📋 Paso 5: Conectar a través del Proxy

1. **Obtener endpoint del proxy**
   - RDS > Proxies > Seleccionar `my-rds-proxy`
   - Copiar el **Proxy endpoint**: `my-rds-proxy.proxy-xxxxx.us-east-1.rds.amazonaws.com`

2. **Conectar desde terminal**
   ```bash
   mysql -h my-rds-proxy.proxy-xxxxx.us-east-1.rds.amazonaws.com -P 3306 -u admin -p
   ```

3. **Verificar conexión**
   ```sql
   SHOW DATABASES;
   USE proxydb;
   CREATE TABLE test_proxy (id INT, mensaje VARCHAR(100));
   INSERT INTO test_proxy VALUES (1, 'Conectado via Proxy');
   SELECT * FROM test_proxy;
   ```

---

### 📋 Paso 6: Probar Beneficios del Proxy

1. **Test de múltiples conexiones simultáneas**
   - El proxy reutiliza conexiones
   - Reduce la carga en la BD
   - Mejora el rendimiento con muchos clientes

2. **Simular failover**
   - Si usas Multi-AZ, el proxy maneja el failover transparentemente
   - La aplicación no necesita reconectar
   - El endpoint del proxy no cambia

---

## 2. Redo Logs (Logs de Transacciones)

### 📋 Concepto
- Archivos de log que registran todas las transacciones
- Permiten recuperación point-in-time (PITR)
- Almacenados automáticamente en RDS
- Se usan para restaurar BD a un momento específico

---

### 📋 Paso 1: Verificar Logs en RDS

1. **Ver configuración de logs**
   - RDS > Databases > Seleccionar tu instancia
   - Pestaña "Configuration"
   - Ver "Backup retention period": Debe ser > 0 días

2. **Logs disponibles**
   - Pestaña "Logs & events"
   - Ver logs de:
     - Error log
     - Slow query log
     - General log

3. **Habilitar logs adicionales** (opcional)
   - Modify > Additional configuration
   - Log exports:
     - ☑ Error log
     - ☑ Slow query log
     - ☑ General log (genera mucho tráfico)

---

### 📋 Paso 2: Descargar y Ver Logs

1. **Desde la consola**
   - RDS > Databases > Tu instancia
   - Pestaña "Logs & events"
   - Seleccionar un log (ej: error/mysql-error.log)
   - Clic en **Download** o **View**

2. **Desde CLI** (opcional)
   ```bash
   # Listar logs disponibles
   aws rds describe-db-log-files --db-instance-identifier rds-con-proxy
   
   # Descargar un log específico
   aws rds download-db-log-file-portion \
     --db-instance-identifier rds-con-proxy \
     --log-file-name error/mysql-error.log \
     --output text
   ```

---

## 3. AWS Backup y Otras Copias

### 📋 Concepto de Backups en RDS
- **Snapshots automatizados**: Diarios, retención configurable
- **Snapshots manuales**: Bajo demanda, se mantienen hasta que los elimines
- **AWS Backup**: Servicio centralizado para gestión de backups

---

### 🔄 Opción A: Snapshots Automáticos

### 📋 Paso 1: Configurar Backups Automáticos

1. **Crear RDS con backups automáticos**
   - DB instance identifier: `rds-backup-auto`
   - Engine: **MySQL**
   - Instance class: **db.t3.micro**
   - En "Additional configuration":
     - **Backup retention period**: **7 days**
     - **Backup window**: Select window o No preference
       - Start time: 03:00 UTC (ejemplo)
       - Duration: 1 hour
     - **Copy tags to snapshots**: Activar
   - Clic en **Create database**

2. **Verificar configuración de backup**
   - RDS > Databases > Seleccionar `rds-backup-auto`
   - Pestaña "Maintenance & backups"
   - Ver "Backup retention period": 7 days
   - Ver "Latest restorable time": Se actualiza cada 5 minutos

---

### 📋 Paso 2: Verificar Snapshots Automáticos

1. **Ver snapshots automáticos**
   - RDS > Automated backups
   - Ver tu instancia `rds-backup-auto`
   - Muestra el primer snapshot (creado tras ~24h)
   - **System snapshots**: Snapshots automáticos diarios
   - Se eliminan automáticamente después de 7 días

---

### 📸 Opción B: Snapshots Manuales

### 📋 Paso 1: Crear Snapshot Manual

1. **Crear datos de prueba primero**
   ```bash
   mysql -h rds-backup-auto.xxxxx.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   CREATE DATABASE backupdb;
   USE backupdb;
   CREATE TABLE datos_importantes (
       id INT PRIMARY KEY AUTO_INCREMENT,
       dato VARCHAR(200),
       fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   
   INSERT INTO datos_importantes (dato) VALUES 
   ('Dato antes del snapshot'),
   ('Dato crítico 1'),
   ('Dato crítico 2');
   
   SELECT * FROM datos_importantes;
   ```

2. **Crear snapshot manual**
   - RDS > Databases > Seleccionar `rds-backup-auto`
   - Actions > **Take snapshot**
   - Snapshot name: `snapshot-manual-antes-cambios`
   - Clic en **Take snapshot**

3. **Verificar snapshot**
   - RDS > Snapshots
   - Ver el snapshot en estado "Creating" → "Available"
   - Tiempo: ~5-10 minutos dependiendo del tamaño

---

### 📋 Paso 2: Hacer Cambios en la BD

1. **Simular cambios/errores**
   ```sql
   -- Conectar de nuevo
   USE backupdb;
   
   -- Agregar más datos
   INSERT INTO datos_importantes (dato) VALUES 
   ('Dato DESPUÉS del snapshot'),
   ('Cambio que queremos deshacer');
   
   -- Simular error: eliminar datos importantes
   DELETE FROM datos_importantes WHERE id <= 2;
   
   SELECT * FROM datos_importantes;
   -- Ahora faltan los primeros 2 registros
   ```

---

### 📋 Paso 3: Restaurar desde Snapshot

1. **Restaurar snapshot**
   - RDS > Snapshots
   - Seleccionar `snapshot-manual-antes-cambios`
   - Actions > **Restore snapshot**

2. **Configurar la restauración**
   - DB instance identifier: `rds-restaurada-desde-manual`
   - DB instance class: **db.t3.micro**
   - Storage type: Heredado
   - VPC: Default
   - Public access: **YES**
   - VPC security group: Mismo que el original
   - Database port: **3306**
   - Clic en **Restore DB instance**

3. **Esperar a que esté Available**

4. **Verificar datos restaurados**
   ```bash
   mysql -h rds-restaurada-desde-manual.xxxxx.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   USE backupdb;
   SELECT * FROM datos_importantes;
   -- Debería mostrar los 3 registros originales (antes del DELETE)
   ```

---

### 📋 Paso 4: Restauración Point-in-Time (PITR)

1. **Restaurar a un momento específico**
   - RDS > Databases > Seleccionar `rds-backup-auto`
   - Actions > **Restore to point in time**

2. **Seleccionar el momento**
   - **Latest restorable time**: Momento más reciente
   - o **Custom**: Seleccionar fecha y hora específica
   - Ejemplo: Restaurar a 2 horas antes
   - DB instance identifier: `rds-pitr-restaurada`
   - Resto de configuración similar
   - Clic en **Restore DB instance**

3. **Uso de PITR**
   - Útil para recuperar de errores específicos
   - Requiere que los backups automáticos estén habilitados
   - Puede restaurar hasta el minuto anterior

---

### ☁️ Opción C: AWS Backup (Centralizado)

### 📋 Paso 1: Crear Plan de Backup con AWS Backup

1. **Acceder a AWS Backup**
   - Buscar "AWS Backup" en servicios
   - Clic en "Backup plans"
   - Clic en **Create backup plan**

2. **Configurar el plan**
   - Start with: **Build a new plan**
   - Backup plan name: `plan-backup-rds-diario`
   
3. **Configurar regla de backup**
   - Backup rule name: `regla-diaria-rds`
   - Backup vault: **Default**
   - Backup frequency: **Daily**
   - Backup window:
     - Start time: **03:00 UTC**
     - Start within: **8 hours**
     - Complete within: **12 hours**
   - Lifecycle:
     - Transition to cold storage: **Never**
     - Retention period: **7 days**
   - Clic en **Create plan**

---

### 📋 Paso 2: Asignar Recursos al Plan

1. **Crear asignación de recursos**
   - En el plan creado, clic en **Assign resources**
   - Resource assignment name: `asignacion-rds-backup`
   - IAM role: **Default role** (se crea automáticamente)

2. **Seleccionar recursos**
   - Resource selection:
     - **Include specific resource types**
     - Resource type: **RDS - DB Instance**
   - Specific resources:
     - Seleccionar `rds-backup-auto` o usar tags

3. **Crear la asignación**
   - Clic en **Assign resources**

---

### 📋 Paso 3: Verificar Backups en AWS Backup

1. **Ver trabajos de backup**
   - AWS Backup > Jobs
   - Ver los backups programados y completados

2. **Ver puntos de recuperación**
   - AWS Backup > Backup vaults > Default
   - Ver los recovery points creados
   - Cada punto tiene:
     - Fecha/hora de creación
     - Tamaño
     - Estado
     - Fecha de expiración

---

### 📋 Paso 4: Restaurar desde AWS Backup

1. **Iniciar restauración**
   - AWS Backup > Backup vaults > Default
   - Seleccionar un recovery point
   - Clic en **Restore**

2. **Configurar restauración**
   - DB instance identifier: `rds-restaurada-aws-backup`
   - Instance class: **db.t3.micro**
   - VPC, subnet, security group: Configurar según necesidad
   - Clic en **Restore backup**

3. **Verificar restauración**
   - La instancia aparece en RDS > Databases
   - Conectar y verificar datos

---

### 📊 Comparación de Métodos de Backup

| Método | Automático | Retención | PITR | Costo | Centralizado |
|--------|-----------|-----------|------|-------|--------------|
| **Snapshots Auto RDS** | ✅ Sí | 1-35 días | ✅ Sí | Incluido | ❌ No |
| **Snapshots Manuales** | ❌ No | Indefinida | ❌ No | Por GB-mes | ❌ No |
| **AWS Backup** | ✅ Sí | Configurable | ✅ Sí | Separado | ✅ Sí |

---

## 4. Multi-AZ (Alta Disponibilidad)

### 📋 Concepto Multi-AZ
- Replica síncrona en otra zona de disponibilidad
- Failover automático en caso de fallo
- **NO es para lectura**: la réplica standby no sirve tráfico
- Tiempo de failover: 1-2 minutos
- Protege contra fallos de AZ, hardware, red

---

### 🏢 Opción A: Multi-AZ con 1 Instancia Standby

### 📋 Paso 1: Crear RDS Multi-AZ (1 Standby)

1. **Crear RDS**
   - DB instance identifier: `rds-multi-az-1-standby`
   - Engine: **MySQL**
   - Templates: **Production** (recomendado para Multi-AZ)
   - Instance class: **db.t3.small** (mínimo recomendado)
   - Storage: **20 GiB gp3**

2. **Configurar Multi-AZ**
   - Availability & durability:
     - **Multi-AZ DB instance** (opción tradicional)
     - Crea 1 instancia standby en otra AZ
   - VPC: Default
   - Public access: **YES** (para pruebas)
   - Backup retention: **7 days**
   - Initial database: `multiazdb`
   - Clic en **Create database**

3. **Esperar a que esté Available**
   - Tarda más que Single-AZ (~15-20 min)
   - Se crean 2 instancias en diferentes AZs

---

### 📋 Paso 2: Verificar Configuración Multi-AZ

1. **Ver configuración**
   - RDS > Databases > `rds-multi-az-1-standby`
   - Pestaña "Configuration":
     - Multi-AZ: **Yes**
     - Secondary zone: Ver la AZ donde está el standby

2. **Crear datos de prueba**
   ```bash
   mysql -h rds-multi-az-1-standby.xxxxx.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   CREATE DATABASE multiazdb;
   USE multiazdb;
   CREATE TABLE ha_test (
       id INT PRIMARY KEY AUTO_INCREMENT,
       mensaje VARCHAR(200),
       timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   
   INSERT INTO ha_test (mensaje) VALUES ('Dato en instancia primaria');
   SELECT * FROM ha_test;
   ```

---

### 📋 Paso 3: Probar Failover Manual

1. **Iniciar failover**
   - RDS > Databases > `rds-multi-az-1-standby`
   - Actions > **Reboot**
   - ☑ **Reboot with failover**
   - Clic en **Confirm**

2. **Observar el proceso**
   - Estado: Available → Failing-over → Available
   - Tiempo: ~1-2 minutos
   - Durante el failover:
     - Conexiones actuales se pierden
     - Nuevas conexiones fallan temporalmente
   - Después del failover:
     - El standby se convierte en primario
     - El antiguo primario se convierte en standby

3. **Verificar datos después del failover**
   ```bash
   # Reconectar (usando el mismo endpoint)
   mysql -h rds-multi-az-1-standby.xxxxx.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   USE multiazdb;
   SELECT * FROM ha_test;
   -- Los datos siguen ahí (replicación síncrona)
   
   INSERT INTO ha_test (mensaje) VALUES ('Dato después del failover');
   SELECT * FROM ha_test;
   ```

---

### 🏢 Opción B: Multi-AZ con Cluster (2 Readers Standby)

### 📋 Paso 1: Crear RDS Multi-AZ Cluster

1. **Crear RDS con Multi-AZ Cluster**
   - DB instance identifier: `rds-multi-az-cluster`
   - Engine: **MySQL** (8.0.28 o superior)
   - Templates: **Production**
   - Instance class: **db.r5.large** o superior (NO soporta t3/t4)

2. **Configurar Multi-AZ Cluster**
   - Availability & durability:
     - **Multi-AZ DB cluster** (nueva opción)
     - Crea 1 Writer + 2 Readers en 3 AZs diferentes
   - VPC: Default
   - Public access: **YES**
   - Backup retention: **7 days**
   - Initial database: `clusterdb`
   - Clic en **Create database**

3. **Esperar a que esté Available**
   - Tarda ~20-30 minutos
   - Se crean 3 instancias automáticamente

---

### 📋 Paso 2: Verificar Arquitectura del Cluster

1. **Ver instancias del cluster**
   - RDS > Databases
   - Ver el cluster `rds-multi-az-cluster`
   - Expandir: verás 3 instancias:
     - 1 Writer
     - 2 Readers

2. **Ver endpoints**
   - Cluster endpoint (Writer): Para escrituras
   - Reader endpoint: Para lecturas (balancea entre los 2 readers)
   - Instance endpoints: 3 endpoints individuales

3. **Crear datos**
   ```bash
   mysql -h rds-multi-az-cluster.cluster-xxxxx.us-east-1.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   CREATE DATABASE clusterdb;
   USE clusterdb;
   CREATE TABLE cluster_test (
       id INT PRIMARY KEY AUTO_INCREMENT,
       dato VARCHAR(200)
   );
   
   INSERT INTO cluster_test (dato) VALUES 
   ('Dato en Multi-AZ Cluster'),
   ('Alta disponibilidad mejorada');
   
   SELECT * FROM cluster_test;
   ```

---

### 📋 Paso 3: Probar Failover en Multi-AZ Cluster

1. **Iniciar failover**
   - Seleccionar el cluster
   - Actions > **Failover**
   - Confirmar

2. **Observar el proceso**
   - Failover mucho más rápido que Multi-AZ tradicional
   - Tiempo: ~35 segundos (en vez de 1-2 minutos)
   - Uno de los readers se convierte en writer
   - El antiguo writer se convierte en reader

3. **Verificar**
   - Endpoint del cluster NO cambia
   - Aplicación continúa funcionando con mínima interrupción

---

### 📊 Comparación Multi-AZ: 1 Standby vs Cluster

| Característica | Multi-AZ 1 Standby | Multi-AZ Cluster |
|----------------|-------------------|------------------|
| **Instancias** | 1 primaria + 1 standby | 1 writer + 2 readers |
| **AZs** | 2 | 3 |
| **Failover** | 1-2 minutos | ~35 segundos |
| **Lecturas en standby** | ❌ No | ✅ Sí (2 readers) |
| **Rendimiento lectura** | Normal | 2x (2 readers activos) |
| **Coste** | ~2x instancia single | ~3x instancia single |
| **Motores** | Todos | MySQL 8.0.28+, PostgreSQL 13.4+ |
| **Instance types** | t3, t4, m, r | Solo m, r (NO t3/t4) |
| **Ideal para** | HA básica | HA + alto rendimiento |

---

## 🧹 Limpieza de Recursos

### RDS Proxy:
```
1. RDS > Proxies > Seleccionar proxy > Delete
2. Secrets Manager > Secrets > Eliminar secret
3. IAM > Roles > Eliminar RDSProxyRole
4. RDS > Databases > Eliminar instancia RDS
```

### Snapshots:
```
1. RDS > Snapshots > Seleccionar snapshots manuales > Delete
2. Los snapshots automáticos se eliminan automáticamente
3. Eliminar instancias restauradas
```

### AWS Backup:
```
1. AWS Backup > Backup plans > Seleccionar plan > Delete
2. AWS Backup > Backup vaults > Default > Eliminar recovery points
3. Eliminar instancias restauradas
```

### Multi-AZ:
```
1. RDS > Databases > Seleccionar instancia/cluster
2. Actions > Delete
3. Desmarcar snapshots finales
4. Confirmar eliminación
```

---

## ⚠️ Notas Importantes

### RDS Proxy:
- 💡 Muy útil con Lambda y aplicaciones serverless
- 💡 Reduce el número de conexiones a la BD
- 💰 Coste adicional: ~$0.015/hora por vCPU del proxy
- ⚠️ Requiere Secrets Manager (coste adicional)

### Backups:
- ✅ Snapshots automáticos: Siempre habilitarlos en producción
- ✅ Multi-región: Copiar snapshots a otra región para DR
- 💰 Coste: ~$0.095/GB-mes almacenado
- ⏱️ PITR: Solo disponible con backups automáticos

### Multi-AZ:
- ✅ Esencial para producción
- ✅ Protege contra fallos de AZ, no de región
- ❌ NO es réplica de lectura
- 💰 Multi-AZ Cluster es ~3x más caro pero ofrece lecturas
- ⚠️ Failover automático solo si falla infraestructura, no por errores de aplicación