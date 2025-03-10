import pygame
import random

# ------------------------------------
# 1) SCREEN PARAMETERS
# ------------------------------------
WIDTH = 1000          # Window width
HEIGHT = 1000         # Window height
TILE_SIZE = 50        # Size of each tile (pixel)
ROWS = HEIGHT // TILE_SIZE
COLS = WIDTH // TILE_SIZE

# Surface types A, B, C, D with different costs
SURFACE_TYPES = {
    'A': 1.0,
    'B': 2.0,
    'C': 3.0,
    'D': 4.0
}

def generate_surface_map(rows, cols):
    surface_map = []
    surfaces = list(SURFACE_TYPES.keys())
    for r in range(rows):
        row = []
        for c in range(cols):
            row.append(random.choice(surfaces))
        surface_map.append(row)
    return surface_map

# ------------------------------------
# 2) GA PARAMETERS
# ------------------------------------
POPULATION_SIZE = 1500
MAX_GENERATIONS = 500
MUTATION_RATE = 0.05
CROSSOVER_RATE = 0.8
MAX_PATH_LENGTH = 70

SURFACE_WEIGHT = 10  
DISTANCE_FACTOR = 100.0
LENGTH_PENALTY = 0.01

# Remove old JUMP_PENALTY, now directly penalize large
# when detecting non-adjacent steps.
JUMP_PENALTY = 0.0  

# ------------------------------------
# 3) INITIALIZE PYGAME & MAP
# ------------------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GA Robot - Draw path (line + dot) & ensure adjacent steps")

surface_map = generate_surface_map(ROWS, COLS)

start_cell = (0, 0)
goal_cell = (ROWS - 1, COLS - 1)

def cell_to_pixel(row, col):
    x = col * TILE_SIZE + TILE_SIZE // 2
    y = row * TILE_SIZE + TILE_SIZE // 2
    return (x, y)

def create_random_path():
    path = [start_cell]
    current = start_cell
    while current != goal_cell and len(path) < MAX_PATH_LENGTH:
        r, c = current
      
        neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
        valid_neighbors = [(nr, nc) for (nr, nc) in neighbors 
                           if 0 <= nr < ROWS and 0 <= nc < COLS]
        if not valid_neighbors:
            break
        current = random.choice(valid_neighbors)
        path.append(current)
    return path

# ------------------------------------
# 5) COST FUNCTION (PENALIZE HEAVILY FOR NON-ADJACENT STEPS)
# ------------------------------------
def path_cost(path):
    total_cost = 0.0
    surface_cost = 0.0

    # (A) Calculate surface cost
    for (r, c) in path:
        if r < 0 or r >= ROWS or c < 0 or c >= COLS:
            surface_cost += 999999  # Heavy penalty if out of map
        else:
            surface_cost += SURFACE_TYPES[surface_map[r][c]]

    # (B) Penalize if steps are not adjacent
    adjacency_penalty = 0.0
    for i in range(len(path) - 1):
        r1, c1 = path[i]
        r2, c2 = path[i+1]
        # Check Manhattan distance, if != 1 => not adjacent
        if abs(r2 - r1) + abs(c2 - c1) != 1:
            adjacency_penalty += 999999  # Very heavy penalty
    
    # (C) Length penalty
    length_cost = len(path) * LENGTH_PENALTY

    # (D) Distance penalty to goal (if not reached)
    dx = abs(path[-1][0] - goal_cell[0])
    dy = abs(path[-1][1] - goal_cell[1])
    distance_cost = (dx + dy) * DISTANCE_FACTOR if path[-1] != goal_cell else 0

    # Total cost
    total_cost = (SURFACE_WEIGHT * surface_cost
                  + length_cost
                  + distance_cost
                  + adjacency_penalty)
    return total_cost

# ------------------------------------
# 6) GA OPERATORS: Selection, Crossover, Mutation
# ------------------------------------
def selection(population):
    fitness_list = [1.0 / (cost + 1e-6) for _, cost in population]
    total_fitness = sum(fitness_list)
    pick = random.uniform(0, total_fitness)
    current = 0
    for i, f in enumerate(fitness_list):
        current += f
        if current >= pick:
            return population[i][0]
    return population[-1][0]

def crossover(path1, path2):
    if random.random() < CROSSOVER_RATE and len(path1) > 1 and len(path2) > 1:
        cut1 = random.randint(1, len(path1) - 1)
        cut2 = random.randint(1, len(path2) - 1)
        new_path1 = path1[:cut1] + path2[cut2:]
        new_path2 = path2[:cut2] + path1[cut1:]
        # start_cell is always the first element
        new_path1[0] = start_cell
        new_path2[0] = start_cell
        return new_path1[:MAX_PATH_LENGTH], new_path2[:MAX_PATH_LENGTH]
    else:
        path1[0] = start_cell
        path2[0] = start_cell
        return path1, path2

