"""
GENETIC ALGORITHM — Optimize Candidate-Job Matching

Standard ML models score each candidate independently.
The genetic algorithm optimizes the OVERALL assignment:
  "Given N candidates and M jobs, find the best assignment
   that maximizes total match quality across all positions."

This is especially useful when:
  - One candidate applies to multiple jobs
  - A recruiter has multiple positions to fill
  - You want to avoid assigning the same top candidate to every role

Uses evolutionary optimization:
  1. Create random candidate-job assignments (population)
  2. Score each assignment by total match quality (fitness)
  3. Select best assignments (selection)
  4. Combine good assignments (crossover)
  5. Add small random changes (mutation)
  6. Repeat for N generations
  7. Return the best overall assignment
"""
import logging
import random
import numpy as np
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class GeneticMatcher:
    """
    Genetic algorithm for optimal candidate-job matching.

    Usage:
        matcher = GeneticMatcher(scores_matrix)
        best_assignment = matcher.evolve()
    """

    def __init__(
        self,
        scores: np.ndarray,
        population_size: int = 100,
        generations: int = 200,
        mutation_rate: float = 0.1,
        elite_ratio: float = 0.1,
    ):
        """
        Args:
            scores: Matrix of shape (n_candidates, n_jobs) where
                    scores[i][j] = match score of candidate i for job j (0-100)
            population_size: Number of assignments per generation
            generations: Number of evolution cycles
            mutation_rate: Probability of random mutation per gene
            elite_ratio: Top fraction kept unchanged (elitism)
        """
        self.scores = scores
        self.n_candidates = scores.shape[0]
        self.n_jobs = scores.shape[1]
        self.pop_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.elite_count = max(2, int(population_size * elite_ratio))

    def _create_individual(self) -> List[int]:
        """Create a random assignment: each candidate gets assigned to a job (or -1 for unassigned)."""
        assignment = []
        for i in range(self.n_candidates):
            if random.random() > 0.3:  # 70% chance of assignment
                assignment.append(random.randint(0, self.n_jobs - 1))
            else:
                assignment.append(-1)  # Unassigned
        return assignment

    def _fitness(self, individual: List[int]) -> float:
        """
        Calculate fitness of an assignment.
        Higher = better overall match quality.

        Factors:
          - Sum of match scores for assigned candidates
          - Penalty for overloading a single job
          - Bonus for diversity (spreading across jobs)
        """
        total_score = 0
        job_counts = {}

        for candidate_idx, job_idx in enumerate(individual):
            if job_idx == -1:
                continue
            # Add match score
            total_score += self.scores[candidate_idx][job_idx]
            # Track how many candidates per job
            job_counts[job_idx] = job_counts.get(job_idx, 0) + 1

        # Penalty for overloaded jobs (more than 5 candidates per position)
        overload_penalty = sum(
            max(0, count - 5) * 10
            for count in job_counts.values()
        )

        # Bonus for job coverage (filling all positions)
        coverage_bonus = len(job_counts) * 5

        return total_score - overload_penalty + coverage_bonus

    def _select_parents(self, population: List, fitnesses: List[float]) -> Tuple:
        """Tournament selection — pick 2 parents."""
        def tournament(k=3):
            contenders = random.sample(range(len(population)), k)
            best = max(contenders, key=lambda i: fitnesses[i])
            return population[best]

        return tournament(), tournament()

    def _crossover(self, parent1: List[int], parent2: List[int]) -> List[int]:
        """Single-point crossover."""
        if len(parent1) <= 1:
            return parent1[:]
        point = random.randint(1, len(parent1) - 1)
        child = parent1[:point] + parent2[point:]
        return child

    def _mutate(self, individual: List[int]) -> List[int]:
        """Randomly change some assignments."""
        mutated = individual[:]
        for i in range(len(mutated)):
            if random.random() < self.mutation_rate:
                if random.random() > 0.2:
                    mutated[i] = random.randint(0, self.n_jobs - 1)
                else:
                    mutated[i] = -1  # Unassign
        return mutated

    def evolve(self) -> Dict:
        """
        Run the genetic algorithm.

        Returns:
            {
                "best_assignment": {candidate_idx: job_idx, ...},
                "best_fitness": float,
                "generation_history": [fitness_per_gen],
                "improvement": float (% improvement over random),
            }
        """
        logger.info(
            f"Starting genetic optimization: {self.n_candidates} candidates, "
            f"{self.n_jobs} jobs, {self.generations} generations"
        )

        # Initial population
        population = [self._create_individual() for _ in range(self.pop_size)]

        best_ever = None
        best_fitness_ever = float("-inf")
        history = []

        for gen in range(self.generations):
            # Calculate fitness for all individuals
            fitnesses = [self._fitness(ind) for ind in population]

            # Track best
            gen_best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
            gen_best_fitness = fitnesses[gen_best_idx]

            if gen_best_fitness > best_fitness_ever:
                best_fitness_ever = gen_best_fitness
                best_ever = population[gen_best_idx][:]

            history.append(gen_best_fitness)

            # Early stopping if converged
            if gen > 50 and len(set(history[-20:])) == 1:
                logger.info(f"Converged at generation {gen}")
                break

            # Create next generation
            # Elitism: keep top performers
            sorted_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)
            new_population = [population[i][:] for i in sorted_indices[:self.elite_count]]

            # Fill rest with crossover + mutation
            while len(new_population) < self.pop_size:
                parent1, parent2 = self._select_parents(population, fitnesses)
                child = self._crossover(parent1, parent2)
                child = self._mutate(child)
                new_population.append(child)

            population = new_population

        # Format result
        assignment = {}
        for candidate_idx, job_idx in enumerate(best_ever):
            if job_idx != -1:
                assignment[candidate_idx] = job_idx

        # Calculate improvement over random
        random_fitness = np.mean([self._fitness(self._create_individual()) for _ in range(100)])
        improvement = ((best_fitness_ever - random_fitness) / max(random_fitness, 1)) * 100

        logger.info(
            f"GA complete: fitness={best_fitness_ever:.1f}, "
            f"improvement={improvement:.1f}% over random"
        )

        return {
            "best_assignment": assignment,
            "best_fitness": round(best_fitness_ever, 2),
            "generations_run": len(history),
            "generation_history": history,
            "improvement_over_random": round(improvement, 1),
        }


