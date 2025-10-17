-- ==============================================
-- SCRIPT DE INSERCIÓN INICIAL PARA MYSQL
-- Tablas: CustomUser, OptionForm, UserAccess
-- ==============================================

-- Insertar datos en la tablas correspondientes
INSERT INTO accounts_customuser (
    password, last_login, is_superuser, username, 
    first_name, last_name, email, is_staff, 
    is_active, date_joined, telephone, dui
)
VALUES
-- Usuario admin 
('pbkdf2_sha256$720000$60Jl9UXnUdC9qU3FRYyua9$UIpB35Ktm6xAede143cNHWndSfV9RhrrwycDRa0B6hg=', NULL, 1, 'admin',
 'Administrador', 'General', 'admin@stela.com', 1,
 1, NOW(), '7123-4567', '23456789-0'),

-- Usuario normal 1
('pbkdf2_sha256$720000$fZRQp9YyisgYhTdzRsxk60$QMzaxtG3Cxcltg40Sz/7Wb+qrnaYaS4R+WlBAPHmQkk=', NULL, 0, 'vegetta777',
 'Vegetta', 'Sietesiete', 'vegettasiete@stela.com', 0,
 1, NOW(), '7777-7777', '77777777-7'),

-- Usuario normal 2
('pbkdf2_sha256$720000$UjQxZdzG3SYN4bM1CfxL6Z$KJD2IUkctkTe/5aZE3w65K+L8rVMODUxdhPInQIfYDw=', NULL, 0, 'anaStela',
 'Ana', 'Martínez', 'ana@stela.com', 0,
 1, NOW(), '7890-1234', '23456789-0');



-- Insertar opciones del formulario
INSERT INTO accounts_optionform (optionId, description, formNumber)
VALUES
('010', 'Dashboard', 0),
('011', 'Catalogos', 1),
('012', 'Tipos de Empresa', 2),
('014', 'Empresas', 3),
('015', 'Ratios Generales por tipo de Empresa', 4),
('016', 'Panel de Administración', 5),
('017', 'Tools', 6);



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

-- Falta terminar el script con 100 opciones mas al opcion form
