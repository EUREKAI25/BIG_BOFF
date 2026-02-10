# file: git_lfs_install_track.py
""" Install Git LFS and track patterns """
from utils_run import run
def git_lfs_install_track(track_patterns):
    import json
    out = []
    out.append(run('brew install git-lfs'))
    out.append(run('git lfs install'))
    if track_patterns:
        args = ' '.join([json.dumps(p) for p in track_patterns])
        out.append(run('git lfs track ' + args))
        out.append(run('git add .gitattributes'))
        out.append(run('git commit -m chore_track_via_LFS'))
    return "\n".join(out)
def f_main():
    track_patterns = []
    print(git_lfs_install_track(track_patterns))

if __name__ == '__main__':
    f_main()
