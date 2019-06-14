#!/usr/bin/env python3

import sys
import json
import re
import pg8000


# global DB handle
_glob_db = None
_glob_is_init = False
_glob_debug = False
_glob_inst_crypto = False

# helper function for printing debug messages
def log(s):
	if(_glob_debug):
		print(s, file=sys.stderr)


# extract SQL statement template from the model file
def _xsql(tokname):
	log("* xsql: " + tokname)
	with open("model.sql", "r") as f:
		whole = f.read()
		needle = f"^--SQL_{tokname}_START((.|\s)*?)--SQL_{tokname}_END"
		res = re.search(needle, whole, flags=re.MULTILINE)
		return(res.group(1).strip())

def _init(kvp):
	# this is the default
	pg8000.paramstyle = "format"
	cur = _glob_db.cursor()

	# very ugly but it can't be parametrized
	# besides, at this point the user already knows init password
	tmp = f"CREATE ROLE app WITH PASSWORD '{kvp['password']}' NOCREATEDB NOCREATEROLE LOGIN;"
	cur.execute(tmp)

	# install pgcrypto
	# only in special mode because it requires SUPERUSER role
	if _glob_inst_crypto:
		log("* installing pgcrypto in the current db")
		cur.execute(_xsql("INSTALL_PGCRYPTO"))

	# create tables
	cur.execute(_xsql("CREATE_TB_USEDIDS"))
	cur.execute(_xsql("CREATE_TB_PROJECTS"))
	cur.execute(_xsql("CREATE_TB_MEMBERS"))
	cur.execute(_xsql("CREATE_TB_ACTIONS"))
	cur.execute(_xsql("CREATE_TB_VOTES"))

	# create trigger functions
	cur.execute(_xsql("CREATE_TRP_PROJECTS"))
	cur.execute(_xsql("CREATE_TRP_ACTIONS"))
	cur.execute(_xsql("CREATE_TRP_MEMBERS"))
	cur.execute(_xsql("CREATE_TRP_VOTES"))

	# register triggers
	cur.execute(_xsql("CREATE_TR_PROJECTS"))
	cur.execute(_xsql("CREATE_TR_ACTIONS"))
	cur.execute(_xsql("CREATE_TR_MEMBERS"))
	cur.execute(_xsql("CREATE_TR_VOTES"))

	# create helper functions
	cur.execute(_xsql("CREATE_PRIV_CREATEUSER"))
	cur.execute(_xsql("CREATE_PRIV_ADDACTION"))
	cur.execute(_xsql("CREATE_PRIV_ADDVOTE"))

	# create api functions
	cur.execute(_xsql("CREATE_API_LEADER"))
	cur.execute(_xsql("CREATE_API_SUPPORT"))
	cur.execute(_xsql("CREATE_API_PROTEST"))
	cur.execute(_xsql("CREATE_API_UPVOTE"))
	cur.execute(_xsql("CREATE_API_DOWNVOTE"))
	cur.execute(_xsql("CREATE_API_ACTIONS"))
	cur.execute(_xsql("CREATE_API_PROJECTS"))
	cur.execute(_xsql("CREATE_API_VOTES"))
	cur.execute(_xsql("CREATE_API_TROLLS"))

	# grant execute permissions
	cur.execute(_xsql("GRANTEX_API_LEADER"))
	cur.execute(_xsql("GRANTEX_API_SUPPORT"))
	cur.execute(_xsql("GRANTEX_API_PROTEST"))
	cur.execute(_xsql("GRANTEX_API_UPVOTE"))
	cur.execute(_xsql("GRANTEX_API_DOWNVOTE"))
	cur.execute(_xsql("GRANTEX_API_ACTIONS"))
	cur.execute(_xsql("GRANTEX_API_PROJECTS"))
	cur.execute(_xsql("GRANTEX_API_VOTES"))
	cur.execute(_xsql("GRANTEX_API_TROLLS"))

	_glob_db.commit()
	cur.close()
	pass


def oopen(kvp):
	_open_conn(kvp["login"], kvp["password"], kvp["database"])
	if _glob_is_init:
		_init(kvp)
	_ret_ok()

def leader(kvp):
	cur = _glob_db.cursor()

	cur.execute(_xsql("EXECUTE_API_LEADER"),
		(kvp["timestamp"],
			kvp["password"],
			kvp["member"]))
	_ret_ok()

	_glob_db.commit()
	cur.close()
	pass

