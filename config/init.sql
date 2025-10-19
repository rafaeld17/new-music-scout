-- Initial database setup for Music Scout
-- This file is run when the PostgreSQL container starts for the first time

-- Create any additional extensions we might need
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';