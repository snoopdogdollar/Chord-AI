from dataclasses import dataclass


@dataclass(frozen=True)
class ChordEvent:
    start: float
    end: float
    chord: str
    confidence: float

    def to_dict(self) -> dict:
        return {
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "chord": self.chord,
            "confidence": round(self.confidence, 3),
        }
