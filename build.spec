# build.py
import PyInstaller.__main__
import os

# Path to your main script
script = "Notebook.py"

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    script,
    '--name=NotebookApp',
    '--windowed',  # Don't show console
    '--onefile',   # Single executable
    '--add-data', f'Adeliz-Regular.otf;.',  # For Windows
    '--add-data', f'Adeliz-Regular.ttf;.',
    '--add-data', f'flip.mp3;.',
    '--icon=notebook.ico',  # Optional: add an icon
    '--clean',
    '--noconsole',
])