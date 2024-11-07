import PyInstaller.__main__
import os
import shutil

def build_exe():
    # Clean previous builds
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    print("Building JewelryNest executable...")
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths using os.path.join for cross-platform compatibility
    templates_path = os.path.join(current_dir, 'templates')
    static_path = os.path.join(current_dir, 'static')
    backend_path = os.path.join(current_dir, 'Backend')
    
    PyInstaller.__main__.run([
        'app.py',
        '--name=JewelryNest',
        '--onefile',
        '--clean',
        f'--add-data={templates_path};templates',
        f'--add-data={static_path};static',
        f'--add-data={os.path.join(backend_path, "ca.pem")};Backend',
        '--hidden-import=flask',
        '--hidden-import=flask_mysqldb',
        '--hidden-import=MySQLdb',
        '--hidden-import=cryptography',
        '--noconfirm',
        '--console'  # Remove this line if you don't want a console window
    ])
    
    # Create distribution folder
    dist_folder = 'JewelryNest_Distribution'
    if os.path.exists(dist_folder):
        shutil.rmtree(dist_folder)
    os.makedirs(dist_folder)
    
    # Copy executable
    shutil.copy(os.path.join('dist', 'JewelryNest.exe'), dist_folder)
    
    print("\nBuild complete! Distribution package created in:", dist_folder)
    print("\nPlease test the executable before distribution.")

if __name__ == "__main__":
    build_exe()