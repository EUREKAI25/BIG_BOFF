# file: git_rebase_onto.py
""" Rebase branch onto another """
from utils_run import run
def git_rebase_onto(branch, onto, remote):
    out = []
    out.append(run('git fetch ' + remote + ' --prune'))
    out.append(run('git checkout ' + branch))
    out.append(run('git rebase ' + onto))
    return "\n".join(out)
def f_main():
    branch = ''
    onto = ''
    remote = ''
    print(git_rebase_onto(branch, onto, remote))

if __name__ == '__main__':
    f_main()
