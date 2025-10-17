import os
import shutil
import subprocess
import sys


def clean_venv():
    # Удаление __pycache__ и .pyc файлов
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                dir_path = os.path.join(root, dir_name)
                print(f"Удаление {dir_path}")
                shutil.rmtree(dir_path)

        for file_name in files:
            if file_name.endswith('.pyc'):
                file_path = os.path.join(root, file_name)
                print(f"Удаление {file_path}")
                os.remove(file_path)

    # Очистка кэша pip
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'cache', 'purge'],
                       check=True)
        print("Кэш pip очищен")
    except subprocess.CalledProcessError:
        print("Не удалось очистить кэш pip")


if __name__ == "__main__":
    clean_venv()