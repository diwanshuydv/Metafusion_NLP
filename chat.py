from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
# Define the base model and adapter paths
base_model_name = "unsloth/Qwen2.5-Coder-3B-Instruct"  # Replace with the actual base model name
adapter_path = "./sft_model"

# Load the base model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(base_model_name)
base_model = AutoModelForCausalLM.from_pretrained(base_model_name)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# Load the adapter
model = PeftModel.from_pretrained(base_model, adapter_path).to(device)

# Set the model to evaluation mode
model.eval()

# Chat function
def chat():
    print("Model is ready!")

    user_input = input("You: ")
    inputs = tokenizer(user_input, return_tensors="pt").to(device)
    outputs = model.generate(**inputs, max_length=500, temperature=0.1)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Bot: {response}")

# Start chatting
chat()
