import os
import shutil
import subprocess
import sys

def run_command(command, cwd=None, shell=True):
    """Run a shell command and check for errors"""
    cmd_str = ' '.join(command) if isinstance(command, list) else command
    print(f"Executing: {cmd_str}")
    try:
        subprocess.check_call(command, cwd=cwd, shell=shell)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        sys.exit(1)

def package():
    # Base paths
    project_root = os.getcwd() # Should be D:\...\智能考务系统
    frontend_dir = os.path.join(project_root, 'frontend')

    # Paths for PyInstaller
    spec_file = os.path.join(frontend_dir, 'engine.spec')
    python_dist_dir = os.path.join(frontend_dir, 'python-dist')
    python_build_dir = os.path.join(frontend_dir, 'build-python')
    
    print("=== Step 1: Building Python Backend ===")
    
    # Clean previous Python builds
    if os.path.exists(python_dist_dir):
        print(f"Cleaning {python_dist_dir}...")
        shutil.rmtree(python_dist_dir)
    if os.path.exists(python_build_dir):
        print(f"Cleaning {python_build_dir}...")
        shutil.rmtree(python_build_dir)
    
    # Clean Electron output directory to avoid file lock issues
    release_dir = os.path.join(frontend_dir, 'release_v6')
    if os.path.exists(release_dir):
        print(f"Cleaning Electron output directory: {release_dir}...")
        try:
            shutil.rmtree(release_dir)
        except OSError as e:
            print(f"Warning: Failed to clean release directory. You might need to manually close running instances. Error: {e}")
        
    # Run PyInstaller with specified Anaconda Python
    pyinstaller_cmd = [
        'D:/ANACONDA/envs/exam_scheduler/python.exe', '-m', 'PyInstaller',
        spec_file,
        '--distpath', python_dist_dir,
        '--workpath', python_build_dir,
        '--noconfirm',
        '--clean'
    ]
    run_command(pyinstaller_cmd, cwd=project_root)
    
    print("\n=== Step 2: Building Electron Frontend & Installer ===")
    
    # Run Electron Builder
    # This corresponds to "npm run electron:build"
    # We use 'npm.cmd' for Windows compatibility
    npm_cmd = ['npm.cmd', 'run', 'electron:build']
    run_command(npm_cmd, cwd=frontend_dir)

    print("\n=== Packaging Complete! ===")
    print(f"Installer should be in: {os.path.join(frontend_dir, 'release_v6')}")

if __name__ == '__main__':
    package()
