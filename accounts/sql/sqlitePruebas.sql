-- ==============================================
-- SCRIPT DE INSERCIÓN INICIAL PARA SQLITE
-- Tablas: Ciiu, CustomUser, Empresa, OptionForm, UserAccess
-- ==============================================

-- Insertar códigos CIIU de prueba
INSERT INTO stela_ciiu (codigo, descripcion, nivel, padre_id)
VALUES
('A001', 'Agricultura y ganadería', 1, NULL),
('B001', 'Comercio al por menor', 1, NULL);

-- Insertar usuarios (8 en total, 2 por empresa)
INSERT INTO accounts_customuser (
    password, last_login, is_superuser, username, 
    first_name, last_name, email, is_staff, 
    is_active, date_joined, telephone, dui
)
VALUES
-- Empresa A1
('pbkdf2_sha256$720000$GG6MMJnILxzjMdoM717koi$bvsMldQnazAN0O1ILhbQmf5GJSqPNgXpCYWqAeD/cZs=', NULL, 0, 'userA1_full', 'Carlos', 'A1', 'a1_full@empresa.com', 1, 1, CURRENT_TIMESTAMP, '7000-0001', '11111111-1'),
('pbkdf2_sha256$720000$tygEAjJCd7XqBfWpfqZEWr$2pb77Pg3fToYxWrfU+zOEMqejBF0XbTEMkkbM+2UIzs=', NULL, 0, 'userA1_limited', 'Lucía', 'A1', 'a1_limited@empresa.com', 0, 1, CURRENT_TIMESTAMP, '7000-0002', '11111111-2'),

-- Empresa A2
('pbkdf2_sha256$720000$xSdcJ2pTg92XKvXv2J8xEc$fmDewec0jnYkEAE+dg3HVxcK/8TrvxO/VDo+7YIh000=', NULL, 0, 'userA2_full', 'Mario', 'A2', 'a2_full@empresa.com', 1, 1, CURRENT_TIMESTAMP, '7000-0003', '11111111-3'),
('pbkdf2_sha256$720000$ux9z7mXLvz34GrknECEJGZ$QcX2mNp9xKNJjPDi4LoQdQnPHwfTWmF2fNsujvb7hTI=', NULL, 0, 'userA2_limited', 'Sofía', 'A2', 'a2_limited@empresa.com', 0, 1, CURRENT_TIMESTAMP, '7000-0004', '11111111-4'),

-- Empresa B1
('pbkdf2_sha256$720000$K9wnxgUpx9fGPZ8mmzKYW7$hGZlfuP38rHmxddxQafqSKq1zi3spTrR6LzNdC7Jz24=', NULL, 0, 'userB1_full', 'Luis', 'B1', 'b1_full@empresa.com', 1, 1, CURRENT_TIMESTAMP, '7000-0005', '22222222-1'),
('pbkdf2_sha256$720000$hashB2$passB2', NULL, 0, 'userB1_limited', 'Elena', 'B1', 'b1_limited@empresa.com', 0, 1, CURRENT_TIMESTAMP, '7000-0006', '22222222-2'),

-- Empresa B2
('pbkdf2_sha256$720000$hashB3$passB3', NULL, 0, 'userB2_full', 'Diego', 'B2', 'b2_full@empresa.com', 1, 1, CURRENT_TIMESTAMP, '7000-0007', '22222222-3'),
('pbkdf2_sha256$720000$hashB4$passB4', NULL, 0, 'userB2_limited', 'Valeria', 'B2', 'b2_limited@empresa.com', 0, 1, CURRENT_TIMESTAMP, '7000-0008', '22222222-4');

-- Insertar empresas (2 por rubro, 4 en total)
INSERT INTO stela_empresa (
    nit, idCiiu_id, nrc, razon_social, direccion, telefono, email
)
VALUES
-- Rubro A
('0614-010101-101-1', 'A001', 'A10001', 'Empresa A1', 'San Salvador', '2222-1111', 'contacto@a1.com'),
('0614-010102-102-2', 'A001', 'A10002', 'Empresa A2', 'Santa Ana', '2222-2222', 'contacto@a2.com'),

-- Rubro B
('0614-020201-201-3', 'B001', 'B20001', 'Empresa B1', 'San Miguel', '2222-3333', 'contacto@b1.com'),
('0614-020202-202-4', 'B001', 'B20002', 'Empresa B2', 'La Libertad', '2222-4444', 'contacto@b2.com');

