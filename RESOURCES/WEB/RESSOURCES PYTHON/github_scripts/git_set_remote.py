# file: git_set_remote.py
""" Add or update origin remote """
from utils_run import run
def git_set_remote(url, push_default):
    out = []
    if url:
        try:
            out.append(run('git remote set-url origin ' + url))
        except Exception:
            out.append(run('git remote add origin ' + url))
    if push_default:
        out.append(run('git config push.default ' + push_default))
    return "\n".join(out)
def f_main():
    url = ''
    push_default = 'simple'
    print(git_set_remote(url, push_default))

if __name__ == '__main__':
    f_main()
