# file: git_setup_ssh_config.py
""" Write minimal SSH config for GitHub """
from utils_run import run
def git_setup_ssh_config(identity_file):
    import os
    cfg = 'Host github.com\n  HostName github.com\n  User git\n  IdentityFile ' + identity_file + '\n  AddKeysToAgent yes\n  UseKeychain yes\n'
    path = os.path.expanduser('~/.ssh/config')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,'w') as f:
        f.write(cfg)
    return 'ok'
def f_main():
    identity_file = ''
    print(git_setup_ssh_config(identity_file))

if __name__ == '__main__':
    f_main()
