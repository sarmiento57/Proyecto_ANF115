-- ==============================================
-- SCRIPT DE INSERCIÓN INICIAL PARA SQLITE
-- Tablas: CustomUser, OptionForm, UserAccess
-- ==============================================

-- Insertar datos en la tabla CustomUser
INSERT INTO accounts_customuser (
    password, last_login, is_superuser, username, 
    first_name, last_name, email, is_staff, 
    is_active, date_joined, telephone, dui
)
VALUES
-- Usuario admin contra administrador
('pbkdf2_sha256$720000$60Jl9UXnUdC9qU3FRYyua9$UIpB35Ktm6xAede143cNHWndSfV9RhrrwycDRa0B6hg=', NULL, 1, 'admin',
 'Administrador', 'General', 'admin@stela.com', 1,
 1, CURRENT_TIMESTAMP, '7123-4567', '23456789-0'),

-- Usuario normal 1  contra vegetta777
('pbkdf2_sha256$720000$fZRQp9YyisgYhTdzRsxk60$QMzaxtG3Cxcltg40Sz/7Wb+qrnaYaS4R+WlBAPHmQkk=', NULL, 0, 'vegetta777',
 'Vegetta', 'Sietesiete', 'vegettasiete@stela.com', 0,
 1, CURRENT_TIMESTAMP, '7777-7777', '77777777-7'),

-- Usuario normal 2 contra anaStela
('pbkdf2_sha256$720000$UjQxZdzG3SYN4bM1CfxL6Z$KJD2IUkctkTe/5aZE3w65K+L8rVMODUxdhPInQIfYDw=', NULL, 0, 'anaStela',
 'Ana', 'Martínez', 'ana@stela.com', 0,
 1, CURRENT_TIMESTAMP, '7890-1234', '23456789-0');



-- Insertar opciones del formulario para las vistas principales
INSERT INTO accounts_optionform (optionId, description, formNumber)
VALUES
('010', 'Dashboard', 0),
('011', 'Catálogos', 1),
('012', 'Tipos de Empresa', 2),
('014', 'Empresas', 3),
('015', 'Ratios Generales por tipo de Empresa', 4),
('016', 'Panel de Administración', 5),
('017', 'Tools', 6),
('018', 'Perfiles de Usuario', 7),
('019', 'Cuentas', 8);


-- Insertar opciones del formulario catalogo opciones botones
INSERT INTO accounts_optionform (optionId, description, formNumber)
VALUES
('030', 'Agregar cuenta de catalogo', 30),
('031', 'Editar cuenta de catalogo', 31),
('032', 'Eliminar cuenta de catalogo', 32),
('033', 'Ver catalogo de cuentas', 33),
-- Boton para cargar catalogo desde un excel
('034', 'Cargar catalogo desde Excel', 34);

-- Insertar opciones del formulario tipos de empresa botones
INSERT INTO accounts_optionform (optionId, description, formNumber)
VALUES
('040', 'Agregar tipo de empresa', 40),
('041', 'Editar tipo de empresa', 41),
('042', 'Eliminar tipo de empresa', 42),
('043', 'Ver tipos de empresa', 43);


-- Insertar opciones del formulario empresas botones
INSERT INTO accounts_optionform (optionId, description, formNumber)
VALUES
('050', 'Agregar empresa', 50),
('051', 'Editar empresa', 51),
('052', 'Eliminar empresa', 52),
('053', 'Ver empresas', 53);

-- Insertar opciones del formulario perfiles botones
INSERT INTO accounts_optionform (optionId, description, formNumber)
VALUES
('060', 'Agregar perfil de usuario', 60),
('061', 'Editar perfil de usuario', 61),
('062', 'Eliminar perfil de usuario', 62),
('063', 'Ver perfiles de usuario', 63);

-- Insertar opciones del formulario señalar cuentas seleccionadas
INSERT INTO accounts_optionform (optionId, description, formNumber)
VALUES
('070', 'Señalar cuentas seleccionadas', 70);


-- Insertar accesos de usuario
-- Acceso para admin 
INSERT INTO accounts_useraccess (userId_id, optionId_id)
SELECT 1, optionId FROM accounts_optionform;

-- dar acceso parcial a usuario 1 
INSERT INTO accounts_useraccess (userId_id, optionId_id)
VALUES 
(2, '010'),
(2, '011'),
(2, '017'); 

-- dar acceso parcial a usuario 2 
INSERT INTO accounts_useraccess (userId_id, optionId_id)
VALUES 
(3, '010'),
(3, '012');
