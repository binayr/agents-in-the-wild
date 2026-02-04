import os
import json
import time

from langchain_core.prompts import ChatPromptTemplate
from agents.element.SchemaAgent import schema_agent


def read_sp(path):
    """
    Reads a stored procedure file from the specified path.

    Args:
        path (str): Path to the stored procedure file

    Returns:
        dict: Dictionary containing the name and content of the stored procedure
    """
    sp = read_sql_file(f"../source/StoredProcedure/{path}")
    tmp = {
        "name": path,
        "content": str(sp)
    }

    return tmp

def save_to_json(filename, data, mode='w'):
    """
    Saves data to a JSON file.

    Args:
        filename (str): Path to the output JSON file
        data (dict/list): Data to be saved as JSON
        mode (str): File open mode ('w' for write, 'a' for append)
    """
    with open(filename, mode) as f:
        json.dump(data, f, indent=4)
        f.write('\n')

def find_from_json(filename, key=None, value=None):
    """
    Retrieves data from a JSON file, with optional filtering by key-value.

    Args:
        filename (str): Path to the JSON file
        key (str, optional): Key to search for in the JSON objects
        value (str, optional): Value to match against the specified key

    Returns:
        dict/list: All data if no key/value provided, or matching object if found
    """
    logger.debug(f"Reading {filename} for key: {key} and value: {value}")
    with open(filename, 'r') as f:
        data = json.loads(f.read())

    if not key and not value:
            return data
    elif key and not value:
        logger.debug(f"Reading {filename} for key: {key}")

        if isinstance(data, dict):
            return data.get(key)
        elif isinstance(data, list):
            for i in data:
                if i.get(key):
                    return i
            else:
                return None
        else:
            return None
    else:
        logger.debug(f"Reading {filename} for key: {key} and value: {value}")
        for i in data:
            if i.get(key).lower() == value.lower():
                return i
        else:
            return None

def read_sql_file(file_path):
    """
    Attempt to read a SQL file with multiple encodings to handle special characters.

    Args:
        file_path: Path to the SQL file

    Returns:
        The content of the file if successful, or an error message
    """
    # List of encodings to try in order of likelihood
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'utf-16', 'utf-16-le', 'utf-16-be']

    # First, try to detect BOM to identify UTF-16 encoded files
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(4)
            # Check for UTF-16 BOM markers
            if raw_data.startswith(b'\xff\xfe') or raw_data.startswith(b'\xfe\xff'):
                with open(file_path, 'r', encoding='utf-16') as f:
                    content = f.read()
                    logger.info(f"Successfully read file using UTF-16 encoding (detected BOM).")
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
                logger.info(f"Successfully read file using {encoding} encoding.")
                return content
        except UnicodeDecodeError:
            logger.info(f"Failed to read with {encoding} encoding, trying next...")
            continue
        except Exception as e:
            return f"Error: {e}"

    # If all encodings failed, try binary mode and replace null bytes
    try:
        with open(file_path, 'rb') as f:
            binary_content = f.read()
            # Remove null bytes and attempt to decode
            cleaned_content = binary_content.replace(b'\x00', b'')
            content = cleaned_content.decode('utf-8', errors='replace')
            logger.info("Used fallback: binary read with null byte removal")
            return content
    except Exception as e:
        return f"Error: Unable to read file with any encoding: {e}"


def json_to_dict(json_data):
    """
    Extracts a dictionary from a JSON string with error handling.

    Args:
        json_data: JSON string containing dependencies data

    Returns:
        A dictionary containing the parsed dependencies or an empty dict if parsing fails
    """
    try:
        # Check if the input is already a dictionary
        if isinstance(json_data, dict):
            return json_data

        # Try to parse the JSON string
        import json
        import re

        # Sometimes JSON strings might have markdown formatting or code blocks
        # Try to extract the JSON content if it's inside code blocks
        json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', json_data)
        if json_match:
            clean_json = json_match.group(1)
            return json.loads(clean_json)

        # If no code blocks, try parsing the string directly
        return json.loads(json_data)

    except Exception as e:
        logger.info(f"Error extracting dependencies dictionary: {e}")
        return {}


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


