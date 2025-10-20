import os
from transformers import PegasusTokenizer, PegasusForConditionalGeneration
from finetune_model import finetune_pegasus

content = """
Avatar is set in a largely Asian-inspired world in which some people can telekinetically manipulate one of the four elements—water, earth, fire or air—through practices known as "bending", inspired by Chinese martial arts.
The only individual who can bend all four elements, the "Avatar", is responsible for maintaining harmony among the world's four nations, and serves as the link between the physical and spirit worlds.
The series follows the journey of twelve-year-old Aang, the current Avatar and last survivor of his nation, the Air Nomads, along with his friends Katara, Sokka, and Toph, as they strive to end the Fire Nation's war against the other nations and defeat Fire Lord Ozai before he conquers the world.
The series also follows Zuko—the exiled prince of the Fire Nation, seeking to restore his lost honor by capturing Aang, accompanied by his uncle Iroh—and later, his sister Azula.
Avatar is presented and animated in a style that combines Japanese anime influences with those of American cartoons and relies on the imagery of primarily Chinese culture,[3][4] with various other influences from different East Asian, Southeast Asian, South Asian, North Asian, and indigenous American cultures.
"""


def load_base_model():
    model_name = "google/pegasus-xsum"
    tokenizer = PegasusTokenizer.from_pretrained(model_name)
    model = PegasusForConditionalGeneration.from_pretrained(model_name, dtype="auto", device_map="auto")
    return tokenizer, model


def load_finetuned_model(model, tokenizer):
    if os.path.exists("./finetuned_model"):
        print(10 * "=" + "\nLoading existing finetuned model\n" + (10 * "="))
        model = PegasusForConditionalGeneration.from_pretrained("./finetuned_model", dtype="auto", device_map="auto")
        tokenizer = PegasusTokenizer.from_pretrained("./finetuned_model")
        return model, tokenizer
    else:
        return finetune_pegasus(tokenizer, model, output_dir="./finetuned_model")


def generate_summary(tokenizer, model, content: str, num_beams=1, do_sample=False,
                     prompt_lookup_num_tokens=None) -> str:
    inputs = tokenizer(content, return_tensors="pt", truncation=True)

    # Move inputs to the same device as the model
    device = model.device
    inputs = {key: value.to(device) for key, value in inputs.items()}

    generate_kwargs = {"num_beams": num_beams, "do_sample": do_sample}
    if prompt_lookup_num_tokens is not None:
        generate_kwargs["prompt_lookup_num_tokens"] = prompt_lookup_num_tokens

    summary_ids = model.generate(**inputs, **generate_kwargs)
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)


def test_decoding_strategies(tokenizer, model):
    print("\n" + "=" * 50)
    print("PEGASUS - DECODING TESTS")
    print("=" * 50 + "\n")

    summary = generate_summary(tokenizer, model, content, num_beams=1, do_sample=False)
    print("Greedy Decoding Summary:", summary)

    summary = generate_summary(tokenizer, model, content, num_beams=1, do_sample=True)
    print("\nMultinomial Sampling Summary:", summary)

    summary = generate_summary(tokenizer, model, content, num_beams=5, do_sample=False)
    print("\nBeam-Search Decoding Summary:", summary)

    summary = generate_summary(tokenizer, model, content, num_beams=5, do_sample=True)
    print("\nBeam-Search Multinomial Sampling Summary:", summary)

    summary = generate_summary(tokenizer, model, content, prompt_lookup_num_tokens=10)
    print("\nAssisted Decoding Summary:", summary)


def main():
    # Run all tests (Base Model)
    print("\n" + "=" * 50)
    print("TESTING BASE MODEL")
    print("=" * 50)
    tknizer, mdl = load_base_model()
    test_decoding_strategies(tknizer, mdl)

    # Run all tests (Fine-tuned Model)
    print("\n" + "=" * 50)
    print("TESTING FINE-TUNED MODEL")
    print("=" * 50)
    mdl_ft, tknizer_ft = load_finetuned_model(mdl, tknizer)
    test_decoding_strategies(tknizer_ft, mdl_ft)


if __name__ == "__main__":
    main()