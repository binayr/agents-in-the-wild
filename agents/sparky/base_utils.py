import logging
import os


logger = logging.getLogger(__name__)


def read_file_content(file_path):
    """
    Read file content with robust encoding detection.
    Uses the same encoding logic as read_sql_file but for any file type.

    Args:
        file_path (str): Path to the file to read

    Returns:
        str: File content as string, or error message if failed
    """
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'utf-16', 'utf-16-le', 'utf-16-be']

    # First, try to detect BOM to identify UTF-16 encoded files
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(4)
            # Check for UTF-16 BOM markers
            if raw_data.startswith(b'\xff\xfe') or raw_data.startswith(b'\xfe\xff'):
                with open(file_path, 'r', encoding='utf-16') as f:
                    content = f.read()
                    logger.info(f"✅ Successfully read {file_path} using UTF-16 encoding (detected BOM).")
                    return content
    except Exception:
        pass  # Continue with regular approach if BOM detection fails

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                # Check if content contains null bytes which indicate wrong encoding
                if '\x00' in content:
                    logger.info(f"Found null bytes with {encoding}, trying next...")
                    continue
                logger.info(f"Successfully read {file_path} using {encoding} encoding.")
                return content
        except UnicodeDecodeError:
            logger.info(f"Failed to read {file_path} with {encoding} encoding, trying next...")
            continue
        except Exception as e:
            return f"Error reading {file_path}: {e}"

    # If all encodings failed, try binary mode and replace null bytes
    try:
        with open(file_path, 'rb') as f:
            binary_content = f.read()
            # Remove null bytes and attempt to decode
            cleaned_content = binary_content.replace(b'\x00', b'')
            content = cleaned_content.decode('utf-8', errors='replace')
            logger.info(f"Used fallback for {file_path}: binary read with null byte removal")
            return content
    except Exception as e:
        return f"Error: Unable to read {file_path} with any encoding: {e}"


def remove_comments(content, file_extension):
    """
    Remove comments from file content based on file type.

    Args:
        content (str): File content as string
        file_extension (str): File extension (e.g., '.sql', '.py')

    Returns:
        str: Content with comments removed
    """
    if not content:
        return content

    lines = content.split('\n')
    cleaned_lines = []

    # Define comment patterns based on file extension
    comment_patterns = {
        '.sql': '--',
        '.py': '#',
        '.java': '//',
        '.js': '//',
        '.ts': '//',
        '.c': '//',
        '.cpp': '//',
        '.h': '//',
        '.hpp': '//',
        '.cs': '//',
        '.php': '//',
        '.rb': '#',
        '.sh': '#',
        '.bash': '#',
        '.zsh': '#',
        '.r': '#',
        '.pl': '#',
        '.pm': '#'
    }

    comment_start = comment_patterns.get(file_extension.lower())

    if not comment_start:
        # If we don't recognize the file type, return original content
        return content

    for line in lines:
        # Find the position of the comment start
        comment_pos = line.find(comment_start)

        if comment_pos == -1:
            # No comment in this line, keep the entire line
            cleaned_lines.append(line)
        elif comment_pos == 0:
            # Line starts with comment, skip entirely (but keep empty line for structure)
            cleaned_lines.append('')
        else:
            # Comment is inline, keep only the part before the comment
            # But be careful with strings that might contain the comment pattern
            cleaned_line = line[:comment_pos].rstrip()
            cleaned_lines.append(cleaned_line)

    return '\n'.join(cleaned_lines)


def path_to_content_dict(in_path):
    """
    Takes a file path or directory path and returns a dictionary where keys are relative file paths
    and values are file contents as strings with comments removed.

    Args:
        in_path (str): Path to file or directory to process

    Returns:
        dict: Dictionary mapping relative file paths to their string contents (comments removed)
              Returns empty dict if path doesn't exist or on error
    """
    result = {}

    if not os.path.exists(in_path):
        logger.error(f"Path does not exist: {in_path}")
        return result

    try:
        # If it's a file, read it directly
        if os.path.isfile(in_path):
            content = read_file_content(in_path)
            # Remove comments based on file extension
            file_extension = os.path.splitext(in_path)[1]
            # cleaned_content = remove_comments(content, file_extension)
            cleaned_content = content
            # Use the original input path as key for single files
            result[in_path] = cleaned_content
            logger.debug(f"Read file: {in_path} (comments removed)")

        # If it's a directory, walk through all files recursively
        elif os.path.isdir(in_path):
            # Normalize the input path to ensure consistent relative path calculation
            in_path_normalized = os.path.normpath(in_path)

            for root, dirs, files in os.walk(in_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        content = read_file_content(file_path)
                        # Remove comments based on file extension
                        file_extension = os.path.splitext(file)[1]
                        # cleaned_content = remove_comments(content, file_extension)
                        cleaned_content = content

                        # Create relative path from the input directory
                        rel_path = os.path.relpath(file_path, start=os.path.dirname(in_path_normalized) if in_path_normalized != '.' else '.')
                        result[rel_path] = cleaned_content
                        logger.debug(f"Read file: {rel_path} (comments removed)")
                    except Exception as e:
                        logger.error(f"Failed to read file {file_path}: {e}")
                        # Still add the file with an error message using relative path
                        rel_path = os.path.relpath(file_path, start=os.path.dirname(in_path_normalized) if in_path_normalized != '.' else '.')
                        result[rel_path] = f"Error reading file: {e}"

        else:
            logger.error(f"Path is neither file nor directory: {in_path}")

    except Exception as e:
        logger.error(f"Error processing path {in_path}: {e}")

    logger.info(f"✅ Successfully read {len(result)} files from path: {in_path}")
    return result


def read_prompt(prompt_path):
    with open(prompt_path, 'r') as file:
        return file.read()
