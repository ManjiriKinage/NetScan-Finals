import os
from openai import OpenAI
import google.generativeai as genai

client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

genai.configure(api_key=os.getenv("GEMINI_KEY"))


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
            model = genai.GenerativeModel("gemini-2.5-flash")

            last_msg = ctx[-1]["content"]

            r = model.generate_content(last_msg)

            return r.text.strip(), "gemini"