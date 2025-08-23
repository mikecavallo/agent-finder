import os
import aiofiles

async def save_file(content: bytes, filename: str, directory: str) -> str:
    """Saves binary content to a specified file within a directory."""
    full_directory_path = os.path.join('data', directory)
    os.makedirs(full_directory_path, exist_ok=True)
    
    file_path = os.path.join(full_directory_path, filename)
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        return file_path
    except Exception as e:
        print(f"Error saving file {filename} to {full_directory_path}: {e}")
        return None

async def save_text_file(content: str, filename: str, directory: str) -> str:
    """Saves text content to a specified file within a directory."""
    full_directory_path = os.path.join('data', directory)
    os.makedirs(full_directory_path, exist_ok=True)
    
    file_path = os.path.join(full_directory_path, filename)
    
    try:
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(content)
        return file_path
    except Exception as e:
        print(f"Error saving text file {filename} to {full_directory_path}: {e}")
        return None
