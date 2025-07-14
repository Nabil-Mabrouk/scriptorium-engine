import os
import shutil # For cleanup in example

def get_folder_info(folder_path: str) -> str:
    """
    Takes a folder path as an argument and returns a string containing:
    1. The folder's filesystem structure.
    2. The name and full text content of each file with extension .py
       (including files in subfolders).

    Args:
        folder_path (str): The path to the folder to analyze.

    Returns:
        str: A multi-line string holding the filesystem structure and .py file contents.
             Returns an error message if the path is not a valid directory.
    """
    if not os.path.isdir(folder_path):
        return f"Error: '{folder_path}' is not a valid directory or does not exist."

    output_lines = []
    absolute_folder_path = os.path.abspath(folder_path)

    # --- Section 1: Filesystem Structure ---
    output_lines.append("--- Filesystem Structure ---")
    output_lines.append(f"{os.path.basename(absolute_folder_path)}/") # Root folder name

    # Use os.walk to traverse the directory tree
    for root, dirs, files in os.walk(absolute_folder_path):
        # Calculate the relative path from the initial folder to the current 'root'
        relative_path = os.path.relpath(root, absolute_folder_path)

        # Determine the indentation level
        # If relative_path is '.', it's the starting folder itself (depth 0)
        # Otherwise, count the number of separators to get depth
        current_depth = len(relative_path.split(os.sep)) if relative_path != '.' else 0

        # Indent everything one level more than the 'root' it belongs to
        # This makes items *inside* a folder indented
        indent_level = "    " * (current_depth + 1)

        # Sort dirs and files for consistent output
        dirs.sort()
        files.sort()

        # Add directories
        for dname in dirs:
            output_lines.append(f"{indent_level}{dname}/")

        # Add files
        for fname in files:
            output_lines.append(f"{indent_level}{fname}")

    # --- Section 2: Python File Contents ---
    output_lines.append("\n--- Python File Contents (.py files) ---")
    found_py_files = False

    for root, _, files in os.walk(absolute_folder_path):
        for filename in files:
            if filename.endswith(".py"):
                found_py_files = True
                full_file_path = os.path.join(root, filename)
                output_lines.append(f"\n--- FILE: {full_file_path} ---")
                try:
                    # Attempt to read the file with UTF-8 encoding
                    # 'errors='ignore'' will skip un-decodable characters
                    with open(full_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        output_lines.append(content)
                except Exception as e:
                    output_lines.append(f"    <ERROR READING FILE: {e}>")

    if not found_py_files:
        output_lines.append("No .py files found in this folder or its subfolders.")

    return "\n".join(output_lines)

# --- Example Usage ---
if __name__ == "__main__":
    # Define the output file name
    output_filename = "folder_analysis_report.txt"

    # Create a dummy folder structure for testing
    test_folder = "src"

    print(f"Analyzing folder: '{test_folder}'...")
    info_string = get_folder_info(test_folder)

    # Write the output string to a file
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(info_string)
        print(f"Analysis complete. Report written to '{output_filename}'")
    except IOError as e:
        print(f"Error writing to file '{output_filename}': {e}")
