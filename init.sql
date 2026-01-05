-- Initialize PostgreSQL database for Materials Explorer
-- This script sets up extensions needed for the application

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable btree_gin for efficient indexing
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create database (if it doesn't exist)
-- Note: This is handled by the POSTGRES_DB environment variable

-- Set timezone
SET timezone = 'UTC';