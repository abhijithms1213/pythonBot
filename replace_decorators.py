import re
import os

files_to_modify = ['execution.py', 'schedule.py', 'db_management.py']

for filepath in files_to_modify:
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r') as f:
        content = f.read()

    if filepath == 'db_management.py':
        # Let's change the global exception handling in dbops to avoid crashing the logic
        original_dbops_except = '''    except Exception as e:
        print(f"[DB ERROR] {operation} → {e}")
        raise'''
        
        replacement_dbops_except = '''    except Exception as e:
        import traceback; traceback.print_exc()
        import logging; logging.error(f"[DB ERROR] {operation} → {e}")
        return [False, []]'''
        
        content = content.replace(original_dbops_except, replacement_dbops_except)
        
        with open(filepath, 'w') as f:
            f.write(content)
        continue

    if 'import error_handler' not in content:
        content = "import error_handler\n" + content

    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('async def ') and '@error_handler.safe_handler' not in (lines[i-1] if i>0 else ''):
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(f"{indent}@error_handler.safe_handler")
        new_lines.append(line)
        i += 1

    with open(filepath, 'w') as f:
        f.write('\n'.join(new_lines))

print("Modified files.")
