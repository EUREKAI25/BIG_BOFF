# file: git_show_large_files.py
""" List blobs >100MB with paths """
from utils_run import run
def git_show_large_files():
    import subprocess, shlex
    p1 = subprocess.Popen(shlex.split("git rev-list --objects --all"), stdout=subprocess.PIPE, text=True)
    p2 = subprocess.Popen(shlex.split("git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)'"), stdin=p1.stdout, stdout=subprocess.PIPE, text=True, shell=False)
    p3 = subprocess.Popen(["awk", "$1==\"blob\"{size=$3; path=\"\"; for(i=4;i<=NF;i++){path=path (i==4?\"\":\" \") $i} if(size>100000000) print size \"\\t\" path}"], stdin=p2.stdout, stdout=subprocess.PIPE, text=True)
    out, _ = p3.communicate()
    print(out.strip())
    return out.strip()
def f_main():
    print(git_show_large_files())

if __name__ == '__main__':
    f_main()
