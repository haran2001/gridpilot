from google.adk.agents import LlmAgent
from prompts.grid import get_grid_instructions
from tools.grid import (
    get_caiso_demand,
    get_caiso_supply_mix,
    get_caiso_renewable_generation,
    get_caiso_net_demand,
    calculate_load_deviation,
    get_caiso_curtailment,
    get_caiso_tie_flows,
    get_caiso_outages,
)

GRID_INSTRUCTIONS = get_grid_instructions()

grid_agent = LlmAgent(
    name="CAISO_Grid",
    instruction=GRID_INSTRUCTIONS,
    description="Analyzes real-time grid operations including demand vs forecast deviations, supply mix, renewable generation, net demand, curtailment, and transmission constraints.",
    tools=[
        get_caiso_demand,
        get_caiso_supply_mix,
        get_caiso_renewable_generation,
        get_caiso_net_demand,
        calculate_load_deviation,
        get_caiso_curtailment,
        get_caiso_tie_flows,
        get_caiso_outages,
    ]
)