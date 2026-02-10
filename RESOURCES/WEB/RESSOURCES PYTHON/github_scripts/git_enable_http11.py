# file: git_enable_http11.py
""" Force Git HTTP/1.1 and larger postBuffer """
from utils_run import run
def git_enable_http11():
    out = []
    out.append(run('git config --global http.version HTTP/1.1'))
    out.append(run('git config --global http.postBuffer 524288000'))
    return "\n".join(out)
def f_main():
    print(git_enable_http11())

if __name__ == '__main__':
    f_main()