def mutate(path):
    new_path = path[:]
    for i in range(1, len(new_path)):
        if random.random() < MUTATION_RATE:
            op = random.choice(["modify", "insert", "delete"])
            if op == "modify":
                r, c = new_path[i]
                neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
                new_path[i] = random.choice(neighbors)
            elif op == "insert" and len(new_path) < MAX_PATH_LENGTH:
                r, c = new_path[i]
                neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
                if neighbors:
                    new_gene = random.choice(neighbors)
                    new_path.insert(i+1, new_gene)
            elif op == "delete" and len(new_path) > 2:
                new_path.pop(i)
                break
    new_path[0] = start_cell
    return new_path

# ------------------------------------
# 7) INITIALIZE INITIAL POPULATION
# ------------------------------------
population = []
for _ in range(POPULATION_SIZE):
    p = create_random_path()
    c = path_cost(p)
    population.append((p, c))

final_best_path = None
generation = 0
running = True
clock = pygame.time.Clock()
font_small = pygame.font.SysFont(None, 18)

# ------------------------------------
# 8) MAIN LOOP
# ------------------------------------
while running:
    clock.tick(10)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # (A) Draw map
    screen.fill((0, 0, 0))
    for r in range(ROWS):
        for c in range(COLS):
            surface_type = surface_map[r][c]
            cost_value = SURFACE_TYPES[surface_type]

            if surface_type == 'A':
                color = (100, 200, 100)
            elif surface_type == 'B':
                color = (200, 200, 100)
            elif surface_type == 'C':
                color = (200, 100, 100)
            else:
                color = (50, 50, 100)
            rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, color, rect)

            cost_str = str(cost_value)
            text_surf_small = font_small.render(cost_str, True, (0, 0, 0))
            text_rect_small = text_surf_small.get_rect(center=rect.center)
            screen.blit(text_surf_small, text_rect_small)

    # Draw goal
    gx, gy = cell_to_pixel(*goal_cell)
    pygame.draw.circle(screen, (255, 0, 0), (gx, gy), TILE_SIZE // 2)

    # (B) GA: create new generation
    if generation < MAX_GENERATIONS:
        # Calculate cost for current population
        population = [(p, path_cost(p)) for p, _ in population]
        # Sort by increasing cost
        population.sort(key=lambda x: x[1])
        best_path, best_cost = population[0]

        # Update global best path
        if final_best_path is None or path_cost(best_path) < path_cost(final_best_path):
            final_best_path = best_path

        # Elite
        new_population = []
        elite_size = POPULATION_SIZE // 10
        for i in range(elite_size):
            new_population.append(population[i])

        # Generate new population
        while len(new_population) < POPULATION_SIZE:
            parent1 = selection(population)
            parent2 = selection(population)
            child1, child2 = crossover(parent1, parent2)
            child1 = mutate(child1)
            child2 = mutate(child2)
            new_population.append((child1, None))
            if len(new_population) < POPULATION_SIZE:
                new_population.append((child2, None))

        population = new_population
        generation += 1
    else:
        # After GA ends
        best_path, best_cost = population[0]
        final_best_path = best_path

    # (C) Draw best path (line + dot)
    if final_best_path and len(final_best_path) > 1:
        # Draw lines
        for i in range(len(final_best_path) - 1):
            (r1, c1) = final_best_path[i]
            (r2, c2) = final_best_path[i+1]
            x1, y1 = cell_to_pixel(r1, c1)
            x2, y2 = cell_to_pixel(r2, c2)
            pygame.draw.line(screen, (0, 0, 255), (x1, y1), (x2, y2), 2)

        # Draw dots
        for (pr, pc) in final_best_path:
            x, y = cell_to_pixel(pr, pc)
            pygame.draw.circle(screen, (255, 255, 255), (x, y), 5)

    # (D) Draw static robot at start
    rx, ry = cell_to_pixel(*start_cell)
    pygame.draw.circle(screen, (0, 255, 255), (rx, ry), TILE_SIZE // 2)

    # (E) Display information
    font = pygame.font.SysFont(None, 24)
    text_surf = font.render(
        f"Gen: {generation} | Best cost: {best_cost:.2f} | Path length: {len(final_best_path)}",
        True, (255, 255, 255)
    )
    screen.blit(text_surf, (10, 10))
    pygame.display.flip()

pygame.quit()