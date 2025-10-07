fast_model_config = {
    "model_name": "Diwanshuydv/qwen2.5-3B-coder-Instruct-Added-Tokens",
    "max_seq_length": 16384,
    "dtype": None,
    "load_in_8bit": False,
    "load_in_4bit" : True
}

peft_model_config = {
    "r": 512,
    "target_modules": ["q_proj", "k_proj", "v_proj"], #"gate_proj", "o_proj","up_proj", "down_proj"
    "lora_alpha": 512,
    "lora_dropout": 0,
    "bias": "none",
    "use_gradient_checkpointing": "unsloth",
    "random_state": 3407,
    "use_rslora": True,
    "loftq_config": None
}
