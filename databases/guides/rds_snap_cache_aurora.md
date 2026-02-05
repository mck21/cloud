# Guía T2: Despliegue de RDS

## 1. Crear RDS con Acceso desde EC2 y Conectar

### 📋 Paso 1: Crear una instancia EC2

1. **Acceder al servicio EC2**
   - Ir a la consola de AWS
   - Buscar "EC2" en el buscador de servicios
   - Clic en "Instances" > "Launch instances"

2. **Configuración básica de EC2**
   - Name: `EC2-RDS-Client`
   - AMI: **Amazon Linux 2023** o **Ubuntu Server**
   - Instance type: **t2.micro** (Free tier)
   - Key pair: Crear nueva o seleccionar existente
   - Network settings:
     - VPC: Usar la VPC por defecto
     - Auto-assign public IP: **Enable**
     - Security group: Crear nuevo o usar existente (permitir SSH - puerto 22)
   - Clic en "Launch instance"

---

### 📋 Paso 2: Crear RDS con Conexión Automática a EC2

1. **Acceder al servicio RDS**
   - Ir a RDS > Databases > "Create database"

2. **Configuración del motor**
   - Choose a database creation method: **Standard create**
   - Engine options: **MySQL**
   - Engine Version: Dejar la recomendada
   - Templates: **Free tier** o **Dev/Test**

3. **Configuración de la instancia**
   - DB instance identifier: `rds-desde-ec2`
   - Master username: `admin`
   - Master password: Crear contraseña segura
   - Confirm password: Repetir contraseña

4. **Configuración de instancia**
   - DB instance class: **db.t3.micro**
   - Storage type: **General Purpose SSD (gp3)**
   - Allocated storage: **20 GiB**

5. **Conectividad (CLAVE)**
   - Compute resource: **Connect to an EC2 compute resource**
   - EC2 instance: Seleccionar `EC2-RDS-Client` (la instancia creada)
   - Network type: **IPv4**
   - **Public access: NO** (acceso solo desde EC2)
   - VPC security group: Se creará automáticamente
   - Database port: **3306**

6. **Configuración adicional**
   - Initial database name: `dbdesdeec2`
   - Backup: Desmarcar backups automáticos (para pruebas)
   - Clic en **Create database**
   - Esperar hasta que esté "Available"

---

### 💻 Paso 3: Conectar desde EC2 a RDS

1. **Conectar a la instancia EC2 por SSH**
   ```bash
   # Desde tu terminal local
   ssh -i "tu-key.pem" ec2-user@<IP-PUBLICA-EC2>
   # o si es Ubuntu:
   ssh -i "tu-key.pem" ubuntu@<IP-PUBLICA-EC2>
   ```

2. **Instalar cliente MySQL en EC2**
   ```bash
   # Amazon Linux 2023
   sudo dnf install mariadb105 -y
   
   # Ubuntu
   sudo apt update
   sudo apt install mysql-client -y
   ```

3. **Conectar a RDS desde EC2**
   ```bash
   # Obtener el endpoint desde la consola RDS
   mysql -h rds-desde-ec2.xxxxx.us-east-1.rds.amazonaws.com -P 3306 -u admin -p
   ```

4. **Verificar conexión**
   ```sql
   SHOW DATABASES;
   USE dbdesdeec2;
   CREATE TABLE test (id INT, dato VARCHAR(100));
   INSERT INTO test VALUES (1, 'Conexion desde EC2');
   SELECT * FROM test;
   ```

---

## 2. Crear RDS, Hacer Snapshot y Crear Caché (Comparar)

### 📋 Paso 1: Crear RDS Base

1. **Crear RDS normal**
   - Seguir pasos estándar de creación
   - DB instance identifier: `rds-snapshot-test`
   - Engine: **MySQL**
   - Instance class: **db.t3.micro**
   - Storage: **20 GiB**
   - Public access: **YES** (para pruebas)
   - Initial database: `snapshotdb`

2. **Esperar a que esté Available**

---

