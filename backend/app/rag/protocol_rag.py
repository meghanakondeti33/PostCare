import re
import uuid
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.domain import Protocol, KnowledgeDocument, KnowledgeChunk

# Deterministic Clinical Concept Map for Lexical Expansion
CLINICAL_CONCEPT_MAP: Dict[str, Set[str]] = {
    "concept_cardiac_pain": {
        "pain", "angina", "ischemic", "ischemia", "chest", "pressure", 
        "discomfort", "tightness", "cardiac", "infarction", "myocardial", "heart"
    },
    "concept_dyspnea": {
        "breath", "breathing", "shortness", "dyspnea", "sob", "respiratory", 
        "suffocating", "gasping", "air"
    },
    "concept_edema": {
        "edema", "swelling", "swollen", "fluid", "weight", "edematous", "extremity"
    },
    "concept_fever": {
        "fever", "temperature", "febrile", "chills", "infection", "pyrexia"
    },
    "concept_medication": {
        "medication", "medicine", "pill", "adherence", "compliance", "prescription", 
        "dose", "antiplatelet", "aspirin"
    },
    "concept_outreach": {
        "outreach", "followup", "discharge", "postdischarge", "guidelines", "standard"
    }
}

def normalize_token(token: str) -> str:
    """Strip common English inflectional suffixes for simple deterministic stemming."""
    token = token.lower().strip()
    if len(token) > 4:
        for suffix in ("ing", "ed", "es", "s", "ly"):
            if token.endswith(suffix):
                return token[:-len(suffix)]
    return token

def tokenize_and_normalize(text: str) -> Set[str]:
    """Lowercase, strip punctuation, and normalize whitespace & tokens."""
    clean_text = re.sub(r"[^\w\s]", " ", text.lower())
    raw_tokens = clean_text.split()
    return {normalize_token(t) for t in raw_tokens if len(t) > 1}

def extract_clinical_concepts(tokens: Set[str]) -> Set[str]:
    """Map normalized tokens to canonical clinical concept identifiers."""
    triggered_concepts = set()
    for concept_id, terms in CLINICAL_CONCEPT_MAP.items():
        for term in terms:
            norm_term = normalize_token(term)
            if norm_term in tokens or any(norm_term in t for t in tokens):
                triggered_concepts.add(concept_id)
                break
    return triggered_concepts


class ProtocolRAGService:
    """
    Tenant-Isolated Protocol & Knowledge Retrieval Service.
    Enforces strict hospital_id boundary for vector and keyword search.
    Features deterministic text normalization and clinical concept mapping.
    """
    
    def __init__(self, db: AsyncSession, hospital_id: str):
        self.db = db
        self.hospital_id = hospital_id

    async def ingest_protocol_document(self, title: str, category: str, content: str, version: str = "1.0.0") -> str:
        doc_id = str(uuid.uuid4())
        doc = KnowledgeDocument(
            id=doc_id,
            hospital_id=self.hospital_id,
            title=title,
            category=category,
            content=content,
            version=version
        )
        self.db.add(doc)
        await self.db.flush()
        
        # Simple text chunking by paragraph / section
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        for idx, text in enumerate(paragraphs):
            chunk_id = str(uuid.uuid4())
            chunk = KnowledgeChunk(
                id=chunk_id,
                document_id=doc_id,
                hospital_id=self.hospital_id,
                chunk_index=idx,
                text=text,
                embedding_vector=None,
                metadata_json={"title": title, "version": version, "category": category}
            )
            self.db.add(chunk)
            
        await self.db.flush()
        return doc_id

    async def retrieve_protocol_evidence(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        # Fetch knowledge chunks strictly matching hospital_id
        stmt = select(KnowledgeChunk).where(KnowledgeChunk.hospital_id == self.hospital_id)
        res = await self.db.execute(stmt)
        chunks = res.scalars().all()
        
        query_tokens = tokenize_and_normalize(query)
        query_concepts = extract_clinical_concepts(query_tokens)
        
        scored = []
        for c in chunks:
            chunk_tokens = tokenize_and_normalize(c.text)
            chunk_concepts = extract_clinical_concepts(chunk_tokens)
            
            # Token overlap score
            token_overlap = len(query_tokens.intersection(chunk_tokens))
            token_score = token_overlap / max(len(query_tokens), 1.0)
            
            # Concept overlap score
            if query_concepts:
                concept_overlap = len(query_concepts.intersection(chunk_concepts))
                concept_score = concept_overlap / max(len(query_concepts), 1.0)
            else:
                concept_score = 0.0
                
            # Combined deterministic relevance score
            if query_concepts and concept_score > 0:
                final_score = min(1.0, 0.4 * token_score + 0.6 * concept_score + 0.1)
            else:
                final_score = min(1.0, token_score)
                
            scored.append((final_score, c))
            
        scored.sort(key=lambda x: x[0], reverse=True)
        top_matches = scored[:top_k]
        
        results = []
        for score, chunk in top_matches:
            meta = chunk.metadata_json or {}
            results.append({
                "document_id": chunk.document_id,
                "chunk_id": chunk.id,
                "title": meta.get("title", "Hospital Protocol"),
                "category": meta.get("category", "Clinical Guidelines"),
                "version": meta.get("version", "1.0.0"),
                "hospital_id": chunk.hospital_id,
                "score": round(score, 4),
                "text": chunk.text
            })
            
        return results
