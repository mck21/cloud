# Guía T3: Escalado de Bases de Datos Relacionales

## 1. Escalado Vertical

### 📋 Concepto
- Aumentar/disminuir recursos de la instancia (CPU, RAM)
- Cambiar el tipo de instancia (ej: db.t3.micro → db.t3.medium)
- **Limitación**: Requiere downtime (reinicio)

---

### 📋 Paso 1: Crear RDS Base para Escalar

1. **Crear RDS inicial**
   - Ir a RDS > Databases > "Create database"
   - Engine: **MySQL**
   - Templates: **Free tier** o **Dev/Test**
   - DB instance identifier: `rds-escalado-vertical`
   - Master username: `admin`
   - Master password: Crear contraseña segura
   - DB instance class: **db.t3.micro** (instancia pequeña inicial)
   - Storage: **20 GiB**
   - Public access: **YES** (para pruebas)
   - Initial database name: `escaladb`
   - Backup: Desmarcar backups automáticos
   - Clic en **Create database**

2. **Esperar a que esté Available**

---

### 📈 Paso 2: Realizar Escalado Vertical

1. **Modificar la instancia**
   - Ir a RDS > Databases
   - Seleccionar `rds-escalado-vertical`
   - Clic en **Modify**

2. **Cambiar el tipo de instancia**
   - En "DB instance class" cambiar de **db.t3.micro** a **db.t3.small**
   - Scroll hasta el final
   - En "Scheduling of modifications" seleccionar:
     - **Apply immediately** (cambio inmediato con downtime)
     - o **Apply during the next scheduled maintenance window** (sin downtime hasta ventana)

3. **Aplicar cambios**
   - Clic en **Continue**
   - Revisar resumen de cambios
   - Clic en **Modify DB instance**

4. **Observar el proceso**
   - Estado cambiará: Available → Modifying → Rebooting → Available
   - Durante este tiempo la BD NO está disponible
   - **Anotar tiempo de downtime**: ~5-10 minutos

5. **Verificar cambio**
   - En la pestaña "Configuration" verificar que ahora es **db.t3.small**
   - Conectar y verificar que todo funciona

---

### 📊 Paso 3: Escalar Almacenamiento (sin downtime)

1. **Modificar almacenamiento**
   - Seleccionar la instancia
   - Clic en **Modify**
   - En "Allocated storage" cambiar de **20 GiB** a **30 GiB**
   - Apply immediately
   - Clic en **Continue** > **Modify DB instance**

2. **Observar**
   - El estado sigue "Available"
   - El escalado de almacenamiento NO requiere downtime
   - Se aplica en caliente

---

## 2. Escalado Horizontal - Réplicas de Lectura RDS

### 📋 Concepto
- Crear copias read-only de la BD
- Distribuir lecturas entre múltiples instancias
- La instancia principal (master) maneja escrituras
- Las réplicas sincronizan datos de forma asíncrona

---

### 📋 Paso 1: Crear RDS Master

1. **Crear RDS principal**
   - DB instance identifier: `rds-master-replicas`
   - Engine: **MySQL**
   - Instance class: **db.t3.micro**
   - Storage: **20 GiB**
   - **MUY IMPORTANTE**: En "Additional configuration"
     - Backup retention period: **1 day** (mínimo, necesario para réplicas)
   - Public access: **YES**
   - Initial database: `masterdb`
   - Clic en **Create database**

2. **Insertar datos de prueba**
   ```bash
   mysql -h rds-master-replicas.xxxxx.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   USE masterdb;
   CREATE TABLE productos (
       id INT PRIMARY KEY AUTO_INCREMENT,
       nombre VARCHAR(100),
       precio DECIMAL(10,2)
   );
   
   INSERT INTO productos (nombre, precio) VALUES 
   ('Laptop', 999.99),
   ('Mouse', 29.99),
   ('Teclado', 79.99);
   
   SELECT * FROM productos;
   ```

---

### 📋 Paso 2: Crear Réplica de Lectura

1. **Crear la réplica**
   - Ir a RDS > Databases
   - Seleccionar `rds-master-replicas`
   - Actions > **Create read replica**

2. **Configurar la réplica**
   - DB instance identifier: `rds-replica-1`
   - Destination region: **Same region** (misma región)
   - DB instance class: **db.t3.micro** (puede ser diferente al master)
   - Storage type: Heredado del master
   - Public access: **YES** (para pruebas)
   - VPC security group: Mismo que el master
   - Monitoring: Desmarcar Enhanced monitoring
   - Clic en **Create read replica**

3. **Esperar a que esté Available**
   - Estado: Creating → Backing-up → Available
   - Tiempo: ~10-15 minutos

---

### 📋 Paso 3: Verificar Replicación

1. **Conectar al Master y agregar datos**
   ```bash
   mysql -h rds-master-replicas.xxxxx.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   USE masterdb;
   INSERT INTO productos (nombre, precio) VALUES ('Monitor', 299.99);
   SELECT * FROM productos;
   -- Debería mostrar 4 productos
   ```

