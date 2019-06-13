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
CREATE ROLE app WITH PASSWORD %s NOCREATEDB NOCREATEROLE LOGIN;
--SQL_CREATEAPPUSER_END

-- this statement is not used for obvious reasons
--SQL_CREATEDB_STUDENT_START
CREATE DATABASE IF NOT EXISTS student OWNER init;
--SQL_CREATEDB_STUDENT_END


--SQL_CREATE_TB_USEDIDS_START
CREATE TABLE used_ids (
	id integer PRIMARY KEY
);
--SQL_CREATE_TB_USEDIDS_END

--SQL_CREATE_TB_MEMBERS_START
CREATE TABLE IF NOT EXISTS members(
	id integer PRIMARY KEY,
	password VARCHAR(255) NOT NULL,
	is_leader boolean NOT NULL DEFAULT FALSE,
	upvotes integer NOT NULL DEFAULT 0,
	downvotes integer NOT NULL DEFAULT 0,
	last_active timestamp NOT NULL
);
--SQL_CREATE_TB_MEMBERS_END

-- BELOW TODO: FOREIGN KEYS


--SQL_CREATE_TB_VOTES_START
CREATE TABLE IF NOT EXISTS votes(
	member integer NOT NULL,
	action integer NOT NULL,
	up boolean NOT NULL
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
	authority integer NOT NULL
);
--SQL_CREATE_TB_PROJECTS_END


-- Procedure for the `projects` on insert trigger
--SQL_CREATE_TRP_PROJECTS_START
CREATE FUNCTION projects_trig() RETURNS TRIGGER AS $$
	BEGIN
		INSERT INTO used_ids VALUES (NEW.id);
		IF NOT EXISTS (SELECT * FROM projects WHERE authority = NEW.authority) THEN
			INSERT INTO used_ids VALUES (NEW.authority);
		END IF;
		RETURN NEW;
	END;
$$ LANGUAGE plpgsql;
--SQL_CREATE_TRP_PROJECTS_END

--SQL_CREATE_TR_PROJECTS_START
CREATE TRIGGER projects_insert BEFORE INSERT ON projects
FOR EACH ROW EXECUTE PROCEDURE projects_trig();
--SQL_CREATE_TR_PROJECTS_END

-- Procedure for the `actions` on insert trigger
--SQL_CREATE_TRP_ACTIONS_START
CREATE FUNCTION actions_trig() RETURNS TRIGGER AS $$
	BEGIN
		INSERT INTO used_ids VALUES (NEW.id);
		RETURN NEW;
	END;
$$ LANGUAGE plpgsql;
--SQL_CREATE_TRP_ACTIONS_END

--SQL_CREATE_TR_ACTIONS_START
CREATE TRIGGER actions_insert BEFORE INSERT ON actions
FOR EACH ROW EXECUTE PROCEDURE actions_trig();
--SQL_CREATE_TR_ACTIONS_END


-- Procedure for the `members` on insert trigger
--SQL_CREATE_TRP_MEMBERS_START
CREATE FUNCTION members_trig() RETURNS TRIGGER AS $$
	BEGIN
		INSERT INTO used_ids VALUES (NEW.id);
		RETURN NEW;
	END;
$$ LANGUAGE plpgsql;
--SQL_CREATE_TRP_MEMBERS_END

--SQL_CREATE_TR_MEMBERS_START
CREATE TRIGGER members_insert BEFORE INSERT ON members
FOR EACH ROW EXECUTE PROCEDURE members_trig();
--SQL_CREATE_TR_MEMBERS_END


-- Procedure for the `votes` on insert trigger
--SQL_CREATE_TRP_VOTES_START
CREATE FUNCTION votes_trig() RETURNS TRIGGER AS $$
	DECLARE
	v_creator integer;
	BEGIN
		v_creator := (SELECT creator FROM actions where id = NEW.action);
		IF NEW.up = TRUE THEN
			UPDATE members SET upvotes = upvotes + 1 WHERE id = v_creator;
		ELSE
			UPDATE members SET downvotes = downvotes + 1 WHERE id = v_creator;
		END IF;
		RETURN NEW;
	END;
$$ LANGUAGE plpgsql;
--SQL_CREATE_TRP_VOTES_END

--SQL_CREATE_TR_VOTES_START
CREATE TRIGGER votes_insert BEFORE INSERT ON votes
FOR EACH ROW EXECUTE PROCEDURE votes_trig();
--SQL_CREATE_TR_VOTES_END
