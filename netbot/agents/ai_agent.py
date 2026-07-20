import os
from openai import OpenAI
from google import genai

client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

genai_client = genai.Client(api_key=os.getenv("GEMINI_KEY"))


class AIAgent:

    def chat(self, ctx):

        # Fallback if context is empty
        if not ctx:
            ctx = [{"role": "user", "content": "Hello"}]

        try:

            # Reasoning system prompt
            system = {
                "role": "system",
                "content": "You are NetBot, a cybersecurity assistant. Reason step-by-step internally. Give concise final answers."
            }

            messages = [system] + ctx

            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2
            )

            return res.choices[0].message.content.strip(), "openai"

        except Exception as e:

            # Gemini fallback
            last_msg = ctx[-1]["content"]

            r = genai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=last_msg
            )

            return r.text.strip(), "gemini"