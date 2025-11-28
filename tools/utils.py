import gridstatus

def search_caiso_nodes(query: str, limit: int = 10):
    """
    Search for CAISO pricing nodes by name.
    Useful for finding specific generators, substations, or load zones.
    """
    iso = gridstatus.CAISO()
    
    # gridstatus may have a method for this, or you pull the full list once
    # and cache it. CAISO publishes the master node list on OASIS.
    all_nodes = iso.get_pnode_ids()  # Check if this exists in your version
    
    matches = [n for n in all_nodes if query.lower() in n.lower()]
    return matches[:limit]