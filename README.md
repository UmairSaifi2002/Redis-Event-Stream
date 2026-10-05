# Redis-Event-Stream

# Redis as Event Streaming Platform — Mukammal Guftagu

Aaiye, ab hum Redis ka **chautha aur sabse advanced** use case samajhte hain. Pehle ek important baat clear kar dete hain — aapne **Streams jo padha, woh actually event streaming hi tha**. Lekin humne usko **message broker** ke perspective se dekha tha (acknowledgment, consumer groups). Ab hum **event streaming** ke perspective se dekhenge.

---

## 🎯 Pehle Ek Confusion Clear Karein

Redis ke 4 use cases:

| Use Case | Kya hai | Humne kya padha |
|---|---|---|
| **Database** | Primary data store | ❌ Nahi (SQLite use kiya) |
| **Cache** | Fast temporary storage | ✅ Search cache |
| **Message Broker** | Messages bhejna/lena | ✅ Pub/Sub, List Queue, Streams (partially) |
| **Event Streaming Platform** | Events ka permanent log | ⚠️ Streams ke saath touch kiya, ab detail |

**Confusion yeh hai:** Redis Streams **dono** kaam kar sakta hai:
- **Message Broker** ki tarah — consumers messages utha ke process karein, ack karein
- **Event Streaming Platform** ki tarah — events ka **permanent, replayable log** maintain karein

**Farq perspective ka hai:**
- **Message broker mindset:** "Message process ho gaya? Toh theek. Delete kar do."
- **Event streaming mindset:** "Event **hamesha** rehna chahiye. Log ek **source of truth** hai. Log se **kuch bhi reconstruct** kar sakte ho."

---

## 🧠 Event Streaming Kya Hota Hai

Chalo simple sawaal se shuru karte hain:

> **"Event" kya hota hai?**

Event ek **cheez jo hui** — past tense. "Order placed hua", "User signed up hua", "Payment failed hua", "Product viewed hua".

**Traditional database approach:**

```
User ne profile update kiya
    ↓
UPDATE users SET name='X' WHERE id=42
    ↓
Purana naam GAYA. Sirf naya naam rehta hai.
```

**Yeh problem hai:** Aapko nahi pata ki kal kya hua tha. History nahi hai.

**Event streaming approach:**

```
User ne profile update kiya
    ↓
Event log mein likho: "user_name_changed { id: 42, old: 'Y', new: 'X', at: '...' }"
    ↓
Event log append-only hai. Purana event bhi rehta hai, naya bhi.
```

Ab aap **poori history** dekh sakte ho, replay kar sakte ho, time-travel kar sakte ho.

---

## 🏗️ Event Streaming Ke Core Concepts

### Concept 1: Event Log (Append-Only)

```
Time →→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→

Event 1: user_signed_up      (10:00)
Event 2: order_placed        (10:05)
Event 3: payment_successful  (10:06)
Event 4: order_shipped       (14:00)
Event 5: order_delivered     (18:00)
Event 6: user_name_changed   (next day)
...
```

- **Kabhi delete nahi hota** (unless explicitly trim karo)
- **Kabhi modify nahi hota** — history immutable hai
- **Hamesha end mein append hota hai**
- **Chronological order** guaranteed

### Concept 2: Events as Source of Truth

Traditional: "Current state" database mein hota hai, aur log sirf backup hai.

Event streaming: **Log source of truth hai. Current state log se derive hota hai.**

```
Order events log → replay karke current order state banao
              ↓
"Order #42 abhi SHIPPED state mein hai"
```

**Fayde:**
- **Audit trail** — poora history
- **Time travel** — "kal 3 baje kya state thi?"
- **Replay** — bugs fix karke log dobara process karo
- **Multiple views** — same log se alag-alag projections banao

### Concept 3: Multiple Independent Consumers

Ek hi event log se multiple systems padh sakte hain, **independently**:

```
                    Event Log: "orders"
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   Analytics         Billing Service    Notification
   Service           (apni speed)       Service
   (dashboard)       (invoices)         (emails)
```

