# tranformers Trainer
from transformers import Trainer, TrainingArguments, DataCollatorForSeq2Seq
from datasets import Dataset
import json
from pathlib import Path

def load_data(train_split=0.8):
    # Load the JSON file
    dataset_path = Path("../dataset/edu_summarization_dataset.json")

    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract samples and convert to input/target format
    samples = data['samples']
    formatted_data = []

    for sample in samples:
        formatted_data.append({
            'input': sample['source_text'],
            'target': sample['summary'],
            'subject': sample['subject'],
            'grade_level': sample['grade_level']
        })

    # Split into train and validation sets
    split_idx = int(len(formatted_data) * train_split)
    train_data = formatted_data[:split_idx]
    val_data = formatted_data[split_idx:]

    print(f"Loaded {len(formatted_data)} total samples")
    print(f"Training samples: {len(train_data)}")
    print(f"Validation samples: {len(val_data)}")

    return train_data, val_data

def finetune_pegasus(tokenizer, model, output_dir: str, epochs=3, batch_size=8, learning_rate=5e-5):
    """
    Fine-tune Pegasus hyperparameters

    Args:
        tokenizer: Pretrained tokenizer.
        model: Pretrained model.
        output_dir: Directory to save the fine-tuned model.
        epochs: Number of training epochs.
        batch_size: Batch size for training.
        learning_rate: Learning rate for the optimizer.

    Returns:
        Fine-tuned model.
    """
    # Load data
    train_data, val_data = load_data()
    
    # Tokenize datasets
    def preprocess_function(examples):
        inputs = tokenizer(examples['input'], truncation=True, padding="max_length", max_length=512)
        targets = tokenizer(examples['target'], truncation=True, padding="max_length", max_length=128)
        inputs['labels'] = targets['input_ids']
        return inputs

    train_dataset = Dataset.from_list(train_data).map(preprocess_function, batched=True)
    val_dataset = Dataset.from_list(val_data).map(preprocess_function, batched=True)

    # Data collator for padding
    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    # Define training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=epochs,
        weight_decay=0.01,
        save_total_limit=2,
        #save_steps=500,
        logging_dir=f"{output_dir}/logs",
        logging_steps=100,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=True 
    )

    # Define the Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator
    )

    # Train the model
    trainer.train()

    # Save the fine-tuned model
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    return model, tokenizer

# LoRA fine-tuning script
