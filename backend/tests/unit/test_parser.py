"""Unit tests for the ReAct output parser."""


from agentprobe.application.services.parser import parse_llm_output


class TestParseLLMOutput:
    """Tests for parse_llm_output covering standard and edge cases."""

    def test_parses_thought_action_action_input(self) -> None:
        """Standard ReAct output with all three fields."""
        text = (
            "Thought: I need to calculate this\n"
            "Action: calculator\n"
            "Action Input: 2 ** 10"
        )
        result = parse_llm_output(text)
        assert result.thought == "I need to calculate this"
        assert result.action == "calculator"
        assert result.action_input == "2 ** 10"
        assert result.final_answer is None

    def test_parses_final_answer(self) -> None:
        """Output with Final Answer should terminate parsing."""
        text = (
            "Thought: I have all the information\n"
            "Final Answer: The result is 42."
        )
        result = parse_llm_output(text)
        assert result.thought == "I have all the information"
        assert result.final_answer == "The result is 42."
        assert result.action is None

    def test_empty_string(self) -> None:
        """Empty string should return all None fields."""
        result = parse_llm_output("")
        assert result.thought is None
        assert result.action is None
        assert result.final_answer is None

    def test_malformed_output_no_action(self) -> None:
        """Output with thought but no action."""
        text = "Thought: I'm confused\nSomething else here"
        result = parse_llm_output(text)
        assert result.thought == "I'm confused\nSomething else here"
        assert result.action is None

    def test_multiline_thought(self) -> None:
        """Thought spanning multiple lines before Action."""
        text = (
            "Thought: First I need to think about this.\n"
            "Let me consider the options.\n"
            "Action: web_search\n"
            "Action Input: test query"
        )
        result = parse_llm_output(text)
        assert "First I need to think" in (result.thought or "")
        assert result.action == "web_search"
        assert result.action_input == "test query"

    def test_preserves_raw_text(self) -> None:
        """Raw text should always be preserved."""
        text = "Some random output"
        result = parse_llm_output(text)
        assert result.raw == text

    def test_final_answer_with_multiline_content(self) -> None:
        """Final answer can span multiple lines."""
        text = (
            "Thought: Done\n"
            "Final Answer: Line 1\nLine 2\nLine 3"
        )
        result = parse_llm_output(text)
        assert result.final_answer is not None
        assert "Line 1" in result.final_answer
        assert "Line 3" in result.final_answer

    def test_action_without_thought(self) -> None:
        """Action without preceding Thought still parses."""
        text = "Action: calculator\nAction Input: 1 + 1"
        result = parse_llm_output(text)
        assert result.thought is None
        assert result.action == "calculator"
        assert result.action_input == "1 + 1"
