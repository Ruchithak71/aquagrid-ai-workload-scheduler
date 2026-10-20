# AquaGrid: Mathematical & Physical Formulation

This document formally specifies the physical simulation equations, environmental metrics, and optimization objectives for AquaGrid.

---

## 1. Physical Indices & Time Resolution

- **Time Horizon**: Discrete simulation horizon $T = \{0, 1, 2, \dots, H-1\}$, where each step $t \in T$ represents a 1-hour interval (typically $H = 24$).
- **Data-Centre Sites**: Set of distributed facilities $S = \{s_1, s_2, \dots, s_M\}$.
- **Workloads**: Set of submitted AI batch tasks $J = \{j_1, j_2, \dots, j_N\}$.

---

## 2. Workload Specifications

Each workload $j \in J$ is parameterized by a tuple:
$$(r_j, d_j, p_j, g_j, \pi_j, \text{preemptible}_j)$$
where:
- $r_j \in T$: Release / arrival hour.
- $d_j \in T$: Hard completion deadline ($d_j > r_j$).
- $p_j \in \mathbb{N}^+$: Required compute duration in hours.
- $g_j \in \mathbb{N}^+$: Number of GPUs required concurrently.
- $\pi_j \in [1, 5]$: Priority weight (higher = more critical).
- $\text{preemptible}_j \in \{\text{True}, \text{False}\}$: Whether the task can be paused and resumed across time slots.

---

## 3. Site Environmental & Physical Models

For each site $s \in S$ at hour $t \in T$:
- $C_s^{\text{GPU}}$: Total physical GPU capacity of site $s$.
- $B_s^{\text{water}}$: Total allowable daily direct water budget (Litres).
- $P_{\text{GPU}}$: Thermal Design Power (TDP) per GPU (kW, default: 0.7 kW for H100).
- $T_{\text{amb}}(s, t)$: Ambient dry-bulb temperature (°C).
- $\text{CI}(s, t)$: Grid carbon intensity ($\text{gCO}_2\text{eq}/\text{kWh}$).
- $\text{Price}(s, t)$: Electricity price ($\$/\text{kWh}$).
- $\text{EWIF}(s, t)$: Grid Energy-Water Intensity Factor ($\text{L}/\text{kWh}$).

### 3.1 IT Energy
If site $s$ runs an active GPU load $L(s, t)$ at hour $t$:
$$E_{\text{IT}}(s, t) = L(s, t) \times P_{\text{GPU}} \times 1\text{ hour} \quad [\text{kWh}]$$

### 3.2 Total Facility Energy & PUE
Power Usage Effectiveness ($\text{PUE}$) models facility overhead (lighting, power conversion, cooling). It scales linearly with ambient temperature above the economizer threshold with slope $\eta_s$ (`pue_temp_slope`):
$$\text{PUE}(s, t) = \text{PUE}_{\text{base}}(s) + \eta_s \cdot \max(0, T_{\text{amb}}(s, t) - T_{\text{economizer}})$$
$$E_{\text{total}}(s, t) = E_{\text{IT}}(s, t) \times \text{PUE}(s, t) \quad [\text{kWh}]$$

### 3.3 Direct Cooling Water Consumption
Water evaporated on-site in evaporative cooling towers:
$$\text{WUE}_{\text{direct}}(s, t) = \begin{cases} 
\text{WUE}_{\text{base}}(s) & \text{if } T_{\text{amb}}(s, t) \le T_{\text{economizer}} \\ 
\text{WUE}_{\text{base}}(s) + \kappa_s \cdot (T_{\text{amb}}(s, t) - T_{\text{economizer}}) & \text{if } T_{\text{amb}}(s, t) > T_{\text{economizer}}
\end{cases}$$
$$W_{\text{direct}}(s, t) = E_{\text{IT}}(s, t) \times \text{WUE}_{\text{direct}}(s, t) \quad [\text{Litres}]$$

### 3.4 Indirect Grid Water Consumption
Water consumed off-site by power generation stations:
$$W_{\text{indirect}}(s, t) = E_{\text{total}}(s, t) \times \text{EWIF}(s, t) \quad [\text{Litres}]$$

### 3.5 Operational Carbon Emissions
$$C(s, t) = E_{\text{total}}(s, t) \times \text{CI}(s, t) \times 10^{-3} \quad [\text{kgCO}_2\text{eq}]$$

### 3.6 Financial Electricity Cost
$$\text{Cost}(s, t) = E_{\text{total}}(s, t) \times \text{Price}(s, t) \quad [\$]$$

---

## 4. Optimization Formulation

### Decision Variables
- $x_{j, s, t} \in \{0, 1\}$: Equals 1 if workload $j$ is actively executing at site $s$ during hour $t$, else 0.

### Hard Constraints
1. **Capacity Limit**: At every site $s$ and hour $t$, total allocated GPUs cannot exceed capacity:
   $$\sum_{j \in J} x_{j, s, t} \cdot g_j \le C_s^{\text{GPU}} \quad \forall s \in S, \forall t \in T$$

2. **Workload Completion**: Every workload $j$ must receive exactly $p_j$ hours of compute across the network:
   $$\sum_{s \in S} \sum_{t \in T} x_{j, s, t} = p_j \quad \forall j \in J$$

3. **Time Window (Arrival & Deadline)**: A job cannot run before arrival or after deadline:
   $$x_{j, s, t} = 0 \quad \text{if } t < r_j \text{ or } t \ge d_j, \quad \forall s \in S, \forall j \in J$$

4. **Single-Site Execution**: A job executes at one chosen site $s$ (no spatial thrashing):
   $$\text{If } \sum_{t \in T} x_{j, s, t} > 0 \implies \sum_{t \in T} x_{j, s', t} = 0 \quad \forall s' \neq s$$

5. **Non-Preemption Continuity** (for tasks with $\text{preemptible}_j = \text{False}$):
   Workload must run in continuous contiguous blocks without interruption.

6. **Site Water Budget Limit**: Total direct cooling water consumed across the horizon at site $s$ must respect the budget:
   $$\sum_{t \in T} W_{\text{direct}}(s, t) \le B_s^{\text{water}} \quad \forall s \in S$$

### Objective Function
Minimize the normalized weighted trade-off:
$$\min \;\; \alpha \cdot \frac{\text{Total Cost}}{\text{Norm}_{\text{cost}}} + \beta \cdot \frac{\text{Total Carbon}}{\text{Norm}_{\text{carbon}}} + \gamma \cdot \frac{\text{Total Water}}{\text{Norm}_{\text{water}}}$$
where $\alpha + \beta + \gamma = 1.0$, $\alpha, \beta, \gamma \ge 0$, and $\text{Total Water} = \sum_{s \in S} \sum_{t \in T} (W_{\text{direct}}(s, t) + W_{\text{indirect}}(s, t))$.
