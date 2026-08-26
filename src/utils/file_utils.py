import os

def cleanup_temp_file(file_path):
    """Безопасное удаление временного файла"""
    if file_path and os.path.exists(file_path):
        try:
            os.unlink(file_path)
        except Exception as e:
            # Просто игнорируем ошибку удаления
            pass
