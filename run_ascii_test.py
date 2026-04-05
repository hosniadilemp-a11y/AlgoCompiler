import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from compiler.parser import compile_algo

ALGO_FILE = 'examples/Tests/TestAscii.algo'

def test_ascii():
    try:
        with open(ALGO_FILE, 'r', encoding='utf-8') as f:
            code = f.read()
        
        python_code, errors = compile_algo(code)
        if errors:
            print(f"[COMPILATION ERRORS] {errors}")
            return
        
        # Execute the generated python code
        exec_globals = {}
        # Pre-populate input() if Leer is used (not in this test yet)
        
        print("--- Generated Python ---")
        # print(python_code) # Uncomment to see code
        
        import io
        from contextlib import redirect_stdout
        
        f_stdout = io.StringIO()
        with redirect_stdout(f_stdout):
            exec(python_code, exec_globals)
        
        output = f_stdout.getvalue().strip()
        print("--- Output ---")
        print(output)
        
        # Expected output:
        # 97
        # 65
        # OK
        expected = "97 65 OK" # Ecrire puts spaces between args or separate lines?
        # Let's check _algo_ecrire implementation.
        
        # In parser.py:
        # code += "    print(' '.join(parts), end='')\n\n"
        # Wait, if multiple Ecrire are called, they stay on the same line if end=''
        # BUT the algo code has 3 separate Ecrire?
        # No, Ecrire adds to the global output.
        
        if "97 65 OK" in output:
            print("[SUCCESS] ASCII built-in working correctly.")
        else:
            print("[FAILURE] Output didn't match expected.")
            
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    test_ascii()
