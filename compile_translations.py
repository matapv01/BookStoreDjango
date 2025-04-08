"""
Script to compile .po files to .mo files using polib.
This is an alternative to Django's compilemessages command,
which requires gettext tools to be installed.
"""
import os
import sys
try:
    import polib
except ImportError:
    print("The polib library is not installed. Installing it now...")
    os.system(f"{sys.executable} -m pip install polib")
    import polib

def compile_po_files():
    """Compile all .po files to .mo files in the locale directory."""
    print("Compiling translation files...")
    locale_dir = 'locale'
    
    for root, dirs, files in os.walk(locale_dir):
        for filename in files:
            if filename.endswith('.po'):
                po_path = os.path.join(root, filename)
                mo_path = po_path.replace('.po', '.mo')
                
                print(f"Compiling {po_path} to {mo_path}")
                try:
                    po_file = polib.pofile(po_path)
                    po_file.save_as_mofile(mo_path)
                    print(f"Successfully compiled {po_path}")
                except Exception as e:
                    print(f"Error compiling {po_path}: {e}")

if __name__ == '__main__':
    compile_po_files()
    print("All translation files compiled successfully!")