Har consumer apni speed se padh sakta hai. Ek slow hai toh doosre wait nahi karte.

**Yeh message broker se alag hai** — message broker mein usually ek consumer hota hai per message. Event streaming mein **saare consumers** same events padhte hain.

---

## 🎯 Event Streaming vs Message Broker — Bunyadi Farq

| Pehlu | Message Broker | Event Streaming |
|---|---|---|
| **Data ka nature** | Message (task, command) | Event (fact, "kuch hua") |
| **Lifetime** | Consume hone ke baad delete | Permanent (log rehta hai) |
| **Consumers** | Ek message, ek consumer | Ek event, saare consumers |
| **Replay** | Nahi | Haan — critical feature |
| **Ordering** | Best-effort | Guaranteed per stream |
| **Use case** | "Yeh kaam karo" | "Yeh hua — jo karna hai karo" |
| **Example** | Email bhejo | User signed up |

**Analogy:**

- **Message Broker** = **WhatsApp group** — message bheja, log padh liya, aage scroll kar diya. Purane messages important nahi.
- **Event Streaming** = **Bank passbook** — har transaction permanently likhi hai. Kabhi bhi wapas dekh sakte ho.

---

## 🏢 Real-World Event Streaming Examples

### Example 1: E-commerce Order Lifecycle

Ek order **multiple events** generate karta hai:

```
1. order_created       {order_id: 42, user: 7, items: [...], total: 599}
2. payment_initiated   {order_id: 42, method: "UPI", amount: 599}
3. payment_successful  {order_id: 42, txn_id: "ABC123", at: "10:06"}
4. inventory_reserved  {order_id: 42, warehouse: "Mumbai", items: [...]}
5. order_confirmed     {order_id: 42, eta: "2 days"}
6. order_shipped       {order_id: 42, tracking: "XYZ", at: "14:00"}
7. order_delivered     {order_id: 42, at: "18:00"}
```

Iss log se aap:
- **Current state** nikaal sakte ho — "Order #42 delivered hai"
- **History** dekh sakte ho — "Kis time pe kya hua"
- **Analytics** chala sakte ho — "Average delivery time kya hai"
- **Customer support** dekh sakta hai — "Iss order mein kya-kya hua"
- **Debugging** — "Payment fail kyun hua tha?"

### Example 2: Banking Transactions

```
1. account_created      {account: "A123", owner: "Alice"}
2. deposit              {account: "A123", amount: 10000}
3. withdrawal           {account: "A123", amount: 3000}
4. transfer_out         {from: "A123", to: "B456", amount: 2000}
5. interest_credited    {account: "A123", amount: 50}
```

**Balance** = replay karke calculate karo = `10000 - 3000 - 2000 + 50 = 5050`

**Fayda:** Kabhi bhi kisi bhi time ka balance nikaal sakte ho. Audit ke liye perfect.

### Example 3: User Activity Tracking

```
1. user_signed_up       {user: 42, source: "google_ads"}
2. viewed_product       {user: 42, product: 100}
3. added_to_cart        {user: 42, product: 100}
4. viewed_product       {user: 42, product: 205}
5. purchased            {user: 42, order: 500}
```

Iss se:
- **Recommendation engine** — kya suggest karein
- **Funnel analysis** — kitne users convert hue
- **Retargeting** — cart abandon karne walon ko email
- **A/B testing** — kaunsa flow better perform karta hai

---

## 🏛️ Event Streaming Ke Architecture Patterns

Ab yahan asli maza hai. Event streaming se **teen bade patterns** banate hain.

### Pattern 1: Event Sourcing

**Traditional approach:** Current state store karte hain. Update hua toh purana overwrite.

```python
# Traditional
user.name = "Alice Smith"   # purana naam kho gaya
```

**Event Sourcing approach:** Events store karte hain, current state **derive** karte hain.

