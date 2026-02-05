# Guía T1: Bases de Datos No Relacionales vs Relacionales - RDS Básico

## Crear RDS con Acceso Público y Conectar

### 📋 Paso 1: Crear la Base de Datos RDS

1. **Acceder al servicio RDS**
   - Ir a la consola de AWS
   - Buscar "RDS" en el buscador de servicios
   - Clic en "Databases" en el menú lateral
   - Clic en "Create database"

2. **Configuración del motor**
   - Choose a database creation method: **Standard create**
   - Engine options: **MySQL** (o el motor que prefieras)
   - Engine Version: Dejar la versión recomendada o seleccionar una específica
   - Templates: **Free tier** (si está disponible) o **Dev/Test**

3. **Configuración de la instancia**
   - DB instance identifier: `mi-rds-prueba` (nombre único)
   - Master username: `admin`
   - Master password: Crear contraseña segura (ej: `Admin123456`)
   - Confirm password: Repetir la contraseña
   - **⚠️ IMPORTANTE: Anota usuario y contraseña**

4. **Configuración de instancia**
   - DB instance class: 
     - Burstable classes: **db.t3.micro** o **db.t4g.micro** (Free tier)
   - Storage type: **General Purpose SSD (gp3)**
   - Allocated storage: **20 GiB** (mínimo)
   - Desmarcar "Enable storage autoscaling" (para pruebas)

5. **Conectividad (CLAVE para acceso público)**
   - Compute resource: **Don't connect to an EC2 compute resource**
   - Network type: **IPv4**
   - Virtual private cloud (VPC): Seleccionar la VPC por defecto
   - DB subnet group: default
   - **Public access: YES** ⚠️ (Importante activar)
   - VPC security group: 
     - Choose existing
     - Crear nuevo o seleccionar "default"
   - Availability Zone: No preference
   - Database port: **3306** (MySQL) o el puerto por defecto del motor elegido

6. **Autenticación de base de datos**
   - Database authentication: **Password authentication**

7. **Configuración adicional**
   - Initial database name: `testdb` (opcional pero recomendado)
   - DB parameter group: default
   - Option group: default
   - Backup:
     - Enable automated backups: **Desmarcar** (para pruebas rápidas)
   - Encryption: Dejar por defecto
   - Monitoring: Desmarcar "Enable Enhanced monitoring" (para pruebas)
   - Maintenance: Dejar opciones por defecto

8. **Crear la base de datos**
   - Revisar estimación de costes
   - Clic en **Create database**
   - Esperar 5-10 minutos hasta que el estado sea "Available"

---

### 🔒 Paso 2: Configurar Security Group para Acceso Público

1. **Acceder al Security Group**
   - En la página de la base de datos creada, ir a "Connectivity & security"
   - En "Security", clic en el security group activo (ej: sg-xxxxx)

2. **Editar reglas de entrada (Inbound rules)**
   - Clic en "Edit inbound rules"
   - Clic en "Add rule"
   - Type: **MySQL/Aurora** (o el tipo correspondiente)
   - Protocol: TCP
   - Port range: **3306** (o el puerto de tu motor)
   - Source: **Anywhere-IPv4** (0.0.0.0/0) ⚠️ Solo para pruebas
   - Description: `Acceso publico temporal para pruebas`
   - Clic en "Save rules"

---

### 💻 Paso 3: Conectar desde Terminal

1. **Obtener el endpoint**
   - Volver a la consola RDS > Databases
   - Clic en tu base de datos
   - En "Connectivity & security", copiar el **Endpoint** (ej: `mi-rds-prueba.xxxxx.us-east-1.rds.amazonaws.com`)

2. **Instalar cliente MySQL** (si no lo tienes)
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install mysql-client
   
   # macOS
   brew install mysql-client
   
   # Windows
   # Descargar MySQL Client desde mysql.com
   ```

3. **Conectar a la base de datos**
   ```bash
   mysql -h mi-rds-prueba.xxxxx.us-east-1.rds.amazonaws.com -P 3306 -u admin -p
   ```
   - Introducir la contraseña cuando se solicite

4. **Verificar conexión**
   ```sql
   SHOW DATABASES;
   USE testdb;
   CREATE TABLE prueba (id INT, nombre VARCHAR(50));
   INSERT INTO prueba VALUES (1, 'Test');
   SELECT * FROM prueba;
   ```

---

### 🖥️ Paso 4: Conectar desde MySQL Workbench

1. **Abrir MySQL Workbench**
   - Descargar desde: https://dev.mysql.com/downloads/workbench/ (si no lo tienes)

2. **Crear nueva conexión**
   - Clic en el botón **"+"** junto a "MySQL Connections"
   - Connection Name: `AWS RDS Prueba`
   - Connection Method: **Standard (TCP/IP)**
   - Hostname: `mi-rds-prueba.xxxxx.us-east-1.rds.amazonaws.com`
   - Port: `3306`
   - Username: `admin`
   - Password: Clic en "Store in Vault..." y poner la contraseña
   - Default Schema: `testdb` (opcional)

3. **Probar conexión**
   - Clic en "Test Connection"
   - Debe aparecer "Successfully made the MySQL connection"
   - Clic en "OK"

4. **Conectar y trabajar**
   - Hacer doble clic en la conexión creada
   - Ya puedes ejecutar queries en el editor SQL

---

### 🧹 Paso 5: Limpieza (Importante para no generar costes)

1. **Eliminar la base de datos**
   - Ir a RDS > Databases
   - Seleccionar tu base de datos
   - Actions > Delete
   - Desmarcar "Create final snapshot"
   - Desmarcar "Retain automated backups"
   - Escribir `delete me` en el campo de confirmación
   - Clic en "Delete"

---

## ⚠️ Notas Importantes

- **Seguridad**: El acceso público con 0.0.0.0/0 es SOLO para pruebas. En producción usar VPN, Security Groups restrictivos o acceso desde EC2.
- **Costes**: RDS genera costes incluso cuando no se usa. Eliminar cuando termines las pruebas.
- **Free Tier**: Solo db.t3.micro y db.t4g.micro con 20GB durante 750 horas/mes el primer año.
- **Endpoint**: Cambia cada vez que se crea una nueva instancia RDS.