### 📸 Paso 2: Crear Snapshot Manual

1. **Crear el snapshot**
   - Ir a RDS > Databases
   - Seleccionar `rds-snapshot-test`
   - Actions > **Take snapshot**
   - Snapshot name: `snapshot-manual-rds-test`
   - Clic en "Take snapshot"

2. **Verificar snapshot**
   - Ir a RDS > Snapshots
   - Ver el snapshot en estado "Creating" → "Available"
   - **Anotar el tiempo que tarda**

---

### 📋 Paso 3: Restaurar desde Snapshot

1. **Restaurar RDS desde snapshot**
   - Ir a RDS > Snapshots
   - Seleccionar `snapshot-manual-rds-test`
   - Actions > **Restore snapshot**
   - DB instance identifier: `rds-restaurada-desde-snapshot`
   - DB instance class: **db.t3.micro**
   - Public access: **YES**
   - Clic en "Restore DB instance"

2. **Verificar datos**
   - Conectar a la nueva instancia restaurada
   - Comprobar que los datos están presentes

---

### ⚡ Paso 4: Crear ElastiCache (Redis) - Comparar Velocidad

1. **Acceder a ElastiCache**
   - Buscar "ElastiCache" en servicios AWS
   - Clic en "Get started" o "Create cluster"

2. **Configuración de Redis**
   - Cluster mode: **Disabled**
   - Cluster engine: **Redis**
   - Name: `cache-rds-comparison`
   - Engine version: Dejar la recomendada
   - Node type: **cache.t3.micro** o **cache.t4g.micro**
   - Number of replicas: **0** (para pruebas)

3. **Configuración de red**
   - Subnet group: Crear nuevo o usar default
   - Security groups: Crear nuevo permitiendo puerto **6379**
   - Encryption: Desmarcar (para pruebas rápidas)
   - Backup: Desmarcar
   - Clic en "Create"

4. **Comparación RDS vs ElastiCache**
   - **RDS**: Persistencia, queries complejas, datos estructurados
   - **ElastiCache**: Velocidad, datos en memoria, cacheo, sesiones
   - **Latencia**: Cache ~1ms vs RDS ~10-50ms
   - **Uso**: Cache para lecturas frecuentes, RDS para almacenamiento permanente

---

## 3. Crear RDS con Aurora

### 🚀 Opción A: Aurora Serverless

### 📋 Paso 1: Crear Aurora Serverless v2

1. **Crear cluster Aurora**
   - Ir a RDS > Databases > "Create database"

2. **Configuración del motor**
   - Choose a database creation method: **Standard create**
   - Engine type: **Amazon Aurora**
   - Edition: **Amazon Aurora MySQL-Compatible Edition**
   - Engine version: Aurora MySQL 3.x compatible con MySQL 8.0
   - Templates: **Dev/Test**

3. **Configuración del cluster**
   - DB cluster identifier: `aurora-serverless-cluster`
   - Master username: `admin`
   - Master password: Crear contraseña segura
   - Confirm password: Repetir

4. **Configuración de instancia**
   - DB instance class: **Serverless v2**
   - Capacity settings:
     - Minimum ACUs: **0.5** (mínimo)
     - Maximum ACUs: **2** (para pruebas)

5. **Conectividad**
   - VPC: Default
   - Public access: **YES** (para pruebas)
   - VPC security group: Crear nuevo
   - Database port: **3306**

6. **Configuración adicional**
   - Initial database name: `auroraserverlessdb`
   - Backup retention: **1 day** (mínimo)
   - Desmarcar "Enable deletion protection"
   - Clic en **Create database**

7. **Características de Serverless**
   - ✅ Escalado automático según demanda
   - ✅ Puede bajar a 0 ACUs (pausarse)
   - ✅ Pago por segundo de uso
   - ✅ Ideal para cargas variables

---

### 🖥️ Opción B: Aurora Aprovisionado

### 📋 Paso 1: Crear Aurora Aprovisionado

1. **Crear cluster Aurora**
   - Ir a RDS > Databases > "Create database"

