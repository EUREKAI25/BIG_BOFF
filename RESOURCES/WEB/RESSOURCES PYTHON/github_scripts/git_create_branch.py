# file: git_create_branch.py
""" Create or reset local branch from remote """
from utils_run import run
def git_create_branch(branch, remote, from_branch):
    out = []
    out.append(run('git fetch ' + remote + ' --prune'))
    if from_branch:
        out.append(run('git checkout -B ' + branch + ' ' + remote + '/' + from_branch))
    else:
        out.append(run('git checkout -b ' + branch))
    return "\n".join(out)
def f_main():
    branch = ''
    remote = ''
    from_branch = ''
    print(git_create_branch(branch, remote, from_branch))

if __name__ == '__main__':
    f_main()
