# file: git_init_repo.py
""" Initialize a new git repository """
from utils_run import run
def git_init_repo(path, default_branch, create_readme):
    out = []
    if path:
        import os
        os.makedirs(path, exist_ok=True)
        os.chdir(path)
    out.append(run('git init'))
    if default_branch:
        out.append(run('git checkout -B ' + default_branch))
    if create_readme:
        with open('README.md','w') as f:
            f.write('# Repo\n')
        out.append(run('git add README.md'))
        out.append(run('git commit -m init'))
    return "\n".join(out)
def f_main():
    path = ''
    default_branch = 'main'
    create_readme = True
    print(git_init_repo(path, default_branch, create_readme))

if __name__ == '__main__':
    f_main()
