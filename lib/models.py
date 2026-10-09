from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class CaptureMeta:
    id: str
    timestamp: str
    type: str # 'note', 'link', 'file'
    source: str
    original_filename: Optional[str] = None
    content_hash: Optional[str] = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "type": self.type,
            "source": self.source,
            "original_filename": self.original_filename,
            "content_hash": self.content_hash
        }

@dataclass
class CaptureResult:
    id: str
    path: str
    type: str

@dataclass
class WikiNote:
    id: str
    raw_id: str
    para: str
    tags: List[str]
    summary: str
    created: str
    links: List[str]
    body: str

@dataclass
class GraphNode:
    id: str
    label: str
    para: str
    tags: List[str]
    summary: str
    content_preview: str
    group: str
    
    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "para": self.para,
            "tags": self.tags,
            "summary": self.summary,
            "content_preview": self.content_preview,
            "group": self.group
        }

@dataclass
class GraphEdge:
    source: str
    target: str
    weight: float
    type: str
    
    def to_dict(self):
        return {
            "source": self.source,
            "target": self.target,
            "weight": self.weight,
            "type": self.type
        }

@dataclass
class AskResult:
    answer: str
    sources: List[Dict[str, Any]]