def optimize_job_assignments(job_id: int = None) -> Dict:
    """
    Run genetic algorithm to optimize candidate-job assignments.

    If job_id is provided, optimize for that specific job.
    If None, optimize across all approved jobs.
    """
    from candidates.models import Application, ScreeningScore
    from jobs.models import Job

    if job_id:
        jobs = Job.objects.filter(id=job_id, status="approved")
    else:
        jobs = Job.objects.filter(status="approved")

    if not jobs.exists():
        return {"error": "No approved jobs found"}

    # Build scores matrix
    job_list = list(jobs)
    applications = Application.objects.filter(
        job__in=job_list
    ).select_related("score", "candidate")

    if not applications.exists():
        return {"error": "No applications found"}

    # Get unique candidates
    candidates = list(set(app.candidate_id for app in applications))
    candidate_map = {cid: idx for idx, cid in enumerate(candidates)}
    job_map = {j.id: idx for idx, j in enumerate(job_list)}

    # Build score matrix (candidates x jobs)
    n_candidates = len(candidates)
    n_jobs = len(job_list)
    scores = np.zeros((n_candidates, n_jobs))

    for app in applications:
        c_idx = candidate_map.get(app.candidate_id)
        j_idx = job_map.get(app.job_id)
        if c_idx is not None and j_idx is not None:
            try:
                scores[c_idx][j_idx] = app.score.overall_score
            except ScreeningScore.DoesNotExist:
                scores[c_idx][j_idx] = 0

    # Run GA
    matcher = GeneticMatcher(scores)
    result = matcher.evolve()

    # Map indices back to actual IDs
    reverse_candidate = {v: k for k, v in candidate_map.items()}
    reverse_job = {v: k for k, v in job_map.items()}

    assignment_readable = {}
    for c_idx, j_idx in result["best_assignment"].items():
        c_id = reverse_candidate[c_idx]
        j_id = reverse_job[j_idx]
        assignment_readable[c_id] = {
            "job_id": j_id,
            "job_title": job_list[j_idx].title,
            "match_score": scores[c_idx][j_idx],
        }

    result["assignment_details"] = assignment_readable
    return result
