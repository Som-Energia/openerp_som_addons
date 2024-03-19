import sys
import json
import minizinc


def optimize(dades, mzn_path):
    model = minizinc.Model(mzn_path)

    solver_name = "coin-bc"
    solver = minizinc.Solver.lookup(solver_name)
    inst = minizinc.Instance(solver, model)

    for k, v in dades.items():
        inst[k] = v

    res = inst.solve()
    print(res.solution)


# Main program optimize
if __name__ == "__main__":
    standard_input = sys.stdin.read()
    dades = json.loads(standard_input)
    mzn_path = dades.pop("mzn_path")
    optimize(dades, mzn_path)
