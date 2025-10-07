import pandas as pd
from datasets import Dataset
from typing import List, Dict, Any
from loguru import logger
from data_v3.data_utils.utils import (
    modify_dataframe as modify_dataframe_v3
)
from .config.prompt_config import (
    MODEL_PROMPT, 
    SYSTEM_PROMPT
)
from .config.prompt_config_v3 import (
    MODEL_PROMPT_V3,
    SYSTEM_PROMPT_V3
)
from unsloth.chat_templates import (
    get_chat_template,
    standardize_sharegpt
)


def load_data_from_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df["prompt"] = df.apply(
        lambda x: MODEL_PROMPT_V3.format(
            schema=x["schema"],
            natural_language_query=x["natural_language_query"]
        ), axis=1
    )
    df = df.sample(frac=1).reset_index(drop=True)
    return df

def load_data_from_csv_v3(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    modified_data = modify_dataframe_v3(df)
    df_modified = pd.DataFrame(modified_data)
    # only take key - line_based_query, line_based_schema, natural_language_query, additional_info
    df_modified = df_modified[["line_based_query", "line_based_schema", "natural_language_query", "additional_info"]]
    df_modified.rename(columns={
        "line_based_query": "mongo_query",
        "line_based_schema": "schema"
    }, inplace=True)
    df_modified["prompt"] = df_modified.apply(
        lambda x: MODEL_PROMPT_V3.format(
            schema=x["schema"],
            natural_language_query=x["natural_language_query"]
        ), axis=1
    )
    df_modified = df_modified.sample(frac=1).reset_index(drop=True)
    return df_modified

def get_data_in_req_format(df: pd.DataFrame) -> Dataset:
    conversation = df.apply(lambda row: [
        {'from': 'human', 'value': row['prompt']},
        {'from': 'gpt', 'value': row['mongo_query']}
    ], axis=1).tolist()
    return Dataset.from_dict({"conversations": conversation})

def convert_to_chat_template(dataset: Dataset, tokenizer: Any, system_prompt: str) -> Dataset:
    dataset = standardize_sharegpt(dataset)
    tokenizer = get_chat_template(
        tokenizer,
        chat_template = "qwen-2.5",
        system_message = system_prompt
    )
    
    def formatting_prompts_func(examples):
        convos = examples["conversations"]
        texts = []
        
        for i, convo in enumerate(convos):
            # Debug: Print original conversation
            if i < 0:  # Print first 3 for debugging
                print(f"Original conversation {i}:")
                print(convo)
                
            text = tokenizer.apply_chat_template(convo, tokenize = False, add_generation_prompt = False)
            
            # Debug: Print formatted text
            if i < 0:
                print(f"Formatted text {i}:")
                print(text)
                print("-" * 50)
                
            texts.append(text)
            
        return {"text" : texts}
    
    dataset = dataset.map(formatting_prompts_func, batched = True,)
    return dataset
def check_empty_assistant_responses(dataset):
    """Check for empty assistant responses in the dataset"""
    empty_assistant_indices = []

    for i, sample in enumerate(dataset):
        text = sample['text']
        # Split on assistant label
        parts = text.split('<|im_start|>assistant')

        # Check each assistant response (skip first part which is before any assistant)
        for part in parts[1:]:
            # Find the next label or end of string
            next_label_pos = part.find('<|im_start|>')
            if next_label_pos == -1:
                # No next label, check until end of string
                response = part.strip()
            else:
                # Next label found, check content until that point
                response = part[:next_label_pos].strip()

            # If response is empty, record this sample
            if response == '':
                empty_assistant_indices.append(i)
                break  # Found empty response in this sample

    return empty_assistant_indices

def analyze_assistant_responses(dataset):
    """Analyze all assistant responses in detail"""
    import re
    
    analysis = {
        'empty_responses': [],
        'whitespace_only': [],
        'valid_responses': [],
        'total_assistant_sections': 0
    }
    
    for i, sample in enumerate(dataset):
        text = sample['text']
        
        # Find all assistant sections
        pattern = r'<\|im_start\|>assistant\s*(.*?)\s*<\|im_end\|>'
        matches = re.findall(pattern, text, re.DOTALL)
        
        analysis['total_assistant_sections'] += len(matches)
        
        for j, match in enumerate(matches):
            if match == '':
                analysis['empty_responses'].append((i, j))
            elif match.strip() == '':
                analysis['whitespace_only'].append((i, j, repr(match)))
            else:
                analysis['valid_responses'].append((i, j, len(match.strip())))
    
    return analysis


def get_data(file_path: str, tokenizer: Any, approach_v3: bool) -> Dataset:
    if approach_v3:
        df = load_data_from_csv(file_path)
        system_prompt = SYSTEM_PROMPT_V3
    else:
        df = load_data_from_csv(file_path)
        system_prompt = SYSTEM_PROMPT_V3
    print(df.head())
    dataset = get_data_in_req_format(df)
    dataset = convert_to_chat_template(dataset, tokenizer, system_prompt)
    # Check your dataset
    empty_indices = check_empty_assistant_responses(dataset)
    print(f"----Found {len(empty_indices)} samples with empty assistant responses")
    print(f"Indices with empty responses: {empty_indices}")

# Inspect the problematic samples
    for idx in empty_indices[:5]:  # Show first 5 problematic samples
        print(f"\n--- Sample {idx} ---")
        print(dataset[idx]['text'])

    analysis = analyze_assistant_responses(dataset)
    print(f"Total assistant sections: {analysis['total_assistant_sections']}")
    print(f"Empty responses: {len(analysis['empty_responses'])}")
    print(f"Whitespace-only responses: {len(analysis['whitespace_only'])}")
    print(f"Valid responses: {len(analysis['valid_responses'])}")
    print(len(dataset[0]))
    return dataset
