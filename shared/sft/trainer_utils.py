from trl import SFTTrainer, IterativeSFTTrainer , SFTConfig
from transformers import (
    TrainingArguments,
    DataCollatorForSeq2Seq
)
from .config.training_config import (
    sft_argument,
    training_argument
)
from unsloth.chat_templates import train_on_responses_only
from datasets import Dataset
from typing_extensions import Dict, Any
from loguru import logger
from unsloth import is_bfloat16_supported

def find_all_minus_100_labels(trainer):
    """Find datapoints where all labels are -100"""
    dataset = trainer.train_dataset
    problematic_indices = []

    for i, example in enumerate(dataset):
        labels = example.get('labels', None)
        if labels is None:
            continue
        # Check if all labels are -100
        if all(label == -100 for label in labels):
            problematic_indices.append(i)

    return problematic_indices



def get_trainer(model: Any, 
                train_dataset: Dataset, 
                eval_dataset: Dataset, 
                tokenizer: Any,
                config: Dict[str, Any] = None
    ) -> SFTTrainer:

    merged_sft_config = {**sft_argument, **(config or {})}
    merged_sft_config = {k: merged_sft_config[k] for k in sft_argument.keys()}

    merged_training_config = {**training_argument, **(config or {})}
    merged_training_config = {k: merged_training_config[k] for k in training_argument.keys()}
   # for i, example in enumerate(train_dataset):
    #    if i<2:
     #       print("hereeeeeeeeeeeeeeeeeeeeee")
      #      print("exp--",example)


    #input_id = train_dataset[0]['input_ids']
    #print("len--",len(input_id))
    import json
    print("=== Merged Training Config ===")
    print(json.dumps(merged_training_config, indent=2, default=str))
    print("=== Merged SFT Config ===")
    print(json.dumps(merged_sft_config, indent=2, default=str))
    merged_sft_config['max_length'] = 16394
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=DataCollatorForSeq2Seq(
            tokenizer=tokenizer
        ),
         **merged_sft_config,
        args = SFTConfig(
            **merged_training_config
        )
    )
    # Print all training arguments
    print("=== Training Arguments ===")
    print(trainer.args)

# Or more readable format
    import json
    print(json.dumps(trainer.args.to_dict(), indent=2))

    after_input_id= trainer.train_dataset[0]['input_ids']
    print("aftr len --",len(after_input_id))
    # Run this after your trainer is created but before train_on_responses_only
    problematic_indices = find_all_minus_100_labels(trainer)
    print(f"Indices with all labels -100: {problematic_indices}")
    print(f"Total problematic samples: {len(problematic_indices)}")

# Inspect the problematic samples
    for idx in problematic_indices[:5]:  # Show first 5
        print(f"\n--- Sample {idx} ---")
        sample = trainer.train_dataset[idx]
        print("Text:", sample.get('text', 'No text field'))
        print("Labels:", sample.get('labels', 'No labels field'))
    trainer = train_on_responses_only(
        trainer,
        instruction_part = "<|im_start|>user\n",
        response_part = "<|im_start|>assistant\n",
    )
    # Run this after your trainer is created but before train_on_responses_only
    problematic_indices = find_all_minus_100_labels(trainer)
    print(f"Indices with all labels -100: {problematic_indices}")
    print(f"Total problematic samples: {len(problematic_indices)}")

# Inspect the problematic samples
    for idx in problematic_indices[:5]:  # Show first 5
        print(f"\n--- Sample {idx} ---")
        sample = trainer.train_dataset[idx]
        print("Text:", sample.get('text', 'No text field'))
        print("Labels:", sample.get('labels', 'No labels field'))
    return trainer
