# AquaGrid: AI Workload Scheduling with Water, Energy, and Carbon Awareness

AquaGrid is an optimization engine and decision-support simulation that coordinates flexible AI compute tasks across geo-distributed data centres to balance **electricity costs**, **operational carbon emissions**, and **direct & indirect freshwater consumption**.

---

## Key Capabilities

1. **Physical Resource Simulation**:
   - Models data centre Power Usage Effectiveness (PUE) as a function of outdoor ambient temperature.
   - Computes direct cooling water evaporation (Water Usage Effectiveness, WUE) based on cooling technology (evaporative towers, dry chillers).
   - Computes indirect power-plant water consumption using regional Energy-Water Intensity Factors (EWIF).
   - Simulates dynamic grid carbon intensity and wholesale electricity prices.

2. **Constraint-Based Scheduling Engine**:
   - Built on **Google OR-Tools CP-SAT**.
   - Hard constraints: GPU site capacity, workload deadlines, and regional daily water consumption budgets.
   - Multi-objective Pareto optimization balancing cost, carbon, and water.
   - Transparent infeasibility diagnosis (no silent drops).

3. **Comparative Benchmarking**:
   - Compares the proposed Water-Aware Optimizer against industry-standard baselines:
     - **Baseline 1**: Greedy Earliest-Deadline-First / FIFO.
     - **Baseline 2**: Carbon-Only Minimizer (spatial-temporal shifting ignoring water stress).

4. **Full-Stack Architecture**:
   - **Backend**: FastAPI, Pydantic v2, Google OR-Tools, PostgreSQL, SQLAlchemy.
   - **Frontend**: React, TypeScript, Vite, TailwindCSS, Recharts.
   - **Testing**: Automated unit and scenario test suite via Pytest.

---

## Project Structure

```
aquagrid/
├── backend/
│   ├── src/
│   │   ├── models/          # Pydantic domain models & validation
│   │   ├── simulation/      # Environmental & physical calculations (PUE, WUE, Carbon, Cost)
│   │   ├── scheduling/      # Baselines & Google OR-Tools CP-SAT optimizer
│   │   └── api/             # FastAPI REST endpoints
│   └── tests/               # Pytest automated test suite
├── docs/
│   ├── mathematical_formulation.md
│   ├── assumptions_and_limitations.md
│   └── architecture.md
├── pyproject.toml
└── requirements.txt
```

---

## Quickstart (Local Development)

### 1. Set Up the Python Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Automated Tests
```bash
pytest backend/tests/ -v
```