2. **Conectar a la Réplica y verificar**
   ```bash
   mysql -h rds-replica-1.xxxxx.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   USE masterdb;
   SELECT * FROM productos;
   -- Debería mostrar los mismos 4 productos (sincronizado)
   ```

3. **Probar que la réplica es READ-ONLY**
   ```sql
   -- En la réplica:
   INSERT INTO productos (nombre, precio) VALUES ('Test', 10.00);
   -- ERROR: The MySQL server is running with the --read-only option
   ```

---

### 📋 Paso 4: Crear Segunda Réplica (Opcional)

1. **Crear réplica adicional**
   - Seleccionar `rds-master-replicas` (el master)
   - Actions > Create read replica
   - DB instance identifier: `rds-replica-2`
   - Misma configuración
   - Clic en **Create read replica**

2. **Verificar arquitectura**
   - 1 Master (escritura)
   - 2 Réplicas (lectura)
   - Total: 3 instancias sincronizadas

---

### 📋 Paso 5: Promover Réplica a Master (Failover Manual)

1. **Promover réplica**
   - Seleccionar `rds-replica-1`
   - Actions > **Promote read replica**
   - Configuración de backup: 
     - Backup retention period: **1 day**
     - Backup window: Default
   - Clic en **Promote read replica**

2. **Observar el proceso**
   - La réplica se convierte en instancia independiente
   - Ya NO replica desde el master original
   - Ahora acepta escrituras (read-write)

3. **Verificar**
   ```bash
   mysql -h rds-replica-1.xxxxx.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   USE masterdb;
   -- Ahora SÍ permite escrituras
   INSERT INTO productos (nombre, precio) VALUES ('Promocionado', 100.00);
   SELECT * FROM productos;
   ```

---

## 3. Escalado Horizontal - Réplicas en Aurora

### 📋 Concepto Aurora
- Arquitectura cluster: 1 Writer + hasta 15 Readers
- Almacenamiento compartido (cluster volume)
- Replicación síncrona (sin lag)
- Failover automático < 30 segundos
- Mejor rendimiento que RDS MySQL con réplicas

---

### 📋 Paso 1: Crear Aurora Cluster

1. **Crear cluster Aurora**
   - Ir a RDS > Databases > "Create database"
   - Engine type: **Amazon Aurora**
   - Edition: **Amazon Aurora MySQL-Compatible Edition**
   - Templates: **Dev/Test**
   - DB cluster identifier: `aurora-cluster-replicas`
   - Master username: `admin`
   - Master password: Crear contraseña segura
   - DB instance class: **db.t3.small** (mínimo para Aurora)
   - Multi-AZ deployment: **Don't create an Aurora Replica** (por ahora)
   - Public access: **YES**
   - Initial database name: `auroradb`
   - Clic en **Create database**

2. **Esperar a que esté Available**
   - Se crea automáticamente 1 instancia Writer

---

### 📋 Paso 2: Insertar Datos de Prueba

```bash
# Conectar al Writer Endpoint
mysql -h aurora-cluster-replicas.cluster-xxxxx.us-east-1.rds.amazonaws.com -u admin -p
```

```sql
CREATE DATABASE IF NOT EXISTS auroradb;
USE auroradb;

CREATE TABLE ventas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    producto VARCHAR(100),
    cantidad INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO ventas (producto, cantidad) VALUES 
('Producto A', 10),
('Producto B', 20),
('Producto C', 15);

SELECT * FROM ventas;
```

---

### 📋 Paso 3: Crear Réplica de Lectura en Aurora

1. **Añadir réplica al cluster**
   - Ir a RDS > Databases
   - Seleccionar el cluster `aurora-cluster-replicas` (NO la instancia)
   - Actions > **Add reader**

2. **Configurar la réplica**
   - DB instance identifier: `aurora-cluster-replicas-reader-1`
   - DB instance class: **db.t3.small** (puede ser diferente)
   - Availability zone: Seleccionar una AZ diferente al Writer
   - Public access: **YES**
   - Clic en **Add reader**

3. **Esperar a que esté Available**
   - Mucho más rápido que RDS (~2-5 minutos)
   - Comparte almacenamiento con el Writer

---

### 📋 Paso 4: Verificar Endpoints de Aurora

1. **Identificar los 3 endpoints**
   - Seleccionar el cluster
   - Pestaña "Connectivity & security":
     - **Cluster endpoint** (Writer): Para escrituras
     - **Reader endpoint** (balanceo): Para lecturas (distribuye entre readers)
     - **Instance endpoints**: Endpoints individuales de cada instancia

2. **Probar Writer Endpoint**
   ```bash
   mysql -h aurora-cluster-replicas.cluster-xxxxx.us-east-1.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   USE auroradb;
   INSERT INTO ventas (producto, cantidad) VALUES ('Producto D', 25);
   SELECT * FROM ventas;
   ```

