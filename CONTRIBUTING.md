# Contributing Guidelines

Thank you for contributing to the Bluelabel AIOS project. This document outlines the workflow and standards for contributing to this project.

## Development Workflow

### 1. Branching Strategy

- `main` branch is the primary development branch
- Create feature branches from `main` for new features
- Use the format `feature/descriptive-name` for feature branches
- Use `bugfix/issue-description` for bug fixes

### 2. Commit Guidelines

- Use conventional commit messages:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation updates
  - `style:` for formatting changes
  - `refactor:` for code refactoring
  - `test:` for adding or modifying tests
  - `chore:` for maintenance tasks

- Example: `feat: add PDF processor with metadata extraction`

### 3. Changelog Updates

**IMPORTANT**: Update the CHANGELOG.md file with every significant commit.

When updating the changelog:
1. Add new versions at the top of the file
2. Include:
   - Version number and commit hash reference
   - Features added in the version
   - Current status of the system
   - Known issues
   - Planned next steps

Example format:
```markdown
### v0.X.0 - Feature Name (commit: commit-hash)
**Date**: Month Day, Year

**Features**:
- Feature 1
- Feature 2

**Status**: Brief description of system state.

**Issues**:
- Known issue 1
- Known issue 2

**Next Steps**:
- Planned improvement 1
- Planned improvement 2
```

### 4. Pull Request Process

1. Ensure code passes all tests
2. Update documentation to reflect changes
3. Update the CHANGELOG.md file
4. Submit PR against the appropriate branch

## Code Standards

### Python Style Guide

- Follow PEP 8 for code style
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Maximum line length: 100 characters

### Documentation

- Document all public functions and classes
- Include examples in docstrings where helpful
- Update README.md when adding major features

## Testing

- Write unit tests for new features
- Ensure all tests pass before committing
- Aim for good test coverage of critical functionality

## Version Control

- Do not commit directly to `main` branch
- Keep commits focused on a single change
- Rebase feature branches before merging

## Releasing

When making a new release:
1. Update version numbers in all relevant files
2. Finalize CHANGELOG.md entries
3. Tag the release with the version number
4. Create a GitHub release with release notes