2. **Configuración del motor**
   - Choose a database creation method: **Standard create**
   - Engine type: **Amazon Aurora**
   - Edition: **Amazon Aurora MySQL-Compatible Edition**
   - Engine version: Aurora MySQL 3.x
   - Templates: **Production** o **Dev/Test**

3. **Configuración del cluster**
   - DB cluster identifier: `aurora-aprovisionado-cluster`
   - Master username: `admin`
   - Master password: Crear contraseña segura

4. **Configuración de instancia**
   - DB instance class: **Burstable classes**
   - Instance type: **db.t3.small** o **db.t4g.small**
   - Multi-AZ deployment: 
     - **Don't create an Aurora Replica** (para pruebas)
     - o **Create an Aurora Replica in a different AZ** (para HA)

5. **Conectividad**
   - VPC: Default
   - Public access: **YES** (para pruebas)
   - VPC security group: Crear nuevo permitiendo puerto 3306
   - Database port: **3306**

6. **Configuración adicional**
   - Initial database name: `auroradb`
   - DB cluster parameter group: default
   - DB parameter group: default
   - Backup retention: **1 day**
   - Desmarcar "Enable deletion protection"
   - Clic en **Create database**

7. **Características de Aprovisionado**
   - ✅ Rendimiento predecible
   - ✅ Hasta 15 réplicas de lectura
   - ✅ Failover automático < 30 segundos
   - ✅ Almacenamiento compartido (cluster volume)
   - ✅ Mejor para cargas constantes

---

### 📊 Comparación Aurora Serverless vs Aprovisionado

| Característica | Serverless v2 | Aprovisionado |
|----------------|---------------|---------------|
| **Escalado** | Automático (ACUs) | Manual (instancias) |
| **Coste** | Por segundo de uso | Pago por hora de instancia |
| **Arranque** | Instantáneo | Instantáneo |
| **Pausado automático** | Sí (puede bajar a 0) | No |
| **Rendimiento** | Variable según ACUs | Fijo según instancia |
| **Réplicas** | Automáticas | Hasta 15 manuales |
| **Ideal para** | Cargas variables | Cargas predecibles |
| **Mínimo coste** | 0.5 ACU (~$0.06/h) | db.t3.small (~$0.04/h) |

---

### 💻 Conectar a Aurora (ambas opciones)

```bash
# Obtener el Writer Endpoint desde la consola RDS
mysql -h aurora-xxxxx.cluster-xxxxx.us-east-1.rds.amazonaws.com -P 3306 -u admin -p
```

```sql
-- Verificar versión Aurora
SELECT @@aurora_version;
SHOW DATABASES;
```

---

## 🧹 Limpieza de Recursos

### Para RDS con EC2:
```
1. Eliminar RDS: Actions > Delete
2. Eliminar EC2: Terminate instance
3. Eliminar Security Groups creados
```

### Para Snapshots:
```
1. RDS > Snapshots > Seleccionar > Actions > Delete
2. Eliminar instancias RDS restauradas
```

### Para ElastiCache:
```
1. ElastiCache > Redis clusters > Seleccionar > Delete
```

### Para Aurora:
```
1. RDS > Databases > Seleccionar cluster
2. Actions > Delete
3. Desmarcar "Create final snapshot"
4. Confirmar eliminación
5. Eliminar instancias del cluster si quedan
```

---

## ⚠️ Notas Importantes

- **Aurora Serverless**: Ideal para desarrollo, cargas impredecibles, aplicaciones poco frecuentes
- **Aurora Aprovisionado**: Ideal para producción, cargas constantes, alta disponibilidad
- **ElastiCache**: NO reemplaza a RDS, complementa para mejorar rendimiento
- **Snapshots**: Los snapshots son incrementales (solo cambios), pero ocupan espacio
- **Costes**: Aurora es más caro que RDS MySQL estándar, pero ofrece mejor rendimiento
- **Free Tier**: Aurora NO está en Free Tier, genera costes desde el primer momento