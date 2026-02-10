# file: git_status_verbose.py
""" Verbose status including ignored """
from utils_run import run
def git_status_verbose():
    return run('git status --ignored -vv')
def f_main():
    print(git_status_verbose())

if __name__ == '__main__':
    f_main()
