import faiss
import numpy as np
import json
import os
from sentence_transformers import SentenceTransformer

class OmniMemory:
    def __init__(self, db_folder='memory_db'):
        print("🧠 Initializing FAISS Vector Memory...")
        # Using a very lightweight embedding model (runs easily on laptops)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = self.encoder.get_sentence_embedding_dimension()
        
        # Initialize FAISS Index
        self.index = faiss.IndexFlatL2(self.dimension)
        self.db_folder = db_folder
        self.metadata = []  # Stores the actual conversation text
        
        if not os.path.exists(db_folder):
            os.makedirs(db_folder)
            
    def store_interaction(self, session_id, user_query, ai_response, diagram_context=""):
        """Phase 5: Store Conversation and Embeddings"""
        # 1. Format the memory block
        memory_text = f"Session: {session_id} | Context: {diagram_context} | User asked: {user_query} | AI answered: {ai_response}"
        
        # 2. Convert text to a dense vector embedding
        vector = self.encoder.encode([memory_text])
        
        # 3. Add to FAISS Database
        self.index.add(np.array(vector).astype('float32'))
        self.metadata.append(memory_text)
        
        print(f"✅ Memory stored successfully! Total memories: {self.index.ntotal}")

    def retrieve_context(self, current_query, top_k=2):
        """Phase 3: Retrieve past knowledge for the AI prompt"""
        if self.index.ntotal == 0:
            return "No previous memory."
            
        print(f"🔍 Searching memory for: '{current_query}'...")
        
        # 1. Convert current question to vector
        query_vector = self.encoder.encode([current_query])
        
        # 2. Search FAISS for the closest mathematical match
        distances, indices = self.index.search(np.array(query_vector).astype('float32'), top_k)
        
        # 3. Extract the matching text
        retrieved_memories = []
        for i in indices[0]:
            if i != -1 and i < len(self.metadata):
                retrieved_memories.append(self.metadata[i])
                
        return "\n".join(retrieved_memories)

# ==========================================
# 🧪 TEST THE MEMORY PIPELINE
# ==========================================
if __name__ == "__main__":
    memory = OmniMemory()
    
    # 1. Simulate saving a conversation from "Yesterday"
    print("\n--- Saving Yesterday's Chat ---")
    memory.store_interaction(
        session_id="chat_001",
        user_query="What is the value of Resistor 1?",
        ai_response="Based on the diagram, Resistor 1 is 100 Ohms.",
        diagram_context="Simple Series Circuit"
    )
    
    # 2. Simulate the user asking a follow-up question "Today"
    print("\n--- Retrieving Today ---")
    test_query = "Wait, what was the value of that resistor we looked at yesterday?"
    
    past_context = memory.retrieve_context(test_query)
    
    print(f"\nContext found for AI to use:\n{past_context}")