def support(kvp):
	cur = _glob_db.cursor()

	cur.execute(_xsql("EXECUTE_API_SUPPORT"),
			(kvp["timestamp"],
			kvp["member"],
			kvp["password"],
			kvp["action"],
			kvp["project"],
			kvp.get("authority", None) ))
	_ret_ok()

	_glob_db.commit()
	cur.close()
	

def protest(kvp):
	cur = _glob_db.cursor()

	cur.execute(_xsql("EXECUTE_API_PROTEST"),
			(kvp["timestamp"],
			kvp["member"],
			kvp["password"],
			kvp["action"],
			kvp["project"],
			kvp.get("authority", None) ))
	_ret_ok()

	_glob_db.commit()
	cur.close()


def upvote(kvp):
	cur = _glob_db.cursor()

	cur.execute(_xsql("EXECUTE_API_UPVOTE"),
			(kvp["timestamp"],
			kvp["member"],
			kvp["password"],
			kvp["action"]))
	_ret_ok()

	_glob_db.commit()
	cur.close()

def downvote(kvp):
	cur = _glob_db.cursor()

	cur.execute(_xsql("EXECUTE_API_DOWNVOTE"),
			(kvp["timestamp"],
			kvp["member"],
			kvp["password"],
			kvp["action"]))
	_ret_ok()

	_glob_db.commit()
	cur.close()

def actions(kvp):
	cur = _glob_db.cursor()

	arg_type = kvp.get("type", None)

	if arg_type:
		if arg_type == "support":
			arg_type = 1
		elif arg_type == "protest":
			arg_type = 0
		else:
			arg_type = None

	cur.execute(_xsql("EXECUTE_API_ACTIONS"),
			(kvp["timestamp"],
			kvp["member"],
			kvp["password"],
			arg_type,
			kvp.get("project", None),
			kvp.get("authority", None) ))

	res = cur.fetchall()

	for row in res:
		row[1] = "support" if row[1] == 1 else "protest"

	_ret_data(res)

	_glob_db.commit()
	cur.close()

def projects(kvp):
	cur = _glob_db.cursor()

	cur.execute(_xsql("EXECUTE_API_PROJECTS"),
			(kvp["timestamp"],
			kvp["member"],
			kvp["password"],
			kvp.get("authority", None) ))

	res = cur.fetchall()
	_ret_data(res)

	_glob_db.commit()
	cur.close()


def votes(kvp):
	cur = _glob_db.cursor()

	cur.execute(_xsql("EXECUTE_API_VOTES"),
			(kvp["timestamp"],
			kvp["member"],
			kvp["password"],
			kvp.get("action", None),
			kvp.get("project", None)))

	res = cur.fetchall()
	_ret_data(res)

	_glob_db.commit()
	cur.close()

def trolls(kvp):
	cur = _glob_db.cursor()

	cur.execute(_xsql("EXECUTE_API_TROLLS"), [kvp["timestamp"]])

	res = cur.fetchall()

	for r in res:
		r[3] = str(r[3]).lower()

	_ret_data(res)

	_glob_db.commit()
	cur.close()


def _ret_error(s):
	print(json.dumps({"status":"ERROR","debug": s}))

def _ret_ok():
	print(json.dumps({"status":"OK"}))

def _ret_data(d):
	print(json.dumps({"status":"OK", "data":d}))

# connect to psql server @localhost
def _open_conn(user, pswd, db):
	try:
		global _glob_db
		_glob_db = pg8000.connect(user=user, password=pswd, database=db)
		log("* opened db connection")
	except Exception as e:
		_ret_error(str(e))


_glob_func_dict = {
	"open" : oopen, # double-o because "open" is a built-in
	"leader" : leader,
	"support" : support,
	"protest" : protest,
	"upvote" : upvote,
	"downvote" : downvote,
	"actions" : actions,
	"projects" : projects,
	"votes" : votes,
	"trolls" : trolls
}

# translate action type into appropriate handler
def a2f(action):
	return _glob_func_dict.get(action, 
		lambda x : _ret_error("unknown action!"))

def main():
	for l in sys.stdin:
		line = l.rstrip()
		try:
			obj = json.loads(line) # safe from code injection
			act = next(iter(obj)) # extract "action" attr
			(a2f(act))(obj[act]) # execute handler
		except Exception as e:
			_ret_error(str(e))


if __name__ == '__main__':
	if "--debug" in sys.argv:
		_glob_debug = True
		log("* debug on")

	if "--install_crypto" in sys.argv:
		_glob_inst_crypto = True
		log("* will install the pgcrypto extensions")

	if "--init" in sys.argv: # check if init mode is set
		_glob_is_init = True
		log("* init on")

	main()
