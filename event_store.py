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



        