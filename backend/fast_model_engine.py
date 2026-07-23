import time
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
from PIL import Image

MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"

print("🚀 Loading VLM Engine on Windows with 4-bit Quantization...")
start_load = time.time()

# 1. Check if GPU is available
device = "cuda" if torch.cuda.is_available() else "cpu"

# 2. Configure 4-bit quantization (if using GPU)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
) if device == "cuda" else None

# 3. Use the CORRECT Multimodal Model Class (Fixes the ValueError!)
model = Qwen2VLForConditionalGeneration.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto" if device == "cuda" else None,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    trust_remote_code=True
)

# 4. Load the Multimodal Processor (Handles both image and text tokenization)
processor = AutoProcessor.from_pretrained(MODEL_NAME, trust_remote_code=True)

print(f"✅ Model loaded in {time.time() - start_load:.2f}s on {device.upper()}")


def generate_stem_response(image_path, user_query):
    start_time = time.time()
    image = Image.open(image_path)

    # Prepare chat message format expected by Qwen2-VL
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": f"Question: {user_query}\nAnswer concisely and step-by-step for a visually impaired student:"}
            ]
        }
    ]

    # Process prompt & image into tensors
    text_prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(
        text=[text_prompt],
        images=[image],
        padding=True,
        return_tensors="pt"
    ).to(device)

    # Generate response
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=False
        )

    # Trim input tokens from output to get only the answer
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    response_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]

    latency = time.time() - start_time
    print(f"✨ Response Generated in {latency:.2f}s!")
    print(f"🤖 Output: {response_text.strip()}")
    
    return response_text, latency


# --- Local Test Execution ---
# Replace with a test image and query
generate_stem_response("processed_images/page_1_300dpi.png", "What is shown in this diagram?")