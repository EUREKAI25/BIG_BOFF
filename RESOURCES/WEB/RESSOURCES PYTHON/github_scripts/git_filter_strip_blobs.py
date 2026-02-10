# file: git_filter_strip_blobs.py
""" Remove blobs bigger than threshold """
from utils_run import run
def git_filter_strip_blobs(threshold):
    cmd = 'bash -lc "git filter-repo --force --strip-blobs-bigger-than ' + threshold + '"'
    return run(cmd)
def f_main():
    threshold = ''
    print(git_filter_strip_blobs(threshold))

if __name__ == '__main__':
    f_main()
