fast_model_config = {
    "model_name": "Qwen/Qwen2.5-Coder-3B-Instruct",
    "max_seq_length": 16384,
    "dtype": None,
    "load_in_8bit": True,
    "load_in_4bit" : False
}

peft_model_config = {
    "r": 512,
    "target_modules": ["q_proj", "k_proj", "v_proj","o_proj"], #"gate_proj", "o_proj","up_proj", "down_proj"
    "lora_alpha": 512,
    "lora_dropout": 0,
    "bias": "none",
    "use_gradient_checkpointing": "unsloth",
    "random_state": 3407,
    "use_rslora": True,
    "loftq_config": None
}
