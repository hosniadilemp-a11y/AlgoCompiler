import subprocess
import sys
import tempfile
import os
import time

POLL_INTERVAL_SECONDS = 0.01
DEFAULT_TIMEOUT_SECONDS = 2.0

def _normalize_output(value):
    """Normalize outputs before comparison to avoid false negatives on whitespace."""
    text = '' if value is None else str(value)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]
    return '\n'.join(lines).strip()

def _read_process_memory_kb(pid):
    """Best-effort current RSS in KB for Linux deployments."""
    status_path = f'/proc/{pid}/status'
    try:
        with open(status_path, 'r', encoding='utf-8') as handle:
            for line in handle:
                if line.startswith('VmRSS:'):
                    parts = line.split()
                    if len(parts) >= 2:
                        return int(parts[1])
    except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError, OSError):
        return 0
    return 0

def _run_with_metrics(script_path, input_data, timeout_seconds):
    process = subprocess.Popen(
        [sys.executable, script_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    start = time.perf_counter()
    peak_memory_kb = 0
    timed_out = False

    try:
        if process.stdin is not None:
            try:
                process.stdin.write(input_data or '')
                process.stdin.close()
                process.stdin = None
            except BrokenPipeError:
                pass

        while process.poll() is None:
            peak_memory_kb = max(peak_memory_kb, _read_process_memory_kb(process.pid))
            if time.perf_counter() - start > timeout_seconds:
                timed_out = True
                process.kill()
                break
            time.sleep(POLL_INTERVAL_SECONDS)

        stdout, stderr = process.communicate()
    except Exception:
        try:
            process.kill()
        except Exception:
            pass
        raise

    elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
    return {
        'returncode': process.returncode,
        'stdout': stdout or '',
        'stderr': stderr or '',
        'timed_out': timed_out,
        'execution_time_ms': elapsed_ms,
        'memory_usage_kb': peak_memory_kb
    }

def execute_code(python_code, test_cases, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
    """
    Executes the provided Python code against a list of test cases in a restricted subprocess.
    Requires python_code to read from stdin and write to stdout.
    """
    results = []
    
    # Write the compiled python code to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_script:
        temp_script.write(python_code)
        script_path = temp_script.name

    try:
        for tc in test_cases:
            tc_id = tc['id']
            input_data = tc['input']
            expected_output = _normalize_output(tc.get('expected_output', ''))

            try:
                process_result = _run_with_metrics(
                    script_path=script_path,
                    input_data=input_data,
                    timeout_seconds=timeout_seconds
                )
                actual_output = process_result['stdout'].strip()
                error_output = process_result['stderr'].strip()
                execution_time_ms = process_result['execution_time_ms']
                memory_usage_kb = process_result['memory_usage_kb']
                
                if not process_result['timed_out'] and process_result['returncode'] == 0:
                    normalized_actual = _normalize_output(actual_output)
                    # Keep strict compare first, then allow whitespace-only differences.
                    passed = (
                        normalized_actual == expected_output
                        or normalized_actual.split() == expected_output.split()
                    )
                    results.append({
                        'test_case_id': tc_id,
                        'input': input_data,
                        'expected_output': expected_output,
                        'passed': passed,
                        'actual_output': actual_output,
                        'error': None,
                        'execution_time_ms': execution_time_ms,
                        'memory_usage_kb': memory_usage_kb
                    })
                else:
                    results.append({
                        'test_case_id': tc_id,
                        'input': input_data,
                        'expected_output': expected_output,
                        'passed': False,
                        'actual_output': actual_output,
                        'error': (
                            "Timeout: Maximum execution time exceeded."
                            if process_result['timed_out']
                            else error_output or "Execution Failed"
                        ),
                        'execution_time_ms': execution_time_ms,
                        'memory_usage_kb': memory_usage_kb
                    })
            except Exception as e:
                results.append({
                    'test_case_id': tc_id,
                    'input': input_data,
                    'expected_output': expected_output,
                    'passed': False,
                    'actual_output': "",
                    'error': f"System Error: {str(e)}",
                    'execution_time_ms': 0.0,
                    'memory_usage_kb': 0
                })
                
    finally:
        # Cleanup temp file
        if os.path.exists(script_path):
            os.remove(script_path)

    return results
