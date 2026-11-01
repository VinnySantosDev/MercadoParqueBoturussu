-- =====================================================================
-- 01_banco.sql — CREATE DATABASE
-- Projeto Integrador — Modelagem de Dados | Supermercado Parque Boturussu
-- SGBD: MySQL 8.0 (testado em 8.0.46). utf8mb4 para acentos e símbolos.
-- ATENÇÃO: recria o banco do zero (apaga o anterior, se existir).
-- =====================================================================
SET NAMES utf8mb4;
DROP DATABASE IF EXISTS mercado_boturussu;

CREATE DATABASE mercado_boturussu
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE mercado_boturussu;
