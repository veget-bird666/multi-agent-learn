from app.tools.vision_tool import analyze_image
from app.tools.ppt_tool import generate_ppt, generate_ppt_tool, list_ppt_templates
from app.tools.resource_tools import generate_document, generate_exercises

STANDARD_TOOLS = [analyze_image, generate_ppt_tool, generate_document, generate_exercises]

__all__ = [
    "analyze_image", "generate_ppt", "generate_ppt_tool", "list_ppt_templates",
    "generate_document", "generate_exercises", "STANDARD_TOOLS",
]
