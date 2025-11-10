-- ==============================================
-- SCRIPT DE INSERCIÓN INICIAL PARA SQLITE
-- Tablas: CustomUser, Empresa, OptionForm, UserAccess
-- ==============================================

-- Insertar usuarios (8 en total, 2 por empresa)
INSERT INTO accounts_customuser (
    password, last_login, is_superuser, username, 
    first_name, last_name, email, is_staff, 
    is_active, date_joined, telephone, dui
)
VALUES
-- Empresa A1  andresstela y carolinastela
('pbkdf2_sha256$720000$Vtfq6yCZdZZKgfWakwK7uw$om/y0SOKwu0zrkplxvO3/9Mii4cWCwtqIyfRq+3WmSo=', NULL, 0, 'andres.mendoza_stela', 'Andrés', 'Mendoza', 'andres.mendoza@stela.com', 1, 1, CURRENT_TIMESTAMP, '7000-0001', '11111111-1'),
('pbkdf2_sha256$720000$MUCtcjooEfB2tvwvNzxY0k$rIPa0xjpn49xY0b1CTMSp04zw4phc/IVzm//YcbZcek=', NULL, 0, 'carolina.rojas_stela', 'Carolina', 'Rojas', 'carolina.rojas@stela.com', 0, 1, CURRENT_TIMESTAMP, '7000-0002', '11111111-2'),

-- Empresa A2  mariostela y sofiastela
('pbkdf2_sha256$720000$sEZg9oDn64BTaIoibEFoFT$eyNuzKQ8/EYuXRRQ8W2DQ5ANf8l5nyWxRbiMwniDnSY=', NULL, 0, 'mario.castillo_stela', 'Mario', 'Castillo', 'mario.castillo@stela.com', 1, 1, CURRENT_TIMESTAMP, '7000-0003', '11111111-3'),
('pbkdf2_sha256$720000$QkNzwwL8v3Ewx1upLRuYN2$U0yHCZSCHEQPnm8TQozwH1szTs6kscBilJZ0zNCXOzQ=', NULL, 0, 'sofia.perez_stela', 'Sofía', 'Pérez', 'sofia.perez@stela.com', 0, 1, CURRENT_TIMESTAMP, '7000-0004', '11111111-4'),

-- Empresa B1  luisstela y elenastela
('pbkdf2_sha256$720000$pK3yVx7So3EMCc6tOdP4rl$BiA/wCXp4jOt/mFvIXc6kG5G4MOpk4zg5osq3VwwCeU=', NULL, 0, 'luis.cardenas_stela', 'Luis', 'Cárdenas', 'luis.cardenas@stela.com', 1, 1, CURRENT_TIMESTAMP, '7000-0005', '22222222-1'),
('pbkdf2_sha256$720000$SuFcecbtdfqCDmrsfcrEy0$OROYCo+07m1LEkVU8F7vmaloYxVqwTLNxhwfX5fongs=', NULL, 0, 'elena.gomez_stela', 'Elena', 'Gómez', 'elena.gomez@stela.com', 0, 1, CURRENT_TIMESTAMP, '7000-0006', '22222222-2'),

-- Empresa B2 diegostela y valeriastela
('pbkdf2_sha256$720000$2K7CigozlfvzqjAjQ4JeCQ$3eL7XTFANSN30nuhizXogiZ8Z3YoCBR9oEk4c4eJFxA=', NULL, 0, 'diego.martinez_stela', 'Diego', 'Martínez', 'diego.martinez@stela.com', 1, 1, CURRENT_TIMESTAMP, '7000-0007', '22222222-3'),
('pbkdf2_sha256$720000$qSAepdfcvp9Fb41GVTxCow$pbYX5rtOM8RNM+fSVzgbGp2oLPQeGHcEPQ7eRe5e+OM=', NULL, 0, 'valeria.ramirez_stela', 'Valeria', 'Ramírez', 'valeria.ramirez@stela.com', 0, 1, CURRENT_TIMESTAMP, '7000-0008', '22222222-4');


-- Insertar empresas (2 por rubro, 4 en total)
INSERT INTO stela_empresa (
    nit, ciiu_id, nrc, razon_social, direccion, telefono, email
)
VALUES
-- Rubro: Alojamiento 
('0614-010101-101-1', '5510001', 'A10001', 'Hotel Casa Verde S.A. de C.V.', 'San Salvador', '2222-1111', 'contacto@hotelcasaverde.stela.com'),
('0614-010102-102-2', '5510001', 'A10002', 'Hostal Buen Día S.A. de C.V.', 'Santa Ana', '2222-2222', 'contacto@hostalbuenadia.stela.com'),

-- Rubro: Servicio de comidas 
('0614-020201-201-3', '5610017', 'B20001', 'Restaurante La Pupusa Gourmet S.A. de C.V.', 'San Miguel', '2222-3333', 'contacto@lapupusa.stela.com'),
('0614-020202-202-4', '5610017', 'B20002', 'Cafetería Central El Rincón S.A. de C.V.', 'La Libertad', '2222-4444', 'contacto@cafeteriacentral.stela.com');


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
('004', 'Perfil de usuario logueado', 4),
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
('040', 'Calcular ratios y análisis financiero', 40),
('041', 'Crear Empresa', 41),
('042', 'Editar Empresa', 42),
('043', 'Editar usuario logueado', 43);

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

-- Ver Perfil de usuario
INSERT INTO accounts_useraccess (userId_id, optionId_id, companyId_id)
VALUES
(2, '004', NULL),
(4, '004', NULL),
(6, '004', NULL),
(8, '004', NULL);

-- Editar Perfil de usuario
INSERT INTO accounts_useraccess (userId_id, optionId_id, companyId_id)
VALUES
(2, '043', NULL),
(4, '043', NULL),
(6, '043', NULL),
(8, '043', NULL);
