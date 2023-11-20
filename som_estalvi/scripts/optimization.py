import sys, json
import minizinc

def optimize(dades):
    # exectuar minizinc
    model_path = './optimization.mzn'
    minizinc.Model(model_path)

    solvers = ["chuffed", "coin-bc"]
    tasks = set()
    for solver_name in self.solvers:
        # Create an instance of the model for every solver
        solver = minizinc.Solver.lookup(solver_name)
        inst = minizinc.Instance(solver, self.model)

        for k,v in dades.items():
            inst[k] = v

        task = asyncio.create_task(inst.solve_async)
        task.solver = solver.name
        tasks.add(task)

    # Wait on the first task to finish and cancel the other tasks
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    if done:
        result = done.pop().result()

    # Clean pending tasks
    for task in pending:
        task.cancel()
        await asyncio.sleep(0.1)


    pass

# Main program optimize
if __name__ == "__main__":
    standard_input = sys.stdin.read()
    dades = json.loads(standard_input)
    optimize(dades)