class EntityCreator:
    """
    A class to convert SQL schema definitions to Java entity classes.

    This class reads all SQL schema files from the Schema directory,
    converts each schema to a corresponding Java entity class using an LLM,
    and stores the generated entities in both files and a metadata JSON.
    """

    def __init__(self, content):
        """
        Initialize the EntityCreator with a prompt template for conversion.

        Args:
            content: Additional content or configuration (currently unused)
        """
        self.schemas = []

    def read_all_schemas(self):
        """
        Read all SQL schema files from the source directory.

        Scans the Schema directory for .sql files and loads their contents
        into the schemas list, with each schema represented as a dictionary.
        """
        schemas = os.listdir(f"../source/Schema/")
        names = [f for f in schemas if f.endswith(".sql")]
        logger.info(names)

        schemas = []
        for name in names:
            sp = read_sql_file(f"../source/Schema/{name}")
            tmp = {
                "schema_name": name,
                "schema": str(sp)
            }
            schemas.append(tmp)

        logger.info(f"Schema text length: {len(schemas)}")
        self.schemas = schemas


    def prepare_output_folders(self):
        """
        Create necessary output directories if they don't exist.
        """
        # Create the destination folders
        if not os.path.exists(f"../out/entities/"):
            os.makedirs(f"../out/entities/")

    def convert_schema_to_entity(self, sc):
        """
        Convert a single SQL schema to a Java entity class.

        Uses the LangChain pipeline with the converter agent to transform
        SQL schema definitions into equivalent Java entity classes.

        Args:
            sc (dict): Dictionary containing schema_name and schema content

        Returns:
            tuple: (schema_name, filename, content) or (schema_name, None, None) on error
        """
        try:
            config = {"configurable": {"thread_id": int(time.time())}}
            response = schema_agent.invoke({
                "source": "SQL schema",
                "target": "Java springboot entity",
                "schema_name": sc["schema_name"],
                "schema": sc["schema"]
            }, config)

            filename = sc["schema_name"].replace(".sql", ".java")

            if os.path.exists(f"../out/entities/{filename}"):
                os.remove(f"../out/entities/{filename}")

            logger.info(f"Exporting {filename}")
            with open(f"../out/entities/{filename}", "w") as f:
                f.write(response["messages"][-1].content)

            return sc["schema_name"], filename, response["messages"][-1].content
        except Exception as e:
            logger.info(f"Error processing {sc['schema_name']}: {e}")
            return sc["schema_name"], None, None

    def create_entities(self):
        """
        Convert all loaded schemas to entities and save them to metadata.

        Process each schema in the schemas list, convert it to a Java entity,
        and store the results in a metadata JSON file for later reference.
        """
        entities = []

        for sc in self.schemas:
            schema_name, filename, response = self.convert_schema_to_entity(sc)
            if filename is not None:
                entities.append({
                    "schema_name": schema_name,
                    "entity_name": filename,
                    "entity": response
                })

        save_to_json(f"../metadata/entities.json", entities, mode='w')

    def run(self):
        """
        Execute the complete entity creation workflow.

        This method orchestrates the entire process:
        1. Prepare output directories
        2. Read all SQL schema files
        3. Convert schemas to Java entities and save metadata
        """
        self.prepare_output_folders()
        self.read_all_schemas()
        self.create_entities()