```python
# Event Sourcing
events = [
    {"type": "user_created", "name": "Alice"},
    {"type": "name_changed", "old": "Alice", "new": "Alice Smith"},
    {"type": "email_changed", "old": "a@x.com", "new": "alice@y.com"},
]

# Current state calculate karo
state = {}
for event in events:
    if event["type"] == "user_created":
        state["name"] = event["name"]
    elif event["type"] == "name_changed":
        state["name"] = event["new"]
    elif event["type"] == "email_changed":
        state["email"] = event["new"]

# Result: {"name": "Alice Smith", "email": "alice@y.com"}
```

**Fayde:**
- **Audit trail** — kaun, kab, kya badla
- **Time travel** — kisi bhi point ka state reconstruct
- **Replay** — bug fix karke events dobara process karo
- **Event-driven integrations** — doosri services events sun sakti hain

**Nuksaan:**
- **Complexity** — state calculate karna thoda mushkil
- **Storage** — events store karna zyada space
- **Snapshots** — bahut events ho jaayein toh performance ke liye snapshots lene padte hain

### Pattern 2: CQRS (Command Query Responsibility Segregation)

**Idea:** Read aur Write ko alag karo.

```
Writes → Event Log → Reads
              │
              ├──► View 1: "Orders by user"
              ├──► View 2: "Orders by status"  
              └──► View 3: "Revenue dashboard"
```

**Traditional:** Ek database, ek schema, sab queries wahi.

**CQRS:** Events log mein likho. Phir **projections** banao — alag-alag views jo events ko consume karke optimize hote hain.

**Real example:**

```
Event log: "orders"
    │
    ├──► Redis Hash: "order:42" → current state of order 42
    ├──► Redis Sorted Set: "orders_by_date" → ranking by timestamp
    ├──► Redis Set: "user:7:orders" → all orders of user 7
    └──► Redis Stream: "analytics:orders" → real-time analytics feed
```

**Fayda:**
- **Read optimized** — har view apne use case ke liye optimized
- **Independent scaling** — reads aur writes alag scale
- **Multiple views** — same event log se kuch bhi project kar sakte ho

### Pattern 3: Event-Driven Microservices

```
Order Service ──► Event Log "orders" ──► Payment Service
                                    ├──► Inventory Service
                                    ├──► Notification Service
                                    └──► Analytics Service
```

Har service **independently** events consume karti hai. Naya service add karo — bas event log subscribe karo. Existing services ko touch nahi karna.

**Fayde:**
- **Loose coupling** — services ek dusre ko nahi jaante
- **Independent deployment** — ek service update karo, baaki unaffected
- **Natural scaling** — har service apni speed se
- **Resilience** — ek service down, baaki chalte rehte hain

---

## 🎯 Ab Redis Mein Event Streaming — Practical

Chalo ab dekhte hain kaise Redis **event streaming platform** ki tarah use hota hai.

### Key Features Redis Mein

| Feature | Redis Command | Kyun Important |
|---|---|---|
| **Append-only log** | `XADD` | Events permanent likhte hain |
| **Range reads** | `XRANGE`, `XREVRANGE` | History padho |
| **Replay from ID** | `XREAD STREAMS orders 0` | Shuru se replay |
| **Consumer groups** | `XGROUP`, `XREADGROUP` | Multiple independent readers |
| **Acknowledgment** | `XACK` | Track processing |
| **Pending list** | `XPENDING` | Stuck events dekho |
| **Claim/recover** | `XCLAIM`, `XAUTOCLAIM` | Crash recovery |
| **Trim** | `XTRIM`, `MAXLEN` | Bounded memory |
| **Blocking reads** | `XREAD BLOCK` | Real-time processing |

Redis Streams **Kafka ka lightweight version** hai. Same patterns, kam complexity.

---

## 💻 Code — Event Streaming Ka Complete Example

Chalo ek **Order Event Sourcing** system banate hain. Yeh code dikhata hai:
- Events append karna
- Current state derive karna (replay se)
- Multiple consumers
- Analytics projection

### 📁 Project Structure

