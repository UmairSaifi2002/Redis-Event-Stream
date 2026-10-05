"""
Analytics consumer — independent consumer group jo
sirf analytics ke liye events padhta hai.
"""
import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

STREAM = "events"
GROUP = "analytics_group"
CONSUMER = "analytics-1"


def ensure_group():
    """Analytics group banao agar nahi hai."""
    try:
        r.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
        print(f"✅ Created group {GROUP}")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            print(f"ℹ️  Group {GROUP} already exists")
        else:
            raise


def process_events():
    """Analytics events padho aur process karo."""
    # XREADGROUP — naye messages padho
    response = r.xreadgroup(
        groupname=GROUP,
        consumername=CONSUMER,
        streams={STREAM: ">"},   # naye messages
        count=100,
        block=2000
    )
    
    if not response:
        return 0
    
    processed = 0
    for stream, messages in response:
        for msg_id, fields in messages:
            etype = fields["event_type"]
            agg_id = fields["aggregate_id"]
            
            # Analytics logic — kya track karein?
            if etype == "order_created":
                print(f"📊 [ANALYTICS] New order: {agg_id}")
            elif etype == "payment_successful":
                print(f"📊 [ANALYTICS] Payment done: {agg_id}")
            elif etype == "order_delivered":
                print(f"📊 [ANALYTICS] Order delivered: {agg_id}")
            
            # Acknowledge
            r.xack(STREAM, GROUP, msg_id)
            processed += 1
    
    return processed


if __name__ == "__main__":
    ensure_group()
    print("\n📊 Analytics consumer running...")
    print("   Reading from 'events' stream independently")
    print("   (This does NOT affect other consumers)\n")
    
    try:
        while True:
            n = process_events()
            if n == 0:
                print(".", end="", flush=True)
    except KeyboardInterrupt:
        print("\n👋 Analytics stopped.")


        