"""
Order service — events likhta hai event log mein.
Traditional database ki jagah, hum events likh rahe hain.
"""
import random
from event_store import EventStore

store = EventStore("events")


def create_order(order_id: int, user_id: int, total: float):
    """Order create hone ka event."""
    store.append(
        event_type="order_created",
        aggregate_id=f"order:{order_id}",
        data={
            "order_id": order_id,
            "user_id": user_id,
            "total": total,
            "items": random.randint(1, 5),
        }
    )
    print(f"📝 order_created      → order:{order_id}")


def payment_successful(order_id: int, txn_id: str):
    """Payment successful hone ka event."""
    store.append(
        event_type="payment_successful",
        aggregate_id=f"order:{order_id}",
        data={"txn_id": txn_id, "method": "UPI"}
    )
    print(f"💳 payment_successful → order:{order_id}")


def order_shipped(order_id: int, tracking: str):
    """Order ship hone ka event."""
    store.append(
        event_type="order_shipped",
        aggregate_id=f"order:{order_id}",
        data={"tracking": tracking, "carrier": "BlueDart"}
    )
    print(f"🚚 order_shipped      → order:{order_id}")


def order_delivered(order_id: int):
    """Order deliver hone ka event."""
    store.append(
        event_type="order_delivered",
        aggregate_id=f"order:{order_id}",
        data={}
    )
    print(f"✅ order_delivered    → order:{order_id}")


if __name__ == "__main__":
    # Fresh start
    import redis
    r = redis.Redis(decode_responses=True)
    r.delete("events")
    
    print("\n=== Simulating an order lifecycle ===\n")
    
    # Order 1001 ka poora lifecycle
    create_order(1001, user_id=42, total=599)
    payment_successful(1001, txn_id="TXN-ABC")
    order_shipped(1001, tracking="BD-12345")
    order_delivered(1001)
    
    print("\n=== Another order ===\n")
    
    create_order(1002, user_id=17, total=1200)
    payment_successful(1002, txn_id="TXN-XYZ")
    # (not yet shipped)
    
    print(f"\n📊 Total events in log: {store.length()}")


    