```
event-streaming-demo/
├── event_store.py      # Event log wrapper
├── order_service.py    # Writes events
├── state_projector.py  # Builds current state from events
├── analytics.py        # Separate consumer for analytics
└── replay_demo.py      # Time-travel / replay demo
```

### 📁 `event_store.py` — Event Log Wrapper

```python
"""
Event store — append-only log wrapper around Redis Streams.
Yeh event sourcing ka core hai.
"""
import time
import json
import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


class EventStore:
    """
    Events ko Redis Stream mein store karta hai.
    Sab events permanently rehte hain (till trim).
    """
    
    def __init__(self, stream_name: str = "events"):
        self.stream = stream_name
    
    def append(self, event_type: str, aggregate_id: str, data: dict) -> str:
        """
        Naya event append karo.
        
        Args:
            event_type: "order_created", "payment_successful", etc.
            aggregate_id: "order:42", "user:7" — kis entity ka event
            data: event ka payload
        
        Returns:
            Redis-generated event ID (timestamp-based)
        """
        event = {
            "event_type": event_type,
            "aggregate_id": aggregate_id,
            "timestamp": str(int(time.time() * 1000)),  # ms
            "data": json.dumps(data),  # nested dict → string
        }
        
        # XADD — stream mein append karo
        # maxlen se stream bounded rakho (production mein zaroori)
        event_id = r.xadd(
            self.stream,
            event,
            maxlen=100000,
            approximate=True
        )
        return event_id
    
    def read_all(self, from_id: str = "0") -> list:
        """
        Saare events padho — shuru se ya given ID se.
        Yeh replay ke liye hai.
        """
        events = r.xrange(self.stream, min=from_id, max="+")
        return [self._parse(eid, fields) for eid, fields in events]
    
    def read_by_aggregate(self, aggregate_id: str) -> list:
        """
        Sirf ek entity ke events padho.
        Replay karke us entity ka current state banao.
        """
        all_events = self.read_all()
        return [e for e in all_events if e["aggregate_id"] == aggregate_id]
    
    def _parse(self, event_id: str, fields: dict) -> dict:
        """Redis response ko clean dict mein convert karo."""
        return {
            "event_id": event_id,
            "event_type": fields["event_type"],
            "aggregate_id": fields["aggregate_id"],
            "timestamp": int(fields["timestamp"]),
            "data": json.loads(fields["data"]),
        }
    
    def length(self) -> int:
        """Kitne events log mein hain."""
        return r.xlen(self.stream)
    
    def trim(self, keep: int):
        """Log ko bounded rakho — sirf latest N events."""
        r.xtrim(self.stream, maxlen=keep, approximate=True)
```

**Urdulish + Comments:**

- **`append()`** — Naya event likhta hai. `XADD` se. `maxlen` se bounded memory.
- **`read_all()`** — Poora log padhta hai. Replay ke liye.
- **`read_by_aggregate()`** — Ek entity ke saare events. Jaise "order:42 ke saare events".
- **`_parse()`** — Redis response mein strings hote hain, iss liye JSON parse karke clean dict banate hain.
- **`trim()`** — Log ko chhota rakho. Production mein zaroori (warna memory khatam).

### 📁 `order_service.py` — Event Writer

```python
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
```

**Urdulish:**

Har function ek **event** likhta hai. Yeh traditional DB update **nahi** hai. Yeh **fact** likh raha hai ki "yeh hua".

- `create_order` → `order_created` event
- `payment_successful` → `payment_successful` event
- etc.

**Important:** Hum **state update nahi kar rahe**. Hum **event log** kar rahe hain. Current state **derive** karenge events se.

### 📁 `state_projector.py` — Events Se State Banao

```python
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
```

**Urdulish — yeh samajhna important hai:**

Yeh function **events ko fold karke** state banata hai. Jaise:

```
Events:  [order_created, payment_successful, order_shipped]
                │              │                  │
                ▼              ▼                  ▼
State:   {status: created} → {paid: true} → {shipped: true}
```

Har event **state ko modify karta hai**. Final state = fold(events).

**Yeh pure functional programming hai.** Events immutable, state derived.

