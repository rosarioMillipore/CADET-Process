#!/usr/bin/env python3

"""
===============================================
Optimize Batch Chromatography of Binary Mixture
===============================================

"""
import sys
sys.path.append('../')

from CADETProcess.simulator import Cadet
from CADETProcess.fractionation import FractionationOptimizer
from CADETProcess.performance import PerformanceProduct
from CADETProcess.performance import Productivity, EluentConsumption, Recovery
from CADETProcess.optimization import OptimizationProblem

from operating_modes.batch_elution import process
component_system = process.component_system

optimization_problem = OptimizationProblem(name='batch elution')
optimization_problem.add_evaluation_object(process)

optimization_problem.add_variable('cycle_time', lb=10, ub=600)
optimization_problem.add_variable('feed_duration.time', lb=10, ub=300)

optimization_problem.add_linear_constraint(
    ['feed_duration.time', 'cycle_time'], [1, -1]
)

process_simulator = Cadet()
process_simulator.evaluate_stationarity = True
optimization_problem.add_evaluator(process_simulator, cache=True)

frac_opt = FractionationOptimizer()
optimization_problem.add_evaluator(
    frac_opt, cache=True, kwargs={'purity_required': [0.95, 0.95]}
)

case = 'single'
if case == 'single':
    ranking = [1, 1]
    performance = PerformanceProduct(component_system, ranking=ranking)
    optimization_problem.add_objective(
        performance, requires=[process_simulator, frac_opt]
    )
elif case == 'multi':
    productivity = Productivity(component_system)
    optimization_problem.add_objective(
        productivity,
        n_objectives=2,
        requires=[process_simulator, frac_opt]
    )

    recovery = Recovery(component_system)
    optimization_problem.add_objective(
        recovery,
        n_objectives=2,
        requires=[process_simulator, frac_opt]
    )

    eluent_consumption = EluentConsumption(component_system)
    optimization_problem.add_objective(
        eluent_consumption,
        n_objectives=2,
        requires=[process_simulator, frac_opt]
    )


def callback(fractionation, individual, evaluation_object, callbacks_dir):
    fractionation.plot_fraction_signal(
        file_name=f'{callbacks_dir}/{individual.id}_{evaluation_object}_fractionation.png',
        show=False
    )


optimization_problem.add_callback(
    callback, requires=[process_simulator, frac_opt]
)


if __name__ == "__main__":
    from CADETProcess.optimization import U_NSGA3
    optimizer = U_NSGA3()
    optimizer.n_cores = 4
    # optimizer.pop_size = 4
    optimizer.n_max_gen = 4

    from CADETProcess import settings
    settings.working_directory = f'./batch_elution/{case}'
    results = optimizer.optimize(
        optimization_problem,
        save_results=True,
        use_checkpoint=False,
    )
