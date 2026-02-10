from backtester import run_from_config

def run(path="config.yaml"):
    return run_from_config(path)

if __name__ == "__main__":
    print(run())
