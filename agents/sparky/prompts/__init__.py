from agents.sparky.base_utils import read_prompt

CONVERSION_SYS_PROMPT = read_prompt("conversion_system_prompt.txt")
CONVERSION_USER_PROMPT = read_prompt("conversion_user_prompt.txt")

IMPROVEMENT_SYS_PROMPT = read_prompt("improvement_system_prompt.txt")
IMPROVEMENT_USER_PROMPT = read_prompt("improvement_user_prompt.txt")

EVALUATION_SYS_PROMPT = read_prompt("evaluation_system_prompt.txt")
EVALUATION_USER_PROMPT = read_prompt("evaluation_user_prompt.txt")

__all__ = [
    CONVERSION_SYS_PROMPT,
    CONVERSION_USER_PROMPT,
    IMPROVEMENT_SYS_PROMPT,
    IMPROVEMENT_USER_PROMPT,
    EVALUATION_SYS_PROMPT,
    EVALUATION_USER_PROMPT,
]
