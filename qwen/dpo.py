from .dataset_util import get_data
from trl import DPOConfig, DPOTrainer
from .trainer_utils import get_trainer
from unsloth import is_bfloat16_supported
from .model_util import (
    load_model,
    get_param_details
)
from datasets import Dataset
import pandas as pd 


def load_dpo_data(file_path):
    df = pd.read_csv(file_path)
    
    chosen = df.apply(lambda row: [
        {
            'role': 'user', 
            'content': f"""schema:
    {row["schema"]}

    Always use ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`) for timestamps.
    For queries involving confidence (e.g., "score greater than 70 percent"), use `score` with operators like `$gt`, `$lt` (e.g., `"$gt": 0.7`).
        Today is 21 July 2025 use only when the query explicitly mentions to use the current date and time like using words today, last week. Never include or infer the date unless strictly mentioned in the query.
    natural_language_query: {row["natural_language_query"]}
    parsed_mongo_query:"""
        },
        {
            'role': 'assistant', 
            'content': row['corret_mongo_query']
        }
    ], axis=1).tolist()


    rejected = df.apply(lambda row: [
        {
            'role': 'user', 
            'content': f"""schema:
    {row["schema"]}

    Always use ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`) for timestamps.
    For queries involving confidence (e.g., "score greater than 70 percent"), use `score` with operators like `$gt`, `$lt` (e.g., `"$gt": 0.7`).
        Today is 21 July 2025 use only when the query explicitly mentions to use the current date and time like using words today, last week. Never include or infer the date unless strictly mentioned in the query.
    natural_language_query: {row["natural_language_query"]}
    parsed_mongo_query:"""},
        {
            'role': 'assistant', 
            'content': row['incorrect_mongo_query']
        }], axis=1).tolist()
    

    return Dataset.from_dict({"chosen": chosen, "rejected": rejected})


def main():

    train_data_path = "/home/raid/Diwanshu/Metafusion_NLP/heavy_dpo_v2.csv"
    eval_data_path = "/home/raid/Diwanshu/Metafusion_NLP/eval_df.csv"

    config = {
        "model_name": "Qwen/Qwen2.5-Coder-3B-Instruct",
       # "num_train_epochs": 1,
        "per_device_train_batch_size": 8,
        "learning_rate": 7.54132e-06,
        "weight_decay": 0.0502397,
        "lr_scheduler_type": "cosine_with_restarts",
        "lora_alpha": 32,
        "warmup_ratio": 0.197403,
        "lora_dropout": 0.0742568,
        "output_dir": "outputs",
        "max_steps": 10,
    }

    model, tokenizer = load_model(config=config)

    train_dataset = load_dpo_data(train_data_path)
    eval_dataset = load_dpo_data(eval_data_path)

    training_args = DPOConfig(
        output_dir="Qwen2-0.5B-DPO_v0.01", 
        logging_steps=1,
        eval_strategy="steps",
        eval_steps=10,
        per_device_train_batch_size=4,
        gradient_accumulation_steps= 1,
        warmup_steps= 5,
        num_train_epochs= 1,
       # max_steps= 10,
        learning_rate= 3e-6,
        beta=0.1,
        fp16= not is_bfloat16_supported(),
        bf16= is_bfloat16_supported(),
        optim= "adamw_8bit",
        weight_decay= 0.01,
        lr_scheduler_type= "linear",
        seed= 3407,
        loss_type='robust'
    )

    trainer = DPOTrainer(
        model=model, 
        args=training_args, 
        processing_class=tokenizer, 
        train_dataset=train_dataset,
        eval_dataset=eval_dataset
    )
    trainer.train()
    model.save_pretrained("heavy_dpo_v1")
    tokenizer.save_pretrained("heavy_dpo_v1")
    print("Training completed...")

    # model.save_pretrained_gguf(
    #     "qwen0.5_512_fine_model_tuned_ins", 
    #     tokenizer, 
    #     quantization_method = ["q4_k_m", "q8_0"]
    # ) 
    
    # tokenizer.save_pretrained_gguf("qwen0.5_512_fine_model_tuned")
    
    model.push_to_hub_gguf(
        "Diwanshuydv/qwen2.5-3B-coder-Instruct-_NL2MONGODB_DPO", # Change hf to your username!
        tokenizer,
        quantization_method = ["q4_k_m", "q8_0"],
        token = "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", # Get a token at https://huggingface.co/settings/tokens
    )

if __name__=="__main__":
    main()

