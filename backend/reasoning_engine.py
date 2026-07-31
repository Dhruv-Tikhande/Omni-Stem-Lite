from memory_engine import OmniMemory
import time

class ReasoningEngine:
    def __init__(self):
        print("⚙️ Initializing Phase 3: Reasoning Engine...")
        self.memory = OmniMemory()
        
    def generate_final_response(self, session_id, user_query, vision_json):
        """
        Combines Vision Data + Past Memory + User Query to generate the final educational response.
        """
        print(f"\n[1] Retrieving Past Memory for Session: {session_id}...")
        # Get past context from Phase 5
        past_context = self.memory.retrieve_context(user_query)
        
        print("[2] Assembling the Master Prompt...")
        # This is the exact prompt structure that forces the LLM to act as an accessible tutor
        master_prompt = f"""
        You are an expert STEM Tutor for visually impaired students. 
        
        CURRENT DIAGRAM DATA (Phase 2 Vision Output):
        {vision_json}
        
        PAST CONVERSATION MEMORY (Phase 5 RAG):
        {past_context}
        
        USER QUESTION: 
        "{user_query}"
        
        INSTRUCTIONS:
        1. Answer the user's question directly based ONLY on the Diagram Data and Past Memory.
        2. Use clear, spatial language (top, bottom, connected to).
        3. Do not mention the "JSON" or "Memory" to the user. Speak naturally like a human tutor.
        4. Explain step-by-step.
        """
        
        print("[3] Sending to LLM (Simulated for Laptop)...")
        # NOTE: On your laptop, we simulate the LLM generation time. 
        # When you move to Colab, you will pass 'master_prompt' directly to Qwen2-VL here!
        time.sleep(1.5) 
        
        # Simulated LLM Response based on the prompt
        ai_response = f"Based on the diagram we are looking at, and remembering that yesterday we established the first resistor is 100 Ohms, the current flows in a series path directly to the LED at the bottom right."
        
        print("[4] Storing New Interaction to Memory...")
        # Save this new interaction so the AI remembers it for the NEXT question!
        self.memory.store_interaction(session_id, user_query, ai_response, vision_json)
        
        return ai_response

# ==========================================
# 🧪 TEST THE FULL LOGIC PIPELINE
# ==========================================
if __name__ == "__main__":
    engine = ReasoningEngine()
    
    # Fake JSON data simulating what Phase 2 (Qwen/InternVL) would output
    mock_vision_json = """
    {
      "diagram_type": "Electrical Circuit",
      "components": ["9V Battery", "100 Ohm Resistor", "Red LED"],
      "relationships": "Battery positive terminal connects to Resistor. Resistor connects to LED anode."
    }
    """
    
    print("\n--- USER ASKS FIRST QUESTION ---")
    response_1 = engine.generate_final_response(
        session_id="student_123", 
        user_query="What components are in this circuit?", 
        vision_json=mock_vision_json
    )
    print(f"\n🤖 AI OUTPUT: {response_1}\n")
    
    print("\n--- USER ASKS A TRICKY FOLLOW-UP ---")
    response_2 = engine.generate_final_response(
        session_id="student_123", 
        user_query="Wait, how does the power get to the LED?", 
        vision_json=mock_vision_json
    )
    print(f"\n🤖 AI OUTPUT: {response_2}\n")