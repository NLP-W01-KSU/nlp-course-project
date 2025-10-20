from transformers import PegasusTokenizer, PegasusForConditionalGeneration

def base_pegasus_summary(content: str) -> str:
    # Load the Pegasus tokenizer and model
    model_name = "google/pegasus-xsum"
    tokenizer = PegasusTokenizer.from_pretrained(model_name)
    model = PegasusForConditionalGeneration.from_pretrained(model_name)

    # Tokenize the input content
    inputs = tokenizer(content, return_tensors="pt", truncation=True)

    # Generate the summary
    summary_ids = model.generate(**inputs)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    return summary

def test_base_pegasus_summary():
    test_content = (
        "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the English alphabet, making it a popular pangram used for testing fonts and keyboard layouts."
    )
    summary = base_pegasus_summary(test_content)
    print("Summary:", summary)
    
test_base_pegasus_summary()