class JavaFunctionCreator:
    """
    A class to convert SQL functions to Java utility functions.

    This class reads all SQL function files from the Function directory,
    converts each function to Java code using an LLM, and stores the
    generated functions in both files and a metadata JSON.
    """

    def __init__(self, content):
        """
        Initialize the JavaFunctionCreator with a prompt template for conversion.

        Args:
            content: Additional content or configuration (currently unused)
        """
        self.functions = []

    def read_all_functions(self):
        """
        Read all SQL function files from the source directory.

        Scans the Function directory for .sql files and loads their contents
        into the functions list, with each function represented as a dictionary.
        """
        functions = os.listdir(f"../source/Function/")
        names = [f for f in functions if f.endswith(".sql")]
        logger.info(names)

        functions = []
        for name in names:
            sp = read_sql_file(f"../source/Function/{name}")
            tmp = {
                "function_name": name,
                "function": str(sp)
            }
            functions.append(tmp)

        logger.info(f"function text length: {len(functions)}")
        self.functions = functions


    def prepare_output_folders(self):
        """
        Create necessary output directories if they don't exist.
        """
        # Create the destination folders
        if not os.path.exists(f"../out/functions/"):
            os.makedirs(f"../out/functions/")

    def convert_schema_to_entity(self, sc):
        """
        Convert a single SQL function to a Java method.

        Uses the LangChain pipeline with the converter agent to transform
        SQL functions into equivalent Java methods.

        Args:
            sc (dict): Dictionary containing function_name and function content

        Returns:
            tuple: (function_name, filename, content) or (function_name, None, None) on error
        """
        try:
            config = {"configurable": {"thread_id": int(time.time())}}
            response = schema_agent.invoke({
                "source": "SQL functions",
                "target": "Java springboot utility",
                "schema_name": sc["function_name"],
                "schema": sc["function"]
            }, config)

            filename = sc["function_name"].replace(".sql", ".java")

            if os.path.exists(f"../out/functions/{filename}"):
                os.remove(f"../out/functions/{filename}")

            logger.info(f"Exporting {filename}")
            with open(f"../out/functions/{filename}", "w") as f:
                f.write(response["messages"][-1].content)

            return sc["function_name"], filename, response["messages"][-1].content
        except Exception as e:
            logger.info(f"Error processing {filename}: {e}")
            return sc["function_name"], None, None

    def create_functions(self):
        """
        Convert all loaded SQL functions to Java methods and save them to metadata.

        Process each function in the functions list, convert it to Java code,
        and store the results in a metadata JSON file for later reference.
        """
        functions = []

        for sc in self.functions:
            function_name, filename, response = self.convert_schema_to_entity(sc)
            if filename is not None:
                functions.append({
                    "function_name": function_name,
                    "java_function_name": filename,
                    "java_function": response
                })

        save_to_json(f"../metadata/functions.json", functions, mode='w')

    def run(self):
        """
        Execute the complete function conversion workflow.

        This method orchestrates the entire process:
        1. Prepare output directories
        2. Read all SQL function files
        3. Convert functions to Java code and save metadata
        """
        self.prepare_output_folders()
        self.read_all_functions()
        self.create_functions()

class TriggerCreator:
    def __init__(self, content):
        self.pt = ChatPromptTemplate([
            ("system", "You are a SQL and Java Springboot expert, read attached SQL Trigger and generate corresponding springboot utility to use. Genereate only java code and noting else."),
            ("user", "{trigger_name}\n\n{trigger}")
        ])
        self.triggers = []

    def read_all_triggers(self):
        triggers = os.listdir(f"../source/Trigger/")
        names = [f for f in triggers if f.endswith(".sql")]
        logger.info(names)

        triggers = []
        for name in names:
            sp = read_sql_file(f"../source/Trigger/{name}")
            tmp = {
                "trigger_name": name,
                "trigger": str(sp)
            }
            triggers.append(tmp)

        logger.info(f"Schema text length: {len(triggers)}")
        self.triggers = triggers


    def prepare_output_folders(self):
        # Create the destination folders
        if not os.path.exists(f"../out/triggers/"):
            os.makedirs(f"../out/triggers/")

    def convert_schema_to_entity(self, sc):
        try:
            config = {"configurable": {"thread_id": int(time.time())}}
            response = schema_agent.invoke({
                "source": "SQL triggers",
                "target": "Java springboot utility",
                "schema_name": sc["trigger_name"],
                "schema": sc["trigger"]
            }, config)

            filename = sc["trigger_name"].replace(".sql", ".java")

            if os.path.exists(f"../out/triggers/{filename}"):
                os.remove(f"../out/triggers/{filename}")

            logger.info(f"Exporting {filename}")
            with open(f"../out/triggers/{filename}", "w") as f:
                f.write(response["messages"][-1].content)

            return sc["trigger_name"], filename, response["messages"][-1].content
        except Exception as e:
            logger.info(f"Error processing {filename}: {e}")
            return sc["trigger_name"], None, None

    def create_triggers(self):
        triggers = []

        for sc in self.schemas:
            trigger_name, filename, response = self.convert_schema_to_entity(sc)
            if filename is not None:
                triggers.append({
                    "trigger_name": trigger_name,
                    "java_function_name": filename,
                    "java_function": response
                })

        save_to_json(f"../metadata/triggers.json", triggers, mode='w')

    def run(self):
        self.prepare_output_folders()
        self.read_all_triggers()
        self.create_triggers()
