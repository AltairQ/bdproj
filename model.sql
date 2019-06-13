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

-- note: this template is not used because DCL stmts cannot be parameterized
--SQL_CREATEAPPUSER_START
CREATE USER app WITH PASSWORD %s NOCREATEDB NOCREATEROLE LOGIN;
--SQL_CREATEAPPUSER_END


--SQL_CREATE_TB_USEDIDS_START
CREATE TABLE used_ids (
	id integer PRIMARY KEY
);
--SQL_CREATE_TB_USEDIDS_END

--SQL_CREATE_TESTFUNC_START
CREATE FUNCTION test() RETURNS integer AS
$$
SELECT 123;
$$ LANGUAGE SQL SECURITY DEFINER;
--SQL_CREATE_TESTFUNC_END


--SQL_GRANTEX_TESTFUNC_START
GRANT EXECUTE ON FUNCTION test() TO app;
--SQL_GRANTEX_TESTFUNC_END

--SQL_CREATE_TB_MEMBERS_START
CREATE TABLE IF NOT EXISTS members(
	id integer PRIMARY KEY,
	password VARCHAR(255) NOT NULL,
	is_leader boolean NOT NULL DEFAULT FALSE,
	upvotes integer NOT NULL DEFAULT 0,
	last_active timestamp NOT NULL
);
--SQL_CREATE_TB_MEMBERS_END

-- BELOW TODO: FOREIGN KEYS


--SQL_CREATE_TB_VOTES_START
CREATE TABLE IF NOT EXISTS votes(
	member integer NOT NULL,
	action integer NOT NULL,
	type integer NOT NULL
);
--SQL_CREATE_TB_VOTES_END

--SQL_CREATE_TB_ACTIONS_START
CREATE TABLE IF NOT EXISTS actions(
	id integer PRIMARY KEY,
	type integer NOT NULL,
	project integer NOT NULL,
	creator integer NOT NULL
);
--SQL_CREATE_TB_ACTIONS_END

--SQL_CREATE_TB_PROJECTS_START
CREATE TABLE IF NOT EXISTS projects(
	id integer PRIMARY KEY,
	authority integer
);
--SQL_CREATE_TB_PROJECTS_END
