import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

content = """
Avatar is set in a largely Asian-inspired world in which some people can telekinetically manipulate one of the four elements—water, earth, fire or air—through practices known as "bending", inspired by Chinese martial arts.
The only individual who can bend all four elements, the "Avatar", is responsible for maintaining harmony among the world's four nations, and serves as the link between the physical and spirit worlds.
The series follows the journey of twelve-year-old Aang, the current Avatar and last survivor of his nation, the Air Nomads, along with his friends Katara, Sokka, and Toph, as they strive to end the Fire Nation's war against the other nations and defeat Fire Lord Ozai before he conquers the world.
The series also follows Zuko—the exiled prince of the Fire Nation, seeking to restore his lost honor by capturing Aang, accompanied by his uncle Iroh—and later, his sister Azula.
Avatar is presented and animated in a style that combines Japanese anime influences with those of American cartoons and relies on the imagery of primarily Chinese culture,[3][4] with various other influences from different East Asian, Southeast Asian, South Asian, North Asian, and indigenous American cultures.
"""


def load_phi2_model():
    torch.set_default_device("cuda")
    model = AutoModelForCausalLM.from_pretrained(
        "microsoft/phi-2",
        torch_dtype="auto",
        trust_remote_code=True
    )
    tokenizer = AutoTokenizer.from_pretrained(
        "microsoft/phi-2",
        trust_remote_code=True
    )
    return tokenizer, model


def generate_summary(tokenizer, model, content: str, max_length=500, num_beams=1, do_sample=False, temperature=1.0,
                     top_p=1.0) -> str:
    prompt = f"Summarize the following content:\n\n{content}\n\nSummary:"

    inputs = tokenizer(prompt, return_tensors="pt", return_attention_mask=False)

    # Move inputs to the same device as the model
    device = model.device
    inputs = {key: value.to(device) for key, value in inputs.items()}

    generate_kwargs = {
        "max_length": max_length,
        "num_beams": num_beams,
        "do_sample": do_sample,
    }

    if do_sample:
        generate_kwargs["temperature"] = temperature
        generate_kwargs["top_p"] = top_p

    outputs = model.generate(**inputs, **generate_kwargs)
    text = tokenizer.batch_decode(outputs)[0]

    # Extract only the summary part (after the prompt)
    if "Summary:" in text:
        summary = text.split("Summary:")[-1].strip()
    else:
        summary = text

    return summary


def test_decoding_strategies(tokenizer, model):
    print("\n" + "=" * 50)
    print("PHI-2 MODEL - DECODING STRATEGIES")
    print("=" * 50 + "\n")

    summary = generate_summary(tokenizer, model, content, num_beams=1, do_sample=False)
    print("Greedy Decoding Summary:", summary)

    summary = generate_summary(tokenizer, model, content, num_beams=1, do_sample=True, temperature=0.7, top_p=0.9)
    print("\nMultinomial Sampling Summary:", summary)

    summary = generate_summary(tokenizer, model, content, num_beams=5, do_sample=False)
    print("\nBeam-Search Decoding Summary:", summary)

    summary = generate_summary(tokenizer, model, content, num_beams=5, do_sample=True, temperature=0.7, top_p=0.9)
    print("\nBeam-Search Multinomial Sampling Summary:", summary)


def main():
    print("\n" + "=" * 50)
    print("TESTING PHI-2 MODEL")
    print("=" * 50)

    tokenizer, model = load_phi2_model()
    test_decoding_strategies(tokenizer, model)


if __name__ == "__main__":
    main()