### 📁 `analytics.py` — Independent Consumer

```python
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
```

**Urdulish:**

Yeh **independent consumer group** hai. Same `events` stream se padh raha hai, lekin **apni separate copy** ki tarah. Analytics group ke read karne se doosre groups pe koi asar nahi.

**Yeh event streaming ka core hai** — multiple independent consumers.

### 📁 `replay_demo.py` — Time Travel

```python
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
```

**Urdulish:**

Replay ka matlab: **purane events ko dobara padho aur process karo**. Yeh event streaming ka killer feature hai.

**Real-world use cases:**
- **Naya microservice** add karo → usko saari history chahiye → replay
- **Bug fix** karo projection mein → events dobara process karo → correct state
- **Analytics** — "pichle mahine kya hua" → us range ka replay
- **Debugging** — "order #42 ke saath kya-kya hua" → us order ke events

---

## 📊 Output — Real Demo

### 1. Order Service Chalao

```bash
python order_service.py
```

Output:
```
=== Simulating an order lifecycle ===

📝 order_created      → order:1001
💳 payment_successful → order:1001
🚚 order_shipped      → order:1001
✅ order_delivered    → order:1001

=== Another order ===

📝 order_created      → order:1002
💳 payment_successful → order:1002

📊 Total events in log: 6
```

### 2. State Projector Chalao

```bash
python state_projector.py
```

Output:
```
=== Current State of Order 1001 ===

  order_id     : 1001
  status       : delivered
  user_id      : 42
  total        : 599
  paid         : True
  shipped      : True
  delivered    : True
  tracking     : BD-12345

=== Current State of Order 1002 ===

  order_id     : 1002
  status       : paid
  user_id      : 17
  total        : 1200
  paid         : True
  shipped      : False
  delivered    : False
  tracking     : None

=== All Orders (single-pass projection) ===

  Order 1001: delivered  ($599)
  Order 1002: paid       ($1200)
```

**Dekha?** Humne **kabhi state store nahi ki**. Humne **events** store kiye. State **derive** ki replay se.

### 3. Analytics Chalao (Dusre Terminal Mein)

```bash
python analytics.py
```

Output:
```
✅ Created group analytics_group

📊 Analytics consumer running...
   Reading from 'events' stream independently
   (This does NOT affect other consumers)
```

Lekin analytics ko **turant kuch nahi milega** kyunki humne `id="0"` set kiya tha — matlab shuru se padho. Toh analytics **6 purane events** process karega:

```
📊 [ANALYTICS] New order: order:1001
📊 [ANALYTICS] Payment done: order:1001
📊 [ANALYTICS] Order delivered: order:1001
📊 [ANALYTICS] New order: order:1002
📊 [ANALYTICS] Payment done: order:1002
```

### 4. Naya Order Daalo

Ab `order_service.py` chalao dobara, ya manually `XADD` karo:

```bash
redis-cli
XADD events * event_type order_created aggregate_id order:1003 timestamp 1704067210000 data '{"order_id":1003,"user_id":99,"total":800}'
```

**Analytics terminal mein turant dikhega:**
```
📊 [ANALYTICS] New order: order:1003
```

**State projector terminal mein:**
```bash
python state_projector.py
```

Ab Order 1003 bhi dikhega:
```
Order 1003: created  ($800)
```

### 5. Replay Demo

```bash
python replay_demo.py
```

Output:
```
=== REPLAY: Processing all events from start ===

Total events: 7

  [1704067200000-0] order_created       order:1001  (ts=1704067200000)
  [1704067201000-0] payment_successful  order:1001  (ts=1704067201000)
  [1704067202000-0] order_shipped       order:1001  (ts=1704067202000)
  [1704067203000-0] order_delivered     order:1001  (ts=1704067203000)
  [1704067204000-0] order_created       order:1002  (ts=1704067204000)
  [1704067205000-0] payment_successful  order:1002  (ts=1704067205000)
  [1704067210000-0] order_created       order:1003  (ts=1704067210000)

=== REPLAY: From event 1704067202000-0 onwards ===

Found 5 events from that point

  order_shipped       order:1001
  order_delivered     order:1001
  order_created       order:1002
  payment_successful  order:1002
  order_created       order:1003
```

