# file: git_install_filter_repo.py
""" Install git-filter-repo via Homebrew """
from utils_run import run
def git_install_filter_repo():
    try:
        return run('brew install git-filter-repo')
    except RuntimeError as e:
        return str(e)
def f_main():
    print(git_install_filter_repo())

if __name__ == '__main__':
    f_main()
