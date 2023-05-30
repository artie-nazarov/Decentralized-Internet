import os
import requests

DOCKERFILE_PATH = '../'
out_file = "out.log"
err_file = "err.log"

def start_cluster():
    # build kvs image
    if os.system(f'docker build -t kvs {DOCKERFILE_PATH} > /dev/null') != 0:
        raise Exception("Docker build failed")
    
    # start cluster, redirect logs to files
    os.system(f'docker compose -f docker-compose-partition-test.yaml up --wait > {out_file} 2> {err_file}')

def stop_cluster():
    if os.system('docker compose -f docker-compose-partition-test.yaml down') != 0:
        raise Exception("Failed to stop and delete containers")
    os.system(f"rm -r {out_file} {err_file}")

def run_tests():
    # call test function in partition-test-run.py
    os.system(f'python partition-test-run.py')

def main():
    start_cluster()
    run_tests()
    stop_cluster()

if __name__ == '__main__':
    main()