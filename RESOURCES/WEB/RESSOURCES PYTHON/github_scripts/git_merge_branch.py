# file: git_merge_branch.py
""" Merge source into target """
from utils_run import run
def git_merge_branch(source, target, remote):
    out = []
    out.append(run('git fetch ' + remote + ' --prune'))
    out.append(run('git checkout ' + target))
    out.append(run('git merge --no-ff ' + source))
    return "\n".join(out)
def f_main():
    source = ''
    target = ''
    remote = ''
    print(git_merge_branch(source, target, remote))

if __name__ == '__main__':
    f_main()
