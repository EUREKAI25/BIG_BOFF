# file: git_filter_purge_paths.py
""" Purge given paths from history using git-filter-repo """
from utils_run import run
def git_filter_purge_paths(paths_to_purge):
    out = []
    out.append(run('git add -A'))
    out.append(run('git commit -m checkpoint_before_filter'))
    out.append(run('bash -lc "git for-each-ref --format=delete %(refname) refs/original | git update-ref --stdin"'))
    out.append(run('git reflog expire --expire=now --all'))
    out.append(run('git gc --prune=now'))
    parts = []
    for p in paths_to_purge:
        parts.append("--path '" + p.replace("'","'\\''") + "' --invert-paths")
    cmd = 'bash -lc "git filter-repo --force ' + ' '.join(parts) + '"'
    out.append(run(cmd))
    return "\n".join(out)
def f_main():
    paths_to_purge = []
    print(git_filter_purge_paths(paths_to_purge))

if __name__ == '__main__':
    f_main()
