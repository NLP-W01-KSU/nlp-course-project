from pegasus import load_base_model, load_finetuned_model, test_decoding_strategies as test_pegasus
from phi_2 import load_phi2_model, test_decoding_strategies as test_phi2
from pegasus import generate_summary as pegasus_generate_summary
from phi_2 import generate_summary as phi2_generate_summary

content = """
Avatar is set in a largely Asian-inspired world in which some people can telekinetically manipulate one of the four elements—water, earth, fire or air—through practices known as "bending", inspired by Chinese martial arts.
The only individual who can bend all four elements, the "Avatar", is responsible for maintaining harmony among the world's four nations, and serves as the link between the physical and spirit worlds.
The series follows the journey of twelve-year-old Aang, the current Avatar and last survivor of his nation, the Air Nomads, along with his friends Katara, Sokka, and Toph, as they strive to end the Fire Nation's war against the other nations and defeat Fire Lord Ozai before he conquers the world.
The series also follows Zuko—the exiled prince of the Fire Nation, seeking to restore his lost honor by capturing Aang, accompanied by his uncle Iroh—and later, his sister Azula.
Avatar is presented and animated in a style that combines Japanese anime influences with those of American cartoons and relies on the imagery of primarily Chinese culture,[3][4] with various other influences from different East Asian, Southeast Asian, South Asian, North Asian, and indigenous American cultures.
"""


def process_with_pegasus_base(content: str, num_beams=1, do_sample=False, prompt_lookup_num_tokens=None):
    """
    Process content using base Pegasus model

    Args:
        content: Text content to summarize
        num_beams: Number of beams for beam search
        do_sample: Whether to use sampling
        prompt_lookup_num_tokens: Number of tokens for assisted decoding

    Returns:
        Generated summary
    """
    print("\n" + "=" * 60)
    print("PROCESSING WITH PEGASUS BASE MODEL")
    print("=" * 60)

    tokenizer, model = load_base_model()
    summary = pegasus_generate_summary(
        tokenizer,
        model,
        content,
        num_beams=num_beams,
        do_sample=do_sample,
        prompt_lookup_num_tokens=prompt_lookup_num_tokens
    )

    print(f"\nSummary: {summary}")
    return summary


def process_with_pegasus_finetuned(content: str, num_beams=1, do_sample=False, prompt_lookup_num_tokens=None):
    """
    Process content using fine-tuned Pegasus model

    Args:
        content: Text content to summarize
        num_beams: Number of beams for beam search
        do_sample: Whether to use sampling
        prompt_lookup_num_tokens: Number of tokens for assisted decoding

    Returns:
        Generated summary
    """
    print("\n" + "=" * 60)
    print("PROCESSING WITH PEGASUS FINE-TUNED MODEL")
    print("=" * 60)

    # Load base model first
    tokenizer, model = load_base_model()

    # Load or create fine-tuned model
    model_ft, tokenizer_ft = load_finetuned_model(model, tokenizer)

    summary = pegasus_generate_summary(
        tokenizer_ft,
        model_ft,
        content,
        num_beams=num_beams,
        do_sample=do_sample,
        prompt_lookup_num_tokens=prompt_lookup_num_tokens
    )

    print(f"\nSummary: {summary}")
    return summary


def process_with_phi2(content: str, max_length=500, num_beams=1, do_sample=False, temperature=1.0, top_p=1.0):
    """
    Process content using Phi-2 model

    Args:
        content: Text content to summarize
        max_length: Maximum length of generated text
        num_beams: Number of beams for beam search
        do_sample: Whether to use sampling
        temperature: Temperature for sampling
        top_p: Top-p value for nucleus sampling

    Returns:
        Generated summary
    """
    print("\n" + "=" * 60)
    print("PROCESSING WITH PHI-2 MODEL")
    print("=" * 60)

    tokenizer, model = load_phi2_model()
    summary = phi2_generate_summary(
        tokenizer,
        model,
        content,
        max_length=max_length,
        num_beams=num_beams,
        do_sample=do_sample,
        temperature=temperature,
        top_p=top_p
    )

    print(f"\nSummary: {summary}")
    return summary


def test_all_models_with_content(content: str):
    """
    Test all models with the provided content using different decoding strategies

    Args:
        content: Text content to summarize
    """
    print("\n" + "=" * 60)
    print("TESTING ALL MODELS WITH PROVIDED CONTENT")
    print("=" * 60)

    # Test Pegasus Base Model
    print("\n\n### PEGASUS BASE MODEL ###")
    tokenizer, model = load_base_model()
    test_pegasus(tokenizer, model)

    # Test Pegasus Fine-tuned Model
    print("\n\n### PEGASUS FINE-TUNED MODEL ###")
    tokenizer_base, model_base = load_base_model()
    model_ft, tokenizer_ft = load_finetuned_model(model_base, tokenizer_base)
    test_pegasus(tokenizer_ft, model_ft)

    # Test Phi-2 Model
    print("\n\n### PHI-2 MODEL ###")
    tokenizer_phi2, model_phi2 = load_phi2_model()
    test_phi2(tokenizer_phi2, model_phi2)


def compare_models(content: str):
    """
    Compare all models with greedy decoding on the same content

    Args:
        content: Text content to summarize
    """
    print("\n" + "=" * 60)
    print("MODEL COMPARISON - GREEDY DECODING")
    print("=" * 60)

    # Pegasus Base
    summary_pegasus_base = process_with_pegasus_base(content, num_beams=1, do_sample=False)

    # Pegasus Fine-tuned
    summary_pegasus_ft = process_with_pegasus_finetuned(content, num_beams=1, do_sample=False)

    # Phi-2
    summary_phi2 = process_with_phi2(content, num_beams=1, do_sample=False)

    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"\nPegasus Base: {summary_pegasus_base}")
    print(f"\nPegasus Fine-tuned: {summary_pegasus_ft}")
    print(f"\nPhi-2: {summary_phi2}")


def main():
    """
    Main function demonstrating different ways to use the models
    """
    # Example 1: Process with individual models
    print("\n" + "#" * 60)
    print("# EXAMPLE 1: Individual Model Processing")
    print("#" * 60)

    process_with_pegasus_base(content, num_beams=5, do_sample=False)
    process_with_phi2(content, num_beams=1, do_sample=True, temperature=0.7, top_p=0.9)

    # Example 2: Test all decoding strategies for all models
    print("\n\n" + "#" * 60)
    print("# EXAMPLE 2: Test All Decoding Strategies")
    print("#" * 60)

    test_all_models_with_content(content)

    # Example 3: Compare models side-by-side
    print("\n\n" + "#" * 60)
    print("# EXAMPLE 3: Side-by-Side Model Comparison")
    print("#" * 60)

    compare_models(content)


if __name__ == "__main__":
    main()