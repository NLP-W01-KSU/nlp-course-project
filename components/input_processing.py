from transformers import PegasusTokenizer, PegasusForConditionalGeneration

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

def generate_summary(tokenizer, model, content: str, num_beams=1, do_sample=False, prompt_lookup_num_tokens=None) -> str:
    # Tokenize the input content
    inputs = tokenizer(content, return_tensors="pt", truncation=True)

    # Generate the summary
    generate_kwargs = {"num_beams": num_beams, "do_sample": do_sample}
    if prompt_lookup_num_tokens is not None:
        generate_kwargs["prompt_lookup_num_tokens"] = prompt_lookup_num_tokens

    summary_ids = model.generate(**inputs, **generate_kwargs)
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

def test_decoding_strategies(tokenizer, model):
    summary = generate_summary(tokenizer, model, content, num_beams=1, do_sample=False)
    print("Greedy Decoding Summary:", summary)
    summary = generate_summary(tokenizer, model, content, num_beams=1, do_sample=True)
    print("Multinomial Sampling Summary:", summary)
    summary = generate_summary(tokenizer, model, content, num_beams=5, do_sample=False)
    print("Beam-Search Decoding Summary:", summary)
    summary = generate_summary(tokenizer, model, content, num_beams=5, do_sample=True)
    print("Beam-Search Multinomial Sampling Summary:", summary)
    summary = generate_summary(tokenizer, model, content, prompt_lookup_num_tokens=10)
    print("Assisted Decoding Summary:", summary)



# Run all tests (Base Model)
tknizer, mdl = load_base_model()
test_decoding_strategies(tknizer, mdl)
