import sys
import json
import re
import pg8000


# global DB handle
_glob_db = None
_glob_is_init = False
_glob_debug = False


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
	# todo fix?
	tmp = f"CREATE ROLE app WITH PASSWORD '{kvp['password']}' NOCREATEDB NOCREATEROLE LOGIN;"
	cur.execute(tmp)

	# install pgcrypto
	# only in debug mode because it requires SUPERUSER role
	if _glob_debug:
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
	cur.execute(_xsql("CREATE_API_ACTIONS"))

	# grant execute permissions
	cur.execute(_xsql("GRANTEX_API_LEADER"))
	cur.execute(_xsql("GRANTEX_API_SUPPORT"))
	cur.execute(_xsql("GRANTEX_API_PROTEST"))
	cur.execute(_xsql("GRANTEX_API_UPVOTE"))
	cur.execute(_xsql("GRANTEX_API_ACTIONS"))

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
		(kvp["timestamp"], kvp["password"], kvp["member"]))
	_ret_ok()

	_glob_db.commit()
	cur.close()
	pass

def support(kvp):
	pass

def protest(kvp):
	pass

def upvote(kvp):
	pass

def downvote(kvp):
	pass

def actions(kvp):
	pass

def projects(kvp):
	pass

def votes(kvp):
	pass

def trolls(kvp):
	pass

def _ret_error(s):
	print(json.dumps({"status":"ERROR","debug": s}))

def _ret_ok():
	print(json.dumps({"status":"OK"}))

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

	if "--init" in sys.argv: # check if init mode is set
		_glob_is_init = True
		log("* init on")
		
	main()