**Yeh hai event streaming.** Poori history hai, replay possible, time-travel possible.

---

## 🎯 Event Streaming Ke Real Fayde

### 1. Audit Trail (Compliance)

Har cheez ka record hai. Tax, legal, security audits ke liye perfect.

**Example:** Bank kehte hain "show me all transactions of account A123 in last 5 years" → event log se nikaal lo. Koi data loss nahi.

### 2. Time Travel / Debugging

"Pichle Tuesday 3 baje kya hua tha?" → events replay karo us time tak.

**Example:** Bug report aayi "order #42 wrong amount dikha raha hai". → us order ke events replay karo → pata chala payment event mein amount 599 tha, but order_created mein 599 tha. Bug mil gaya.

### 3. Event-Driven Architecture

Services ek dusre ko **jaante nahi**. Bas events se communicate karte hain.

**Example:** Naya "recommendation service" launch karo. Bas `user_viewed_product` events subscribe karo. Baaki koi service touch nahi karni.

### 4. Multiple Projections

Ek log se kuch bhi banao:
- **Redis Hash** — current order state
- **Sorted Set** — orders by date
- **Search index** — searchable orders
- **Analytics** — dashboards

**Example:** E-commerce mein "orders by user", "orders by status", "orders by region" — sab ek hi event log se.

### 5. Replay for Bug Fixes

Code mein bug tha, projections galat the. Fix karo → events replay karo → correct projections.

**Example:** Analytics bug tha — "shipped orders count double ho raha tha". Fix karo, events replay karo, correct count mil jaayega.

### 6. Real-Time + Historical

Same stream se:
- **Real-time** — naye events ke liye `XREAD BLOCK`
- **Historical** — purane events ke liye `XRANGE`

**Example:** Dashboard real-time updates dikhaye (naye events), aur "past 30 days" queries bhi support kare (purane events).

---

## ⚠️ Event Streaming Ke Challenges

### 1. Storage Growth

Events kabhi delete nahi hote → unlimited growth.

**Solution:** `XTRIM`, snapshots, archival to cold storage.

```python
# Keep only latest 1 million events
r.xtrim("events", maxlen=1_000_000, approximate=True)

# Or: archive old events to S3/database, then trim
```

### 2. Event Schema Evolution

Events ka format badalta hai over time. Purane events kaise handle karein?

**Solution:** Versioning.

```python
{
    "event_type": "order_created",
    "event_version": 2,   # schema version
    "data": {...}
}
```

### 3. Idempotency

Duplicate events aa sakte hain (network retries). Same event dobara process hone pe kya karein?

**Solution:** Idempotency keys.

```python
def process_event(event_id: str, data: dict):
    # Check if we already processed this
    if r.sismember("processed_events", event_id):
        return   # skip duplicate
    # Process
    do_work(data)
    r.sadd("processed_events", event_id)
```

### 4. Ordering Across Aggregates

Ek order ke events ordered hain. Lekin do alag orders ke events ke beech global order nahi hota.

**Solution:** Aggregate-level ordering usually kaafi hai. Global ordering chahiye toh partition by key.

### 5. Consumer Lag

Slow consumer peeche chalta rehta hai. Monitor karna zaroori.

**Solution:** Consumer group monitoring.

```python
info = r.xinfo_groups("events")
for g in info:
    print(f"Group {g['name']}: pending={g['pending']}, lag=...")
```

---

## 📊 Redis Event Streaming vs Kafka

Yeh comparison important hai kyunki log yeh poochhte hain.

