# file: git_undo_last_commit.py
""" Undo last commit """
from utils_run import run
def git_undo_last_commit(keep_changes):
    out = []
    if keep_changes:
        out.append(run('git reset --soft HEAD~1'))
    else:
        out.append(run('git reset --hard HEAD~1'))
    return "\n".join(out)
def f_main():
    keep_changes = True
    print(git_undo_last_commit(keep_changes))

if __name__ == '__main__':
    f_main()
