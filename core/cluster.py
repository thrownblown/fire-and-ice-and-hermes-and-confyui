from collections import defaultdict

def cluster_people(rows):
    """
    Groups identical token-sets into clusters.
    A signature seen once still gets a cluster.
    Unreliable rows are skipped.
    Cluster ids are person_01 upward, stable sorted by signature then first shot_id.
    """
    # Filter out unreliable rows
    reliable_rows = [r for r in rows if not r.get("people_unreliable", False)]
    if not reliable_rows:
        return []

    # Group shot_ids by their token signatures (as tuples for hashability)
    signature_to_shots = defaultdict(list)
    for r in reliable_rows:
        # signature is the sorted tokens
        sig = tuple(sorted(r["people_tokens"][0])) if r["people_tokens"] else ()
        # Note: The plan says "groups identical token-sets". 
        # If people_tokens is [[...]], we take the first inner list as the signature.
        # If empty, it's an empty signature.
        signature_to_shots[sig].append(r["shot_id"])

    # Create clusters
    clusters = []
    # Sort signatures: The plan says "stable sorted by signature then first shot_id"
    # Since we want person_01, person_02... we need a deterministic order.
    # We'll sort the signatures themselves to be consistent.
    sorted_signatures = sorted(signature_to_shots.keys())
    
    person_counter = 1
    for sig in sorted_signatures:
        shot_ids = sorted(signature_to_shots[sig])
        clusters.append({
            "person_id": f"person_{person_counter:02d}",
            "signature": list(sig),
            "shot_ids": shot_ids
        })
        person_counter += 1

    # The requirement says "stable sorted by signature then first shot_id".
    # Our sorting of signatures handles the 'signature' part.
    # We already sorted shot_ids within each cluster.
    return clusters
