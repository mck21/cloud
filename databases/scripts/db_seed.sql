-- Crear base de datos
CREATE DATABASE dbmck21;

-- Usar la base de datos
USE dbmck21;

-- Crear tabla productos
CREATE TABLE productos (
    id_producto INT PRIMARY KEY AUTO_INCREMENT,
    nombre_producto VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10, 2) NOT NULL,
    cantidad_stock INT NOT NULL DEFAULT 0,
    categoria VARCHAR(50),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo'
);

-- Insertar datos de prueba
INSERT INTO productos (nombre_producto, descripcion, precio, cantidad_stock, categoria) VALUES
('Laptop HP', 'Laptop HP 15 pulgadas, procesador Intel i5, 8GB RAM', 599.99, 15, 'Electrónica'),
('Mouse inalámbrico', 'Mouse inalámbrico USB, batería de larga duración', 29.99, 50, 'Accesorios'),
('Teclado mecánico', 'Teclado mecánico RGB con switches azules', 89.99, 25, 'Accesorios'),
('Monitor LED 24"', 'Monitor LED 24 pulgadas, resolución Full HD', 179.99, 10, 'Electrónica'),
('Auriculares Bluetooth', 'Auriculares inalámbricos con cancelación de ruido', 149.99, 30, 'Audio');

-- Consultar los datos insertados
SELECT * FROM productos;