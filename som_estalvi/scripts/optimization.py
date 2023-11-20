import sys, json
import minizinc

def optimize(dades):
    # exectuar minizinc
    model_path = ''
    minizinc.Model(model_path)

    solvers = ["chuffed", "coin-bc"]
    tasks = set()
    for solver_name in self.solvers:
        # Create an instance of the model for every solver
        solver = minizinc.Solver.lookup(solver_name)
        inst = minizinc.Instance(solver, self.model)

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
    dades = json.loads(sys.stdin.read())
    optimize(dades)
