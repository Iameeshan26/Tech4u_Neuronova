import sys
# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import app.config as config
import app.data_utils as data_utils
from app.optimizer import RouteOptimizer
from app.main import check_reoptimization

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_simulation():
    logger.info("--- Starting Delivery Simulation Mode ---")
    
    # 1. Load Data (in root/data/)
    root_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(root_dir, 'data', 'locations.csv')
    df = data_utils.load_data_from_csv(file_path)
    if df is None:
        logger.error("Could not load locations.csv")
        return

    # 2. Initial Optimization
    logger.info("Phase 1: Initial Route Planning")
    dist_matrix, time_matrix = data_utils.get_tomtom_matrix(df)
    
    optimizer = RouteOptimizer(df, dist_matrix, time_matrix)
    solution = optimizer.solve()
    
    if not solution:
        logger.error("Initial optimization failed.")
        return
        
    routes = optimizer.print_solution()
    if not routes:
        return

    # Pick the first vehicle's route for simulation
    test_route = routes[0]
    initial_eta = test_route['time']
    logger.info(f"Initial ETA for Vehicle {test_route['vehicle']}: {initial_eta:.0f}s")

    # 3. Simulate Progress & Traffic Update
    logger.info("\nPhase 2: Simulating Delivery Progress...")
    time.sleep(1) # Simulate some time passing
    
    # 4. Inject Fake Traffic Update (Reactive Engine Test)
    logger.info("\nPhase 3: Injecting Fake Traffic Update (Anomaly Detection)")
    
    # Case A: Minor delay (within threshold)
    logger.info("Scenario A: Minor delay (5%)")
    simulated_current_eta_minor = initial_eta * 1.05
    if check_reoptimization(simulated_current_eta_minor, initial_eta):
        logger.info(">> RE-OPTIMIZE TRIGGERED (Unexpected behavior!)")
    else:
        logger.info(">> Variance within limits. No re-optimization needed.")

    # Case B: Major traffic jam (30% delay)
    logger.info("\nScenario B: Major traffic jam (30%)")
    simulated_current_eta_major = initial_eta * 1.30
    
    if check_reoptimization(simulated_current_eta_major, initial_eta):
        logger.info(">> RE-OPTIMIZE TRIGGERED! Reactive engine is responding to traffic.")
        
        # In a real scenario, we would re-run solver with updated time_matrix.
        # Here we prove the detection works.
        logger.info("Phase 4: Re-calculating with updated traffic data...")
        # Simulate updated matrix (global 30% slowdown)
        updated_time_matrix = time_matrix * 1.3
        new_optimizer = RouteOptimizer(df, dist_matrix, updated_time_matrix)
        new_solution = new_optimizer.solve()
        
        if new_solution:
            logger.info("Re-optimization successful. New plan generated.")
            new_optimizer.print_solution()
        else:
            logger.error("Re-optimization failed to find a new solution.")
    else:
        logger.error(">> RE-OPTIMIZE NOT TRIGGERED! (Testing failed)")

    logger.info("\n--- Simulation Complete ---")

if __name__ == "__main__":
    run_simulation()
