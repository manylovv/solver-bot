import argparse
import json
import sys
import numpy as np
from scipy.optimize import fsolve

def parse_variables(vars_str):
    """Parse variable string into a list of variables."""
    return [v.strip() for v in vars_str.split(',')]

def create_equation_function(equations, variables):
    """Create a function that evaluates the system of equations."""
    def eval_equations(values):
        var_dict = dict(zip(variables, values))
        results = []
        for eq in equations:
            if '=' in eq:
                left, right = eq.split('=')
                left_val = eval(left.strip(), {"__builtins__": None}, var_dict)
                right_val = eval(right.strip(), {"__builtins__": None}, var_dict)
                results.append(left_val - right_val)
            else:
                results.append(eval(eq, {"__builtins__": None}, var_dict))
        return results
    return eval_equations

def solve_equations(vars_str, equations_list, num_guesses=5):
    """Solve a system of equations with multiple initial guesses."""
    variables = parse_variables(vars_str)
    n_vars = len(variables)
    eq_func = create_equation_function(equations_list, variables)
    
    initial_guesses = [
        np.random.uniform(0, 20, n_vars) for _ in range(num_guesses)
    ]
    initial_guesses.append(np.ones(n_vars))
    
    best_solution = None
    min_residual = float('inf')
    
    for guess in initial_guesses:
        try:
            solution = fsolve(eq_func, guess)
            residuals = eq_func(solution)
            total_residual = sum(abs(r) for r in residuals)
            
            if total_residual < min_residual:
                min_residual = total_residual
                best_solution = solution
        except:
            continue
    
    if best_solution is None:
        raise ValueError("Could not find a solution with any of the initial guesses")
    
    return dict(zip(variables, best_solution)), min_residual

def parse_json_input(json_str):
    """Parse JSON input and validate format."""
    try:
        data = json.loads(json_str)
        
        if not isinstance(data, dict):
            raise ValueError("Input must be a JSON object")
            
        required_fields = {'variables', 'equations'}
        if not all(field in data for field in required_fields):
            raise ValueError(f"Input must contain all required fields: {required_fields}")
            
        if not isinstance(data['variables'], str):
            raise ValueError("'variables' must be a comma-separated string")
            
        if not isinstance(data['equations'], list):
            raise ValueError("'equations' must be a list of strings")
            
        return data['variables'], data['equations']
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Solve system of equations from JSON input')
    parser.add_argument('--input', '-i', type=str, help='JSON input string. If not provided, reads from stdin')
    parser.add_argument('--num-guesses', '-n', type=int, default=5, help='Number of random initial guesses (default: 5)')
    parser.add_argument('--output-format', '-f', choices=['text', 'json'], default='text', 
                       help='Output format (default: text)')
    
    args = parser.parse_args()
    
    # Read input either from argument or stdin
    if args.input:
        json_input = args.input
    else:
        json_input = sys.stdin.read()
    
    try:
        # Parse input
        variables, equations = parse_json_input(json_input)
        
        # Solve equations
        solution, residual = solve_equations(variables, equations, args.num_guesses)
        
        # Output results
        if args.output_format == 'json':
            result = {
                'solution': {k: float(v) for k, v in solution.items()},
                'residual': float(residual)
            }
            print(json.dumps(result, indent=2))
        else:
            for var, val in solution.items():
                print(f"{var} = {val:.4f}")
            # print(f"\nTotal residual: {residual:.10f}")
            
    except Exception as e:
        error_msg = {'error': str(e)} if args.output_format == 'json' else f"Error: {str(e)}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()