-- Relacionar empresas con usuarios (ManyToMany)
INSERT INTO stela_empresa_usuario (empresa_id, customuser_id)
VALUES
-- Empresa A1
('0614-010101-101-1', 1),
('0614-010101-101-1', 2),
-- Empresa A2
('0614-010102-102-2', 3),
('0614-010102-102-2', 4),
-- Empresa B1
('0614-020201-201-3', 5),
('0614-020201-201-3', 6),
-- Empresa B2
('0614-020202-202-4', 7),
('0614-020202-202-4', 8);

-- Insertar opciones del sistema (vistas principales)
INSERT INTO accounts_optionform (optionId, description, formNumber)
VALUES
('002', 'Dashboard de empresas y catálogos', 2),
('003', 'Detalles de empresa', 3),
('004', 'Crear empresa', 4),
('005', 'Herramientas financieras', 5),
('006', 'Proyecciones de ventas (vista)', 6),
('007', 'Listado de códigos CIIU', 7),
('008', 'Carga de catálogo y estados financieros desde Excel', 8),
('009', 'Crear catálogo manualmente', 9),
('010', 'Mapeo de cuentas para ratios', 10);

-- Insertar acciones internas
INSERT INTO accounts_optionform (optionId, description, formNumber)
VALUES
('036', 'Crear código CIIU', 36),
('037', 'Editar código CIIU', 37),
('038', 'Eliminar código CIIU', 38),
('040', 'Calcular ratios y análisis financiero', 40);

-- Insertar accesos para usuarios con acceso completo (todas las opciones)
INSERT INTO accounts_useraccess (userId_id, optionId_id, companyId_id)
SELECT 1, optionId, '0614-010101-101-1' FROM accounts_optionform;
INSERT INTO accounts_useraccess (userId_id, optionId_id, companyId_id)
SELECT 3, optionId, '0614-010102-102-2' FROM accounts_optionform;
INSERT INTO accounts_useraccess (userId_id, optionId_id, companyId_id)
SELECT 5, optionId, '0614-020201-201-3' FROM accounts_optionform;
INSERT INTO accounts_useraccess (userId_id, optionId_id, companyId_id)
SELECT 7, optionId, '0614-020202-202-4' FROM accounts_optionform;

-- Insertar accesos para usuarios con acceso limitado (solo opciones seleccionadas)
-- Usuario 2 (Empresa A1)
INSERT INTO accounts_useraccess (userId_id, optionId_id, companyId_id)
VALUES
(2, '002', '0614-010101-101-1'),
(2, '003', '0614-010101-101-1'),
(2, '004', '0614-010101-101-1'),
(2, '005', '0614-010101-101-1'),
(2, '006', '0614-010101-101-1'),
(2, '007', '0614-010101-101-1'),
(2, '009', '0614-010101-101-1'),
(2, '010', '0614-010101-101-1');

-- Usuario 4 (Empresa A2)
INSERT INTO accounts_useraccess (userId_id, optionId_id, companyId_id)
VALUES
(4, '002', '0614-010102-102-2'),
(4, '003', '0614-010102-102-2'),
(4, '004', '0614-010102-102-2'),
(4, '005', '0614-010102-102-2'),
(4, '006', '0614-010102-102-2'),
(4, '007', '0614-010102-102-2'),
(4, '009', '0614-010102-102-2'),
(4, '010', '0614-010102-102-2');

-- Usuario 6 (Empresa B1)
INSERT INTO accounts_useraccess (userId_id, optionId_id, companyId_id)
VALUES
(6, '002', '0614-020201-201-3'),
(6, '003', '0614-020201-201-3'),
(6, '004', '0614-020201-201-3'),
(6, '005', '0614-020201-201-3'),
(6, '006', '0614-020201-201-3'),
(6, '007', '0614-020201-201-3'),
(6, '009', '0614-020201-201-3'),
(6, '010', '0614-020201-201-3');

-- Usuario 8 (Empresa B2)
INSERT INTO accounts_useraccess (userId_id, optionId_id, companyId_id)
VALUES
(8, '002', '0614-020202-202-4'),
(8, '003', '0614-020202-202-4'),
(8, '004', '0614-020202-202-4'),
(8, '005', '0614-020202-202-4'),
(8, '006', '0614-020202-202-4'),
(8, '007', '0614-020202-202-4'),
(8, '009', '0614-020202-202-4'),
(8, '010', '0614-020202-202-4');
