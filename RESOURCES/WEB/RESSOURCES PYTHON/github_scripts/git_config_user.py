# file: git_config_user.py
""" Set local git user.name and user.email """
from utils_run import run
def git_config_user(name, email):
    import json
    out = []
    if name:
        out.append(run('git config user.name ' + json.dumps(name)))
    if email:
        out.append(run('git config user.email ' + json.dumps(email)))
    return "\n".join(out)
def f_main():
    name = ''
    email = ''
    print(git_config_user(name, email))

if __name__ == '__main__':
    f_main()
