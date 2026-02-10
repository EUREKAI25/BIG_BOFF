# file: git_stash_save_apply.py
""" Save or apply/pop stash """
from utils_run import run
def git_stash_save_apply(action, message, ref):
    import json
    out = []
    if action == 'save':
        out.append(run('git stash push -u -m ' + json.dumps(message)))
    elif action == 'apply':
        out.append(run('git stash apply ' + (ref or '')))
    elif action == 'pop':
        out.append(run('git stash pop ' + (ref or '')))
    return "\n".join(out)
def f_main():
    action = ''
    message = ''
    ref = ''
    print(git_stash_save_apply(action, message, ref))

if __name__ == '__main__':
    f_main()
