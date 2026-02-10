# file: git_tag_create_push.py
""" Create tag and optionally push """
from utils_run import run
def git_tag_create_push(name, message, annotated, push, remote):
    import json
    out = []
    if annotated:
        out.append(run('git tag -a ' + name + ' -m ' + json.dumps(message)))
    else:
        out.append(run('git tag ' + name))
    if push:
        out.append(run('git push ' + remote + ' ' + name))
    return "\n".join(out)
def f_main():
    name = ''
    message = ''
    annotated = True
    push = True
    remote = ''
    print(git_tag_create_push(name, message, annotated, push, remote))

if __name__ == '__main__':
    f_main()
