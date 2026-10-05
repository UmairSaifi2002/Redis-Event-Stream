"""
Replay demo — events ko dobara process karo.
Yeh event streaming ka sabse bada fayda hai.
"""
from event_store import EventStore

store = EventStore("events")


def replay_from_scratch():
    """
    Poora log dobara padho — jaise pehli baar.
    Yeh tab kaam aata hai jab:
    - Naya service add karo (usko saari history chahiye)
    - Bug fix karke projection dobara banao
    """
    print("\n=== REPLAY: Processing all events from start ===\n")
    
    all_events = store.read_all()
    print(f"Total events: {len(all_events)}\n")
    
    for event in all_events:
        eid = event["event_id"]
        etype = event["event_type"]
        agg = event["aggregate_id"]
        ts = event["timestamp"]
        
        print(f"  [{eid}] {etype:20} {agg}  (ts={ts})")


def replay_from_point(from_event_id: str):
    """
    Ek specific point se replay — time travel.
    Jaise: "order 1001 ke baad kya hua?"
    """
    print(f"\n=== REPLAY: From event {from_event_id} onwards ===\n")
    
    events = store.read_all(from_id=from_event_id)
    print(f"Found {len(events)} events from that point\n")
    
    for event in events:
        print(f"  {event['event_type']:20} {event['aggregate_id']}")


if __name__ == "__main__":
    replay_from_scratch()
    
    # Time travel — 3rd event ke baad se
    all_events = store.read_all()
    if len(all_events) >= 3:
        third_id = all_events[2]["event_id"]
        replay_from_point(third_id)


        