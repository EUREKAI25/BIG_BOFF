# file: git_push.py
""" Push current branch """
from utils_run import run
def git_push(remote, branch, force_with_lease, force):
    out = []
    cmd = 'git push ' + remote + ' ' + branch
    if force_with_lease:
        cmd = 'git push --force-with-lease ' + remote + ' ' + branch
    elif force:
        cmd = 'git push --force ' + remote + ' ' + branch
    out.append(run(cmd))
    return "\n".join(out)
def f_main():
    remote = ''
    branch = ''
    force_with_lease = True
    force = True
    print(git_push(remote, branch, force_with_lease, force))

if __name__ == '__main__':
    f_main()
