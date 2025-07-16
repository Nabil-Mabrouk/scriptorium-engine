import os

def get_project_info(folder_paths: list[str], target_extensions: list[str]) -> str:
    """
    Takes a list of folder paths and returns a string containing:
    1. The filesystem structure of each folder.
    2. The name and full text content of each file with a specified extension
       (including files in subfolders).

    Args:
        folder_paths (list[str]): A list of paths to the folders to analyze.
        target_extensions (list[str]): A list of file extensions to include 
                                       (e.g., ['.py', '.css', '.vue']).

    Returns:
        str: A multi-line string holding the filesystem structure and file contents.
             Returns an error message for any path that is not a valid directory.
    """
    output_lines = []
    
    # Process each folder provided in the list
    for folder_path in folder_paths:
        if not os.path.isdir(folder_path):
            output_lines.append(f"\n--- ERROR ---")
            output_lines.append(f"'{folder_path}' is not a valid directory or does not exist.")
            continue # Skip to the next folder

        absolute_folder_path = os.path.abspath(folder_path)

        # --- Section 1: Filesystem Structure ---
        output_lines.append(f"\n--- Filesystem Structure for '{os.path.basename(absolute_folder_path)}' ---")
        output_lines.append(f"{os.path.basename(absolute_folder_path)}/")

        # Use os.walk to traverse the directory tree
        for root, dirs, files in os.walk(absolute_folder_path):
            # To prevent os.walk from going into node_modules, we modify the dirs list in-place.
            if 'node_modules' in dirs:
                dirs.remove('node_modules')

            relative_path = os.path.relpath(root, absolute_folder_path)
            current_depth = len(relative_path.split(os.sep)) if relative_path != '.' else 0
            indent_level = "    " * (current_depth + 1)

            # Sort dirs and files for consistent output
            dirs.sort()
            files.sort()

            for dname in dirs:
                output_lines.append(f"{indent_level}{dname}/")
            for fname in files:
                output_lines.append(f"{indent_level}{fname}")

        # --- Section 2: File Contents ---
        output_lines.append(f"\n--- File Contents for '{os.path.basename(absolute_folder_path)}' ({', '.join(target_extensions)}) ---")
        found_target_files = False

        for root, dirs, files in os.walk(absolute_folder_path):
            # Also ignore node_modules here to be consistent and avoid processing its files.
            if 'node_modules' in dirs:
                dirs.remove('node_modules')

            files.sort() # Sort for consistent order
            for filename in files:
                # Check if the file has one of the target extensions
                if any(filename.endswith(ext) for ext in target_extensions):
                    found_target_files = True
                    full_file_path = os.path.join(root, filename)
                    # Use the absolute folder path as the base for the relative path
                    relative_file_path = os.path.relpath(full_file_path, os.path.dirname(absolute_folder_path))
                    output_lines.append(f"\n--- FILE: {relative_file_path} ---")
                    try:
                        # Attempt to read the file with UTF-8 encoding
                        with open(full_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            output_lines.append(content)
                    except Exception as e:
                        output_lines.append(f"    <ERROR READING FILE: {e}>")

        if not found_target_files:
            output_lines.append(f"No files with the specified extensions found in '{os.path.basename(absolute_folder_path)}'.")

    return "\n".join(output_lines)

# --- Main Execution Block ---
if __name__ == "__main__":
    # --- Analysis Configuration ---
    # Define the folders to analyze.
    # IMPORTANT: This script assumes these folders exist in the same directory where the script is run.
    folders_to_analyze = ["src", "frontend"]
    
    # Define the file types to track
    target_extensions_to_find = ['.py', '.css', '.vue', '.json', '.ts']
    
    # Define the output file name
    output_filename = "project_analysis_report.txt"

    print(f"Analyzing folders: {', '.join(folders_to_analyze)}...")
    
    # Get the combined information string
    info_string = get_project_info(folders_to_analyze, target_extensions_to_find)

    # Write the output string to a file
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(info_string)
        print(f"Analysis complete. Report written to '{output_filename}'")
    except IOError as e:
        print(f"Error writing to file '{output_filename}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")