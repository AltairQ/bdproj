import sys
import json
import re
import pg8000


# global DB handle
_glob_db_handle = None
_glob_is_init = False

# extract SQL statement template from the model file
def _xsql(tokname):
	with open("model.sql", "r") as f:
		whole = f.read()
		needle = f"--SQL_{tokname}_START((.|\s)*)--SQL_{tokname}_END"
		res = re.search(needle, whole)
		return(res.group(1).strip())


def oopen():
	pass

def leader():
	pass

def support():
	pass

def protest():
	pass

def upvote():
	pass

def downvote():
	pass

def actions():
	pass

def projects():
	pass

def votes():
	pass

def trolls():
	pass

def init():
	pass

def _ret_error(s):
	print(json.dumps({"status":"ERROR","debug": s}))

def _open_conn(user, pswd):
	try:
		_glob_db_handle = pg8000.connect(user=user, password=pswd)
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

def a2f(action):
	return _glob_func_dict.get(action, 
		lambda x : _ret_error("unknown action!"))


def main():
	for l in sys.stdin:
		line = l.rstrip()
		try:
			obj = json.loads(line)
			act = next(iter(obj))
			(a2f(act))(obj[act])
		except Exception as e:
			_ret_error(str(e))


if __name__ == '__main__':
	if "--init" in sys.argv:
		_glob_is_init = True
		print("--- INIT ENGAGED ---")
	main()
