from google.adk.agents import LlmAgent
from tools.grid import (
    get_caiso_demand,
    get_caiso_supply_mix,
    # get_renewable_generation,
    # get_net_demand,
    calculate_load_deviation,
    # get_curtailment_data,
    # get_transmission_constraints,
    # get_outages,
)

grid_agent = LlmAgent(
    name="CAISO_Grid",
    description="Analyzes real-time grid operations including demand vs forecast deviations, supply mix, renewable generation, net demand, curtailment, and transmission constraints.",
    tools=[
        get_caiso_demand,
        get_caiso_supply_mix,
        # get_renewable_generation,
        # get_net_demand,
        calculate_load_deviation,
        # get_curtailment_data,
        # get_transmission_constraints,
        # get_outages,
    ]
)