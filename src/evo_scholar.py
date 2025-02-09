#!/usr/bin/env python3
"""
ArxResearch.py

A self-improving research agent that generates concise interdisciplinary research papers.
It fetches recent arXiv paper summaries, generates a new research paper blending ideas
from different STEM fields, and iteratively refines the paper based on evaluation feedback.
"""

import os
import re
import subprocess
import sys
import unittest
import arxiv

# Import OpenAI library (adjust as needed for your environment)
from openai import OpenAI  # Make sure you have the openai package installed


class SelfImprovingResearchAgent:
    def __init__(self, model="grok-2-latest", iterations=1, test_mode=False):
        """
        Initialize the research agent.

        Args:
            model (str): The model name to use for text generation.
            iterations (int): Number of refinement iterations.
            test_mode (bool): If True, bypass external API calls and use dummy responses.
        """
        self.model = model
        self.iterations = iterations
        self.test_mode = test_mode
        if not self.test_mode:
            self.client = OpenAI(
                api_key=os.getenv("XAI_API_KEY"),
                base_url="https://api.x.ai/v1",
            )
        else:
            self.client = None  # Dummy client for testing

    def extract_text(self, text):
        """
        Extracts text from a Markdown code block if present.
        If no code block is found, returns the stripped text.
        """
        code_block = re.search(r"```(?:python)?\n(.*?)\n```", text, re.DOTALL)
        if code_block:
            return code_block.group(1).strip()
        return text.strip()

    def generate_paper(self, prompt):
        """
        Generates a research paper (as text) based on the given prompt.
        In test mode, returns a dummy paper.
        """
        if self.test_mode:
            # Return a dummy research paper for testing purposes.
            return (
                "Title: Dummy Research Paper\n"
                "Abstract: This is a dummy abstract for testing purposes.\n"
                "Introduction: An introduction to the dummy paper.\n"
                "Proposed Method: A dummy method is proposed.\n"
                "Conclusion: The paper concludes with dummy insights."
            )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an AI research paper generator."},
                {"role": "user", "content": prompt},
            ],
        )
        paper = response.choices[0].message.content
        return self.extract_text(paper)

    def evaluate_paper(self, paper_text, max_words=500):
        """
        Evaluates the paper based on word count and required section presence.
        Returns feedback to guide refinement.

        Args:
            paper_text (str): The text of the paper.
            max_words (int): Maximum allowed word count.

        Returns:
            str: Feedback message.
        """
        word_count = len(paper_text.split())
        feedback = ""
        if word_count > max_words:
            feedback += f"Paper is too long by {word_count - max_words} words. "
        # Check for essential sections
        required_sections = [
            "Title:",
            "Abstract:",
            "Introduction:",
            "Proposed Method:",
            "Conclusion:",
        ]
        missing_sections = [sec for sec in required_sections if sec not in paper_text]
        if missing_sections:
            feedback += f"Missing sections: {', '.join(missing_sections)}. "
        if not feedback:
            feedback = f"Success! Paper length is {word_count} words."
        return feedback.strip()

    def refine_paper(self, paper_text, feedback):
        """
        Refines the research paper based on the provided feedback.

        Args:
            paper_text (str): The current version of the paper.
            feedback (str): Feedback from evaluation.

        Returns:
            str: The refined research paper.
        """
        prompt = (
            f"Refine the following research paper based on this feedback:\n{feedback}\n\n"
            f"Paper:\n{paper_text}\n\n"
            "Ensure the paper is concise (under 500 words), introduces a novel interdisciplinary concept "
            "by blending ideas from different STEM fields, and includes the sections: Title, Abstract, "
            "Introduction, Proposed Method, and Conclusion."
        )
        return self.generate_paper(prompt)

    def fetch_latest_papers(self, max_results=5, query="interdisciplinary research AI biology physics"):
        """
        Fetches the latest arXiv papers based on the given query.

        Args:
            max_results (int): Maximum number of papers to retrieve.
            query (str): The search query.

        Returns:
            list: A list of dictionaries with keys: title, abstract, link.
        """
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )
        # Using the arxiv.Client() to get search results
        client = arxiv.Client()
        papers = []
        for result in client.results(search):
            papers.append({
                "title": result.title,
                "abstract": result.summary.replace("\n", " "),
                "link": result.entry_id,
            })
        return papers

    def run(self):
        """
        Runs the self-improving research agent:
         - Fetches recent paper summaries.
         - Generates an initial research paper.
         - Iteratively refines the paper based on evaluation feedback.
         - Saves the final version to 'generated_paper.txt'.
        """
        latest_papers = self.fetch_latest_papers()
        paper_summaries = "\n".join(
            [
                f"Title: {paper['title']}\nAbstract: {paper['abstract']}"
                for paper in latest_papers
            ]
        )

        base_prompt = (
            "Generate a new interdisciplinary research paper inspired by the following arXiv paper summaries:\n"
            f"{paper_summaries}\n\n"
            "Your paper should be concise (under 500 words) and include the sections: Title, Abstract, "
            "Introduction, Proposed Method, and Conclusion. Propose a novel concept by blending ideas from different STEM fields."
        )

        paper_text = self.generate_paper(base_prompt)
        file_name = "generated_paper.txt"

        for i in range(self.iterations):
            # Save current version
            with open(file_name, "w") as f:
                f.write(paper_text)

            feedback = self.evaluate_paper(paper_text)
            print(f"Iteration {i+1} feedback: {feedback}")
            paper_text = self.refine_paper(paper_text, feedback)

        print("\nFinal Version of the Paper:")
        print(paper_text)
        with open(file_name, "w") as f:
            f.write(paper_text)


