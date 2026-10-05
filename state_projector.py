"""
State projector — events ko replay karke current state nikalta hai.
Yeh event sourcing ka "read" side hai.
"""
from collections import defaultdict
from event_store import EventStore

store = EventStore("events")


def project_order_state(order_id: int) -> dict:
    """
    Ek order ke saare events padho aur current state calculate karo.
    Yeh literally event sourcing hai.
    """
    events = store.read_by_aggregate(f"order:{order_id}")
    
    # Initial state — kuch nahi pata
    state = {
        "order_id": order_id,
        "status": "unknown",
        "user_id": None,
        "total": 0,
        "paid": False,
        "shipped": False,
        "delivered": False,
        "tracking": None,
    }
    
    # Har event ko apply karo (fold pattern)
    for event in events:
        etype = event["event_type"]
        data = event["data"]
        
        if etype == "order_created":
            state["status"] = "created"
            state["user_id"] = data["user_id"]
            state["total"] = data["total"]
        
        elif etype == "payment_successful":
            state["status"] = "paid"
            state["paid"] = True
        
        elif etype == "order_shipped":
            state["status"] = "shipped"
            state["shipped"] = True
            state["tracking"] = data["tracking"]
        
        elif etype == "order_delivered":
            state["status"] = "delivered"
            state["delivered"] = True
    
    return state


def project_all_orders() -> dict:
    """
    Saare events ek baar padho, sab orders ka state banao.
    Efficient version — ek hi pass mein.
    """
    all_events = store.read_all()
    orders = defaultdict(lambda: {
        "status": "unknown", "total": 0,
        "user_id": None, "paid": False
    })
    
    for event in all_events:
        agg_id = event["aggregate_id"]
        if not agg_id.startswith("order:"):
            continue
        
        order_id = int(agg_id.split(":")[1])
        etype = event["event_type"]
        data = event["data"]
        
        # Same fold logic, but iterating once
        if etype == "order_created":
            orders[order_id]["status"] = "created"
            orders[order_id]["user_id"] = data["user_id"]
            orders[order_id]["total"] = data["total"]
        elif etype == "payment_successful":
            orders[order_id]["status"] = "paid"
            orders[order_id]["paid"] = True
        elif etype == "order_shipped":
            orders[order_id]["status"] = "shipped"
        elif etype == "order_delivered":
            orders[order_id]["status"] = "delivered"
    
    return dict(orders)


if __name__ == "__main__":
    print("\n=== Current State of Order 1001 ===\n")
    state = project_order_state(1001)
    for k, v in state.items():
        print(f"  {k:12} : {v}")
    
    print("\n=== Current State of Order 1002 ===\n")
    state = project_order_state(1002)
    for k, v in state.items():
        print(f"  {k:12} : {v}")
    
    print("\n=== All Orders (single-pass projection) ===\n")
    all_orders = project_all_orders()
    for oid, st in all_orders.items():
        print(f"  Order {oid}: {st['status']:10} (${st['total']})")


        