"""
Prompt Service for Clinical Intelligence Platform.
Loads prompts from /prompts/ directory with parameter substitution.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache

from app.config import settings

logger = logging.getLogger(__name__)


class PromptService:
    """
    Service for loading and formatting LLM prompts.

    Features:
    - Load prompts from .txt files in /prompts/ directory
    - Parameter substitution using {variable_name} placeholders
    - Prompt caching for performance
    - Validation of required parameters
    """

    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize prompt service.

        Args:
            prompts_dir: Path to prompts directory (default: project_root/prompts)
        """
        if prompts_dir:
            self.prompts_dir = Path(prompts_dir)
        else:
            self.prompts_dir = settings.project_root / "prompts"

        logger.info(f"Prompt service initialized with directory: {self.prompts_dir}")

    def _get_prompt_path(self, prompt_name: str) -> Path:
        """
        Get full path to prompt file.

        Args:
            prompt_name: Prompt name in format "uc1/readiness_synthesis" or just "readiness_synthesis.txt"

        Returns:
            Path to the prompt file
        """
        # Handle with or without .txt extension
        if not prompt_name.endswith(".txt"):
            prompt_name = f"{prompt_name}.txt"

        return self.prompts_dir / prompt_name

    @lru_cache(maxsize=100)
    def _load_template(self, prompt_name: str) -> str:
        """
        Load prompt template from file (cached).

        Args:
            prompt_name: Name of the prompt file

        Returns:
            Raw template content
        """
        file_path = self._get_prompt_path(prompt_name)

        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")

        template = file_path.read_text(encoding="utf-8")
        logger.debug(f"Loaded prompt template: {prompt_name} ({len(template)} chars)")

        return template

    def load(
        self,
        prompt_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        strict: bool = False,
    ) -> str:
        """
        Load and format a prompt template.

        Args:
            prompt_name: Name of the prompt (e.g., "uc1/readiness_synthesis")
            parameters: Dictionary of values to substitute into placeholders
            strict: If True, raise error for missing parameters

        Returns:
            Formatted prompt string

        Example:
            prompt = prompt_service.load(
                "uc2/contextualization",
                {
                    "signal_type": "Periprosthetic Fracture",
                    "signal_rate": 13.5,
                    "threshold": 8.0,
                }
            )
        """
        template = self._load_template(prompt_name)

        if parameters:
            try:
                # Use format_map for partial substitution support
                if strict:
                    return template.format(**parameters)
                else:
                    return template.format_map(SafeDict(parameters))
            except KeyError as e:
                if strict:
                    raise ValueError(f"Missing required parameter: {e}")
                logger.warning(f"Missing parameter in prompt {prompt_name}: {e}")
                return template
        else:
            return template

    def list_prompts(self, use_case: Optional[str] = None) -> Dict[str, list]:
        """
        List available prompts.

        Args:
            use_case: Optional filter by use case (uc1, uc2, etc.)

        Returns:
            Dictionary mapping use cases to prompt names
        """
        prompts = {}

        for subdir in self.prompts_dir.iterdir():
            if subdir.is_dir() and (use_case is None or subdir.name == use_case):
                prompts[subdir.name] = [
                    f.stem for f in subdir.glob("*.txt")
                ]

        return prompts

    def validate_prompt(self, prompt_name: str) -> Dict[str, Any]:
        """
        Validate a prompt file and extract its placeholders.

        Args:
            prompt_name: Name of the prompt

        Returns:
            Dictionary with validation results
        """
        import re

        template = self._load_template(prompt_name)

        # Find all placeholders
        placeholders = re.findall(r'\{(\w+)\}', template)
        unique_placeholders = list(set(placeholders))

        return {
            "prompt_name": prompt_name,
            "char_count": len(template),
            "line_count": template.count('\n') + 1,
            "placeholders": unique_placeholders,
            "placeholder_count": len(unique_placeholders),
        }

    def clear_cache(self):
        """Clear the template cache."""
        self._load_template.cache_clear()
        logger.info("Prompt template cache cleared")


class SafeDict(dict):
    """Dictionary that returns {key} for missing keys instead of raising KeyError."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


# Singleton instance
_prompt_service: Optional[PromptService] = None


def get_prompt_service() -> PromptService:
    """Get singleton prompt service instance."""
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptService()
    return _prompt_service