# --------------------- Testing --------------------- #
class TestSelfImprovingResearchAgent(unittest.TestCase):
    def setUp(self):
        # Use test_mode=True to avoid real API calls during tests.
        self.agent = SelfImprovingResearchAgent(test_mode=True)

    def test_extract_text_with_code_block(self):
        input_text = "Some text\n```python\nTitle: Test Paper\nAbstract: Test Abstract\n```"
        expected_output = "Title: Test Paper\nAbstract: Test Abstract"
        self.assertEqual(self.agent.extract_text(input_text), expected_output)

    def test_extract_text_without_code_block(self):
        input_text = "Title: Direct Text Paper\nAbstract: Direct Abstract"
        expected_output = "Title: Direct Text Paper\nAbstract: Direct Abstract"
        self.assertEqual(self.agent.extract_text(input_text), expected_output)

    def test_evaluate_paper_success(self):
        paper_text = (
            "Title: Test Research Paper\n"
            "Abstract: This is an abstract.\n"
            "Introduction: Intro here.\n"
            "Proposed Method: Method description.\n"
            "Conclusion: Final thoughts."
        )
        feedback = self.agent.evaluate_paper(paper_text, max_words=500)
        self.assertIn("Success!", feedback)

    def test_evaluate_paper_missing_sections(self):
        paper_text = "Title: Incomplete Paper\nAbstract: Missing sections."
        feedback = self.agent.evaluate_paper(paper_text, max_words=500)
        self.assertIn("Missing sections", feedback)

    def test_refine_paper_returns_non_empty(self):
        original_paper = (
            "Title: Original Paper\n"
            "Abstract: Original Abstract.\n"
            "Introduction: Some intro.\n"
            "Proposed Method: Some method.\n"
            "Conclusion: Some conclusion."
        )
        feedback = "Paper is too long by 100 words. Missing sections: Results."
        refined_paper = self.agent.refine_paper(original_paper, feedback)
        self.assertTrue(len(refined_paper) > 0)
        self.assertIn("Title:", refined_paper)
        self.assertIn("Abstract:", refined_paper)


if __name__ == "__main__":
    if "--test" in sys.argv:
        # Run unit tests if "--test" flag is provided
        unittest.main(argv=[sys.argv[0]])
    else:
        agent = SelfImprovingResearchAgent()
        agent.run()

