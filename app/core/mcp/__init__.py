"""
Multi-Component Prompting (MCP) Framework for Bluelabel AIOS.

This module provides a framework for managing prompts as reusable components
with versioning, testing, and management capabilities.
"""

from .component import MCPComponent
from .registry import ComponentRegistry
from .versioning import ComponentVersionStore
from .editor import ComponentEditor
from .testing import ComponentTester, TestResult, TestResultStore

__all__ = [
    'MCPComponent',
    'ComponentRegistry',
    'ComponentVersionStore',
    'ComponentEditor',
    'ComponentTester',
    'TestResult',
    'TestResultStore'
]