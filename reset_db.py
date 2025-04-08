import os
import shutil
import subprocess

def reset_database():
    # Delete database file
    if os.path.exists('db.sqlite3'):
        os.remove('db.sqlite3')
        print("Deleted db.sqlite3")

    # Delete all migrations except __init__.py
    migrations_dir = 'main/migrations'
    for file in os.listdir(migrations_dir):
        if file != '__init__.py' and file.endswith('.py'):
            os.remove(os.path.join(migrations_dir, file))
            print(f"Deleted {file}")

    # Make migrations
    subprocess.run(['python', 'manage.py', 'makemigrations'])
    
    # Apply migrations
    subprocess.run(['python', 'manage.py', 'migrate'])

    print("\nDatabase reset complete. You can now create a superuser with:")
    print("python manage.py createsuperuser")

if __name__ == '__main__':
    reset_database()