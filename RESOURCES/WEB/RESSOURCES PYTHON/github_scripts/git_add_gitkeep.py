# file: git_add_gitkeep.py
""" Add .gitkeep files to keep empty directories """
from utils_run import run
def git_add_gitkeep(dirs):
    import os
    added = []
    for d in dirs or []:
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d,'.gitkeep')
        if not os.path.exists(p):
            open(p,'w').close()
            added.append(p)
    if added:
        run('git add ' + ' '.join(['"' + a + '"' for a in added]))
        run('git commit -m chore_add_gitkeep')
    return '\n'.join(added) if added else 'no-op'
def f_main():
    dirs = []
    print(git_add_gitkeep(dirs))

if __name__ == '__main__':
    f_main()