| Feature | Redis Streams | Kafka |
|---|---|---|
| **Setup** | Simple (already Redis) | Complex (ZooKeeper/KRaft) |
| **Throughput** | High (millions/sec) | Very high (billions/sec) |
| **Storage** | In-memory (limited) | Disk (unlimited) |
| **Retention** | Limited by RAM | Days/weeks/months |
| **Partitioning** | Manual (multiple streams) | Built-in |
| **Replication** | Redis replication | Built-in |
| **Ecosystem** | Small | Huge (Kafka Connect, Streams) |
| **Latency** | Sub-millisecond | Milliseconds |
| **Best for** | Real-time, small-medium scale | Large scale, long retention |

**Rule of thumb:**
- **Small-medium scale** (< 1M events/day) → Redis Streams
- **Large scale** (> 1M events/day, long retention) → Kafka
- **Already Redis use kar rahe ho** → Redis Streams se shuru karo
- **Long-term audit** chahiye → Kafka better

---

## 🎓 Aapne Kya Seekha

Aaj aapne samjha:

1. **Event Streaming** kya hai — events ka permanent, append-only log
2. **Events as source of truth** — state derive karo, store mat karo
3. **Event Sourcing pattern** — current state = fold(events)
4. **CQRS pattern** — same events se multiple views
5. **Event-driven microservices** — services events se communicate karein
6. **Redis Streams as event platform** — `XADD`, `XRANGE`, consumer groups
7. **Replay** — purane events dobara process karo
8. **Time travel** — kisi bhi point ka state reconstruct
9. **Multiple independent consumers** — analytics, notifications, projections sab alag
10. **Event streaming vs message broker** — permanent log vs ephemeral messages

---

## 🎯 Kab Redis Event Streaming Use Karo

### ✅ Karo jab:
- **Audit trail** chahiye — kaun, kab, kya kiya
- **Event-driven architecture** bana rahe ho
- **Multiple consumers** same events pe kaam karein
- **Replay** chahiye (bug fix, new service)
- **Real-time + historical** dono chahiye
- **Already Redis** use kar rahe ho
- **Small-medium scale** (millions of events/day tak)

### ❌ Mat karo jab:
- **Very high throughput** chahiye (billions/day) → Kafka
- **Long retention** (months/years) → Kafka
- **Very large events** (MBs per event) → Kafka
- **Strong ordering** across partitions chahiye → Kafka
- **Complex routing** (topics, filters) chahiye → Kafka/RabbitMQ

---

## ✅ Aapke Manager Ko Kaise Samjhao

Agar manager poochhe "Event Streaming kya hai?", toh aise bolo:

> **"Event streaming ek approach hai jahan hum 'current state' store nahi karte, balki 'events' store karte hain. Jaise bank ki passbook — har transaction likhi rehti hai. Iss se humein:**
>
> - **Audit trail** milta hai — kuch bhi miss nahi hota
> - **Replay** kar sakte hain — bugs fix karke dobara process karo
> - **Time travel** — kisi bhi point ka state dekh sakte ho
> - **Multiple views** — ek hi log se kuch bhi banao
> - **Event-driven architecture** — services ek dusre se decoupled
>
> **Redis Streams isko implement karta hai.** XADD se events likho, XRANGE se history padho, consumer groups se multiple independent consumers banao. Yeh Kafka ka lightweight version hai — simple, fast, aur already humare Redis infrastructure pe chal jaayega."

---

## 🚀 Aage Kya

Ab aapko **Redis ke saare 4 use cases** ka practical knowledge hai:

| Use Case | Mastery | Real-World Ready? |
|---|---|---|
| **Cache** | ✅ | ✅ |
| **Message Broker (Pub/Sub)** | ✅ | ✅ |
| **Message Broker (List Queue)** | ✅ | ✅ |
| **Message Broker (Streams)** | ✅ | ✅ |
| **Event Streaming** | ✅ | ✅ |

**Possible next steps:**
1. **Complete project** — end-to-end system banao (cache + broker + event streaming)
2. **Production hardening** — monitoring, alerts, dead letter queue
3. **Redis Cluster** — sharding, high availability
4. **Redis modules** — RediSearch, RedisJSON, RedisTimeSeries
5. **Idempotency + exactly-once** semantics

Batao, kya karna hai next? Ya koi specific question hai iss topic pe? 🚀