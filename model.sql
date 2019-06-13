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
	password text NOT NULL,
	status integer NOT NULL DEFAULT 2,
	upvotes integer NOT NULL DEFAULT 0,
	downvotes integer NOT NULL DEFAULT 0,
	last_active timestamp NOT NULL
);
--SQL_CREATE_TB_MEMBERS_END

-- BELOW TODO: FOREIGN KEYS

--SQL_INSTALL_PGCRYPTO_START
CREATE EXTENSION pgcrypto;
--SQL_INSTALL_PGCRYPTO_END


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


-- Internal function for creating and validating users
-- mustcreate flag causes it to raise exception when
-- trying to create an user (only leader api)

--SQL_CREATE_PRIV_CREATEUSER_START
CREATE FUNCTION pcreateuser(iid integer, pswd text, is_leader boolean,
	tstamp timestamp, mustcreate boolean)
RETURNS integer AS $$
	DECLARE
	res_stat integer;
	res_time timestamp;
	tmp_stat integer;
	BEGIN

		IF is_leader = TRUE THEN
			tmp_stat := 1;
		ELSE
			tmp_stat := 2;
		END IF;

		SELECT status, last_active INTO res_stat, res_time FROM
		members where id = iid AND password = crypt(pswd, password);

		IF res_stat IS NOT NULL THEN
			IF mustcreate = TRUE THEN
				RAISE EXCEPTION 'User (%) already exists', iid;
			END IF;

			IF date_part('year', age(tstamp, res_time)) >= 1 THEN
				RETURN 0;
			ELSE
				RETURN res_stat;
			END IF;
		END IF;

		INSERT INTO members (id, password, status, last_active) VALUES
		(iid, crypt(pswd, gen_salt('bf', 9)), tmp_stat, tstamp);

		RETURN tmp_stat;
	END;
$$ LANGUAGE plpgsql;
--SQL_CREATE_PRIV_CREATEUSER_END

--SQL_CREATE_API_LEADER_START
CREATE FUNCTION api_leader(epo integer, pswd text, mem integer) 
RETURNS void AS $$
BEGIN
	PERFORM pcreateuser(mem, pswd, TRUE, 
		to_timestamp(epo)::timestamp without time zone, TRUE);
	RETURN;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
--SQL_CREATE_API_LEADER_END

--SQL_GRANTEX_API_LEADER_START
GRANT EXECUTE ON FUNCTION api_leader(epo integer, pswd text, mem integer) 
TO app;
--SQL_GRANTEX_API_LEADER_END

--SQL_CREATE_PRIV_ADDACTION_START
CREATE FUNCTION paddaction(epo integer, memid integer, pswd text,
	aid integer, pid integer, authority integer, atype integer)
RETURNS void AS $$
DECLARE
	tmp_projid integer;
BEGIN
	IF pcreateuser(memid, pswd, FALSE, 
		to_timestamp(epo)::timestamp without time zone, FALSE) = 0 THEN
		RAISE EXCEPTION 'User (%) frozen', memid;
	END IF;

	IF NOT EXISTS (SELECT * from projects WHERE id = pid) THEN
		INSERT INTO projects (id, authority) VALUES
			(pid, authority);
	END IF;

	INSERT INTO actions (id, type, project, creator) VALUES
		(aid, atype, pid, memid);
	RETURN;
END;
$$ LANGUAGE plpgsql;
--SQL_CREATE_PRIV_ADDACTION_END


--SQL_CREATE_API_SUPPORT_START
CREATE FUNCTION api_support(epo integer, memid integer, pswd text,
	aid integer, pid integer, authority integer)
RETURNS void AS $$
DECLARE
	tmp_projid integer;
BEGIN
	PERFORM paddaction(epo, memid, pswd, aid, pid, authority, 1);
	RETURN;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
--SQL_CREATE_API_SUPPORT_END

--SQL_GRANTEX_API_SUPPORT_START
GRANT EXECUTE ON FUNCTION api_support(epo integer, memid integer, pswd text,
	aid integer, pid integer, authority integer)
TO app;
--SQL_GRANTEX_API_SUPPORT_END

--SQL_CREATE_API_PROTEST_START
CREATE FUNCTION api_protest(epo integer, memid integer, pswd text,
	aid integer, pid integer, authority integer)
RETURNS void AS $$
DECLARE
	tmp_projid integer;
BEGIN
	PERFORM paddaction(epo, memid, pswd, aid, pid, authority, 0);
	RETURN;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
--SQL_CREATE_API_PROTEST_END

--SQL_GRANTEX_API_PROTEST_START
GRANT EXECUTE ON FUNCTION api_protest(epo integer, memid integer, pswd text,
	aid integer, pid integer, authority integer)
TO app;
--SQL_GRANTEX_API_PROTEST_END

