import numpy as np

def objective_function(weights, cnn_val, swin_val, hybrid_val, target):
    
    
    sum_w = np.sum(weights)
    if sum_w == 0: return 1e6 
    
    normalized_w = weights / sum_w
    
    
    final_score = (normalized_w[0] * cnn_val + 
                   normalized_w[1] * swin_val + 
                   normalized_w[2] * hybrid_val)
    
   
    return (final_score - target)**2

def run_art_de_optimization(cnn_in, swin_in, hybrid_in, target_val):
    pop_size = 20
    dimensions = 3
    iterations = 100
    F = 0.5
    CR = 0.7

    
    population = np.random.rand(pop_size, dimensions)
    fitness = np.array([objective_function(ind, cnn_in, swin_in, hybrid_in, target_val) for ind in population])

    for gen in range(iterations):
        for i in range(pop_size):
            
            idxs = [idx for idx in range(pop_size) if idx != i]
            r1, r2, r3 = population[np.random.choice(idxs, 3, replace=False)]
            donor = r1 + F * (r2 - r3)
            
            
            donor = np.clip(donor, 0.001, 1.0)

            
            trial = np.copy(population[i])
            j_rand = np.random.randint(0, dimensions)
            for j in range(dimensions):
                if np.random.rand() < CR or j == j_rand:
                    trial[j] = donor[j]

            
            f_trial = objective_function(trial, cnn_in, swin_in, hybrid_in, target_val)
            if f_trial < fitness[i]:
                population[i] = trial
                fitness[i] = f_trial

    best_idx = np.argmin(fitness)
    
    return population[best_idx] / np.sum(population[best_idx])


if __name__ == "__main__":
    print("Art Authentication: DE Ensemble Weight Optimizer")
    print("-----------------------------------------------")
    
    try:
        print("Enter model scores (0.0 to 1.0):")
        c_score = float(input("CNN Model Prediction:      "))
        s_score = float(input("Swin Transformer Score:    "))
        h_score = float(input("Hybrid Model Score:        "))
        
       
        target = float(input("Actual Authenticity (1=Real, 0=Fake): "))

        if any(x > 1.0 or x < 0.0 for x in [c_score, s_score, h_score]):
            print("\nError: All input values must be between 0.0 and 1.0.")
        else:
            opt_weights = run_art_de_optimization(c_score, s_score, h_score, target)
            
            final_score = (opt_weights[0]*c_score + opt_weights[1]*s_score + opt_weights[2]*h_score)

            print("\n--- Optimization Results ---")
            print(f"Optimal Weights: CNN={opt_weights[0]:.3f}, Swin={opt_weights[1]:.3f}, Hybrid={opt_weights[2]:.3f}")
            print(f"Final Optimized Authenticity Score: {final_score:.4f}")
            print(f"Target Authenticity: {target}")
            
    except ValueError:
        print("Error: Please enter numeric values only.")
        