3. **Probar Reader Endpoint**
   ```bash
   mysql -h aurora-cluster-replicas.cluster-ro-xxxxx.us-east-1.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   USE auroradb;
   SELECT * FROM ventas;
   -- Muestra todos los datos (incluyendo el último INSERT)
   -- La sincronización es prácticamente instantánea
   
   INSERT INTO ventas (producto, cantidad) VALUES ('Test', 1);
   -- ERROR: Cannot execute statement in a READ ONLY transaction
   ```

---

### 📋 Paso 5: Crear Segunda y Tercera Réplica

1. **Añadir más réplicas**
   - Seleccionar el cluster
   - Actions > Add reader
   - DB instance identifier: `aurora-cluster-replicas-reader-2`
   - AZ: Otra zona de disponibilidad
   - Clic en **Add reader**

2. **Repetir para tercera réplica** (opcional)
   - DB instance identifier: `aurora-cluster-replicas-reader-3`

3. **Arquitectura final**
   - 1 Writer (escrituras)
   - 3 Readers (lecturas distribuidas)
   - Reader Endpoint balancea entre las 3 réplicas automáticamente

---

### 📋 Paso 6: Failover Automático en Aurora

1. **Simular fallo del Writer**
   - Seleccionar la instancia Writer (NO el cluster)
   - Actions > **Failover**
   - Confirmar

2. **Observar el proceso**
   - Aurora promueve automáticamente una Reader a Writer
   - Tiempo de failover: < 30 segundos
   - Los endpoints NO cambian (el cluster endpoint apunta al nuevo Writer)
   - Una de las Reader se convierte en Writer
   - El antiguo Writer se convierte en Reader (cuando se recupere)

3. **Verificar después del failover**
   ```bash
   # Mismo endpoint, nuevo Writer transparente
   mysql -h aurora-cluster-replicas.cluster-xxxxx.us-east-1.rds.amazonaws.com -u admin -p
   ```
   
   ```sql
   USE auroradb;
   INSERT INTO ventas (producto, cantidad) VALUES ('Post-Failover', 30);
   -- Funciona sin problemas
   ```

---

### 📋 Paso 7: Autoscaling de Réplicas Aurora (Opcional)

1. **Configurar Auto Scaling**
   - Seleccionar el cluster
   - Actions > **Add replica auto scaling**
   - Policy name: `aurora-autoscaling-policy`
   - Target metric: **Average CPU utilization**
   - Target value: **70** %
   - Minimum capacity: **1** (mínimo 1 reader)
   - Maximum capacity: **3** (máximo 3 readers)
   - Clic en **Add policy**

2. **Cómo funciona**
   - Si CPU > 70%: Aurora añade réplicas automáticamente
   - Si CPU < 70%: Aurora reduce réplicas
   - Solo escala dentro del rango 1-3 readers

---

## 📊 Comparación RDS vs Aurora Réplicas

| Característica | RDS MySQL Réplicas | Aurora Réplicas |
|----------------|-------------------|-----------------|
| **Máximo réplicas** | 5 | 15 |
| **Replicación** | Asíncrona (lag posible) | Síncrona (sin lag) |
| **Almacenamiento** | Independiente (duplicado) | Compartido (cluster) |
| **Failover** | Manual (promote) | Automático < 30s |
| **Tiempo creación réplica** | 10-15 min | 2-5 min |
| **Endpoints** | Individuales | Cluster + Reader + Individuales |
| **Coste** | Menor | Mayor (~20% más) |
| **Rendimiento** | Bueno | Excelente |
| **Auto Scaling** | No | Sí |

---

## 🧹 Limpieza de Recursos

### Para RDS con Réplicas:
```
1. Eliminar réplicas: Seleccionar réplica > Actions > Delete
2. Eliminar master: Seleccionar master > Actions > Delete
3. Desmarcar snapshots finales
```

### Para Aurora Cluster:
```
1. Eliminar readers: Seleccionar cada reader > Actions > Delete
2. Eliminar writer: Seleccionar writer > Actions > Delete
3. Eliminar cluster: Seleccionar cluster > Actions > Delete
4. Desmarcar "Create final snapshot"
```

---

## ⚠️ Notas Importantes

### Escalado Vertical:
- ✅ Simple de implementar
- ❌ Requiere downtime
- ❌ Tiene límite físico (máximo tamaño de instancia)
- 💡 Ideal para cargas predecibles que crecen gradualmente

### Escalado Horizontal (RDS):
- ✅ No requiere downtime para lectura
- ✅ Distribuye carga de lectura
- ❌ Lag de replicación posible
- ❌ Solo 5 réplicas máximo
- 💡 Ideal para aplicaciones read-heavy

### Escalado Horizontal (Aurora):
- ✅ Hasta 15 réplicas
- ✅ Sin lag de replicación
- ✅ Failover automático
- ✅ Auto scaling
- ❌ Más costoso
- 💡 Ideal para aplicaciones críticas y alta disponibilidad

### Costes:
- Cada réplica se cobra como instancia independiente
- Aurora es ~20% más caro pero incluye características enterprise
- Free Tier: Solo aplica a RDS MySQL/PostgreSQL, NO a réplicas ni Aurora