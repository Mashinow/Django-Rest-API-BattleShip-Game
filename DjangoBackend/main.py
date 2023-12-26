import os
import subprocess


def run_server():
    venv_python = os.path.join(os.getcwd(), 'venv', 'Scripts', 'python')
    coolsite_dir = os.path.join(os.getcwd(), 'coolsite')
    os.chdir(coolsite_dir)
    try:
        subprocess.run([venv_python, "manage.py", "runserver"])
    except KeyboardInterrupt:
        print("Server was stopped by user.")


if __name__ == '__main__':
    run_server()