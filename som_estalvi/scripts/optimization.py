import sys, json
import minizinc

def optimize(dades):
    # exectuar minizinc
    model_path = './optimization.mzn'
    minizinc.Model(model_path)

    solver_name = "coin-bc"
    # Create an instance of the model for every solver
    solver = minizinc.Solver.lookup(solver_name)
    inst = minizinc.Instance(solver, self.model)

    for k,v in dades.items():
        inst[k] = v

    inst.solve()




    pass

# Main program optimize
if __name__ == "__main__":
    standard_input = sys.stdin.read()
    dades = json.loads(standard_input)
    optimize(dades)
