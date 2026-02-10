# file: git_add_commit.py
""" Stage all and commit with message """
from utils_run import run
def git_add_commit(message):
    import json
    out = []
    out.append(run('git add -A'))
    out.append(run('git commit -m ' + json.dumps(message)))
    return "\n".join(out)
def f_main():
    message = ''
    print(git_add_commit(message))

if __name__ == '__main__':
    f_main()
