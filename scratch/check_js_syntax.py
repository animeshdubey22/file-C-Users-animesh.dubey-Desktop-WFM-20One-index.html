import sys

def check_balance(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()
    
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}
    line = 1
    col = 0
    in_str = None
    in_comment = False
    in_block_comment = False
    
    i = 0
    while i < len(code):
        char = code[i]
        col += 1
        if char == '\n':
            line += 1
            col = 0
            if in_comment:
                in_comment = False
            i += 1
            continue
        
        if in_comment:
            i += 1
            continue
            
        if in_block_comment:
            if char == '*' and i + 1 < len(code) and code[i+1] == '/':
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
            
        if in_str:
            if char == '\\':
                i += 2
                continue
            if char == in_str:
                in_str = None
            i += 1
            continue
            
        if char == '/' and not in_str and not in_comment and not in_block_comment:
            # Check if it's regex or division or comment
            if i + 1 < len(code) and code[i+1] == '/':
                in_comment = True
                i += 2
                continue
            elif i + 1 < len(code) and code[i+1] == '*':
                in_block_comment = True
                i += 2
                continue
            # Simple regex detection heuristic: preceded by ( = : , [ ! ? ;
            prev = code[i-1] if i > 0 else ''
            while prev and prev in ' \t\r':
                i_prev = i - 2
                prev = code[i_prev] if i_prev >= 0 else ''
            if prev in '(=:[,!?;&|':
                # Skip regex literal
                i += 1
                while i < len(code) and code[i] != '/' and code[i] != '\n':
                    if code[i] == '\\':
                        i += 2
                        continue
                    i += 1
                i += 1
                continue

        if char in ('"', "'", '`'):
            in_str = char
            i += 1
            continue
            
        if char in '({[':
            stack.append((char, line, col))
        elif char in ')}]':
            if not stack:
                print(f"Error: Unexpected closing '{char}' at line {line}, col {col}")
                return False
            top, tline, tcol = stack.pop()
            if top != pairs[char]:
                print(f"Error: Mismatched '{char}' at line {line}, col {col} (expected match for '{top}' from line {tline}, col {tcol})")
                return False
        i += 1
        
    if stack:
        top, tline, tcol = stack[-1]
        print(f"Error: Unclosed '{top}' from line {tline}, col {tcol}")
        return False
        
    print(f"Success: Syntax & Brackets balanced across {line} lines in {filename}!")
    return True

if __name__ == '__main__':
    check_balance('app.js')
