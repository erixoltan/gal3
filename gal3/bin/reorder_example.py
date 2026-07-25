import re

def reorder_ed_script_by_line(script_string):
    """
    Reorders command blocks in an ed script string based on the line number they target.

    Commands are sorted from highest target line number to lowest.
    '$' is treated as the highest line number. Commands targeting '.' or
    with no address are given the lowest sort priority (-1).
    Multi-line commands (i, a, c) are kept together with their text and dot.
    Non-edit commands (H, w, q, f) and lines that cannot be parsed are
    preserved at the start (H) or end (others) in their relative order.

    Args:
        script_string (str): The ed script content as a single string.

    Returns:
        str: The reordered ed script content as a single string, ending with newline.
    """
    lines = script_string.strip().split('\n')
    command_blocks = []  # Stores tuples: (sort_key, list_of_lines_in_block)
    preserved_start = [] # For H
    preserved_end = []   # For w, q, f and unparsed/low-priority lines/blocks

    i = 0
    while i < len(lines):
        original_line = lines[i]
        stripped_line = original_line.strip()

        if not stripped_line:  # Skip empty lines if desired, or preserve them
            # To preserve empty lines, add them to preserved_end or handle contextually
            # For simplicity here, we'll skip processing them directly
            i += 1
            continue

        # --- Handle Preserved Commands (non-sortable by line number) ---
        if stripped_line == 'H':
            preserved_start.append(original_line)
            i += 1
            continue
        # Common commands usually placed at the end
        if stripped_line in ['w', 'q', 'f']:
            preserved_end.append(original_line)
            i += 1
            continue

        # --- Attempt to Parse Address and Edit Command ---
        # Regex: Optional Address (numeric, range, $, %, .) then Command (letter)
        # This regex tries to capture the address part and the command letter.
        regex = re.compile(r"^\s*(\%|\$|\.|\d+(?:,(?:\d+|\$|\.))?)?\s*([a-z])", re.IGNORECASE)
        match = regex.match(stripped_line)

        current_block_lines = [original_line] # Start block with the current line
        # Default sort key: 0. Will be adjusted if address is parsed.
        # -1 specifically for '.' or no address (lowest numeric priority)
        # float('inf') for '$' or '%' (highest priority)
        sort_key = 0
        command_char = None

        if match:
            address_str = match.group(1)
            command_char = match.group(2).lower() # Use lowercase command char

            # Determine Sort Key based on the address
            if address_str:
                address_str = address_str.strip()
                try:
                    if address_str == '%' or address_str == '$':
                        sort_key = float('inf')
                    elif address_str == '.':
                        sort_key = -1 # Lowest numeric priority
                    elif ',' in address_str:
                        start_str, end_str = address_str.split(',', 1)
                        # Sort range based on the highest line number involved
                        if end_str == '$': sort_key = float('inf')
                        elif end_str == '.':
                             # Range ending in '.'. Sort based on start line? Or low?
                             # Let's sort based on the start line number.
                             sort_key = int(start_str) if start_str.isdigit() else -1
                        else:
                             sort_key = int(end_str) # Sort range by end line number
                    elif address_str.isdigit():
                         sort_key = int(address_str)
                    else:
                         sort_key = 0 # Unrecognized address format, treat as low priority
                except ValueError:
                    print(f"Warning: Could not parse line number in address '{address_str}' in line '{original_line}'")
                    sort_key = 0 # Treat as low priority on parse error
            else:
                # Command without address implies '.' (current line)
                sort_key = -1 # Lowest numeric priority

            # --- Handle multi-line commands (i, a, c) ---
            if command_char in ['a', 'c', 'i']:
                i += 1
                while i < len(lines):
                    text_line = lines[i]
                    current_block_lines.append(text_line)
                    # Check for exact match of termination line
                    if text_line == '.':
                        break
                    i += 1
                # Safety check for missing terminator
                if i == len(lines) or lines[i] != '.':
                   print(f"Warning: Multi-line command starting '{stripped_line}' seems missing terminator '.'")

            # --- Store the identified command block ---
            command_blocks.append((sort_key, current_block_lines))

        else:
            # Line didn't match regex (e.g., comments, complex 's' commands without clear line target)
            # Add it to the preserved end section, before w, q etc.
            # We preserve its original content entirely.
            preserved_end.insert(0, original_line) # insert at beginning of 'end' list

        i += 1 # Move to the next line for processing


    # --- Sort the identified command blocks ---
    # Sort by sort_key (max line number) descending.
    command_blocks.sort(key=lambda item: item[0], reverse=True)

    # --- Reconstruct the script ---
    output_lines = []
    output_lines.extend(preserved_start) # Add H if present

    # Add the sorted command blocks (highest line number first)
    for _, block_lines in command_blocks:
        output_lines.extend(block_lines)

    # Add the preserved end commands (w, q, f) and any unparsed/unhandled lines
    output_lines.extend(preserved_end)

    # Ensure the script ends with a newline character for ed
    return "\n".join(output_lines) + "\n"


# --- Example Usage ---
input_script = """
H
10i
Text for line 10 insertion.
.
3,5c
Replacement text
for lines 3 through 5.
.
20d
$a
Append text at the end.
Last append line.
.
1,2d
# This is a comment line, should be preserved at end
.s/old/new/g
w
f somefile.txt
q
"""

print("--- Original Script ---")
print(input_script.strip())

reordered_script = reorder_ed_script_by_line(input_script)

print("\n--- Reordered Script ---")
print(reordered_script.strip())

# Example 2
input_script_2 = """
5i
Insertion before 5
.
2d
1a
Append after 1
.
w
q
"""

print("\n--- Original Script 2 ---")
print(input_script_2.strip())

reordered_script_2 = reorder_ed_script_by_line(input_script_2)

print("\n--- Reordered Script 2 ---")
print(reordered_script_2.strip())
