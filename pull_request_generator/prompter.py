import os
import os
import json
from google import genai
from pydantic import BaseModel
from typing import Type, TypeVar


T = TypeVar('T')

class Prompter:
    def __init__(self, prompt_file:str, model: str = "gemini-2.5-flash"):
        self.prompt_file = os.path.abspath(prompt_file)
        self.model = model
        self.api_key = os.getenv("API_KEY", "")
        if not self.api_key:
            raise ValueError("API_KEY environment variable not set.")

    def get_prompt(self):
        if not os.path.exists(self.prompt_file):
            raise FileNotFoundError(f"Prompt file not found: {self.prompt_file}")
        with open(self.prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()
        return prompt

    def get_taxonomy(self):
        with open("workflow/taxonomy.json", 'r', encoding='utf-8') as taxonomy_file:
            taxonomy = json.load(taxonomy_file)
        return taxonomy

    def call_gemini_api(self, prompt: str, prompt_response_class: Type[T]) -> T:
        """
        Calls Gemini API to get a prompt object.
        Returns an instantiated Pydantic object of the provided class type.
        """
        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": prompt_response_class.model_json_schema(),
            },
        )
        prompt_obj: T = prompt_response_class.model_validate_json(response.text)
        return prompt_obj
    