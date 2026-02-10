
# file: utils_run.py
import subprocess, shlex

def run(cmd, cwd=None, env=None):
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out, _ = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(out.strip())
    return out.strip()
