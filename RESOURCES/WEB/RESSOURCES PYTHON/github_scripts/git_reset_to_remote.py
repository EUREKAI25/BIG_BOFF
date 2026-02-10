# file: git_reset_to_remote.py
""" Reset local branch to remote state """
from utils_run import run
def git_reset_to_remote(remote, branch):
    out = []
    out.append(run('git fetch ' + remote + ' --prune'))
    out.append(run('git reset --hard ' + remote + '/' + branch))
    return "\n".join(out)
def f_main():
    remote = ''
    branch = ''
    print(git_reset_to_remote(remote, branch))

if __name__ == '__main__':
    f_main()
