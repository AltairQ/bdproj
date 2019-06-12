import sys
import json
import re
import pg8000


# global DB handle
_glob_db = None
_glob_is_init = False

# extract SQL statement template from the model file
def _xsql(tokname):
	with open("model.sql", "r") as f:
		whole = f.read()
		needle = f"--SQL_{tokname}_START((.|\s)*)--SQL_{tokname}_END"
		res = re.search(needle, whole)
		return(res.group(1).strip())

def _init(kvp):
	pg8000.paramstyle = "format"
	cur = _glob_db.cursor()
	# very ugly but it can't be parametrized
	# besides, at this point the user already knows init password
	# todo fix?
	tmp = f"CREATE ROLE app WITH PASSWORD '{kvp['password']}' NOCREATEDB NOCREATEROLE LOGIN;"
	cur.execute(tmp)
	cur.execute(_xsql("CREATE_TB_USEDIDS"))
	cur.execute(_xsql("CREATE_TESTFUNC"))
	cur.execute(_xsql("GRANTEX_TESTFUNC"))	
	_glob_db.commit()
	cur.close()
	pass


def oopen(kvp):
	_open_conn(kvp["login"], kvp["password"], kvp["database"])
	if _glob_is_init:
		_init(kvp)

def leader(kvp):
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

# connect to psql server @localhost
def _open_conn(user, pswd, db):
	try:
		global _glob_db
		_glob_db = pg8000.connect(user=user, password=pswd, database=db)
		print("* opened db", file=sys.stderr)
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
	if "--init" in sys.argv: # check if init mode is set
		_glob_is_init = True
		print("--- INIT ENGAGED ---")
	main()
