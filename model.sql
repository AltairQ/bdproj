--  NOTE: This file is internally used by the application
--  as it's parsing its contents to extract SQL statements during
--  init phase and further operation.
--  Please do not edit the starting and ending comments, which
--  allow the application to parse this file.

-- Create the 'app' user with no permissions.
-- We assume that scram-sha-256 is enabled.
-- This means we must provide plaintext password as the
-- backend will salt and hash it.
-- Also, pg8000 driver does support this auth method.

--SQL_CREATEUSER_START
CREATE USER app WITH PASSWORD %s NOCREATEDB NOCREATEUSER;
--SQL_CREATEUSER_END



