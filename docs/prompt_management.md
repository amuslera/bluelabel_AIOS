# Prompt Management System

BlueAbel AIOS provides a comprehensive system for managing prompts through the Multi-Component Prompting (MCP) framework. This document explains how to use both the command-line interface (CLI) and web interface for prompt management.

## Overview

The MCP framework provides several key features:

- **Component-Based Prompts**: Modular, reusable prompt templates with placeholders
- **Versioning**: Track history of prompt changes and restore previous versions
- **Testing**: Test prompts with various LLM providers
- **Validation**: Check prompt templates for syntax errors and missing inputs
- **API Integration**: Seamless integration with the BlueAbel AIOS ecosystem

## Command-Line Interface

The Prompt Manager CLI provides a powerful command-line interface for working with the MCP system.

### Installation

The CLI tool is located at `/app/cli/prompt_manager.py`. It can be run directly if you have the required Python packages installed.

Make it executable:

```bash
chmod +x /app/cli/prompt_manager.py
```

### Basic Usage

```bash
./app/cli/prompt_manager.py [command] [options]
```

### Available Commands

- **list**: List all components
  ```bash
  ./app/cli/prompt_manager.py list [--tag TAG]
  ```

- **view**: View details of a component
  ```bash
  ./app/cli/prompt_manager.py view COMPONENT_ID
  ```

- **create**: Create a new component
  ```bash
  ./app/cli/prompt_manager.py create --name "Component Name" --description "Description" --template "Template text or file path" [--tags "tag1,tag2"]
  ```

- **edit**: Edit a component with your default text editor
  ```bash
  ./app/cli/prompt_manager.py edit COMPONENT_ID
  ```

- **edit-template**: Edit only the template portion of a component
  ```bash
  ./app/cli/prompt_manager.py edit-template COMPONENT_ID
  ```

- **versions**: List all versions of a component
  ```bash
  ./app/cli/prompt_manager.py versions COMPONENT_ID
  ```

- **view-version**: View a specific version of a component
  ```bash
  ./app/cli/prompt_manager.py view-version COMPONENT_ID VERSION
  ```

- **compare**: Compare two versions of a component
  ```bash
  ./app/cli/prompt_manager.py compare COMPONENT_ID VERSION1 VERSION2
  ```

- **restore**: Restore a component to a previous version
  ```bash
  ./app/cli/prompt_manager.py restore COMPONENT_ID VERSION
  ```

- **test-render**: Test render a component with inputs
  ```bash
  ./app/cli/prompt_manager.py test-render COMPONENT_ID --inputs "key1=value1,key2=value2"
  ```

- **test-llm**: Test a component with an LLM
  ```bash
  ./app/cli/prompt_manager.py test-llm COMPONENT_ID --inputs "key1=value1,key2=value2" [--provider PROVIDER] [--model MODEL]
  ```

### Examples

List all components:

```bash
./app/cli/prompt_manager.py list
```

Create a new component:

```bash
./app/cli/prompt_manager.py create \
  --name "Summarization Prompt" \
  --description "Summarizes text input into a concise format" \
  --template "templates/summarize.txt" \
  --tags "summarization,content"
```

Edit a component's template:

```bash
./app/cli/prompt_manager.py edit-template abc123
```

Compare two versions of a component:

```bash
./app/cli/prompt_manager.py compare abc123 1.0.1 1.0.0
```

Test a component with OpenAI:

```bash
./app/cli/prompt_manager.py test-llm abc123 \
  --inputs "text=This is a sample text to summarize." \
  --provider OpenAI \
  --model gpt-4
```

## Web Interface

The Prompt Manager also provides a user-friendly web interface built with Streamlit. This interface enables easy visual management of prompt components.

### Accessing the Web Interface

1. Start the Streamlit app:
   ```bash
   streamlit run app/ui/streamlit_app.py
   ```

2. Navigate to the "Prompt Manager" page in the Streamlit sidebar.

### Features

The web interface provides the following features:

- **Component List**: View all available prompt components
- **Detailed View**: See all details of a selected component
- **Component Editor**: Edit component name, description, tags, and template
- **Version History**: View all versions of a component
- **Version Comparison**: Compare different versions of a component
- **Version Restore**: Restore a component to a previous version
- **Testing Interface**: Test render components and test with LLM providers

## Template Syntax

MCP templates use a simple placeholder syntax:

```
This is a template with a {required_input} and an {optional_input:optional}.
```

- **Required inputs**: `{input_name}`
- **Optional inputs**: `{input_name:optional}`

## Best Practices

1. **Descriptive Names**: Give components clear, descriptive names that indicate their purpose
2. **Detailed Descriptions**: Include comprehensive descriptions to explain the component's usage
3. **Appropriate Tags**: Tag components for easy filtering and organization
4. **Version Carefully**: Increment versions when making significant changes
5. **Test Thoroughly**: Always test components before using them in production
6. **Document Inputs**: Clearly document what each input placeholder should contain
7. **Compare Before Restoring**: Always compare versions before restoring to avoid unintended changes

## API Endpoints

The MCP system provides a full REST API for programmatic access:

- `GET /components`: List all components
- `GET /components/{id}`: Get a specific component
- `POST /components`: Create a new component
- `PUT /components/{id}`: Update a component
- `DELETE /components/{id}`: Delete a component
- `GET /components/{id}/versions`: List all versions of a component
- `GET /components/{id}/version/{version}`: Get a specific version of a component
- `POST /components/{id}/validate`: Validate a component
- `POST /components/{id}/test-render`: Test render a component
- `POST /components/{id}/test-llm`: Test a component with an LLM

## Customization

Both the CLI and web interface can be customized to suit your needs:

### CLI Customization

You can modify `/app/cli/prompt_manager.py` to add new commands or change behavior.

### Web Interface Customization

The Streamlit interface in `/app/ui/pages/prompt_manager.py` can be extended with additional features.

## Troubleshooting

### Common Issues

1. **API Connection Errors**: Ensure the BlueAbel AIOS API is running and accessible.
2. **Template Validation Errors**: Check your template syntax for unclosed braces or invalid placeholders.
3. **Missing Inputs**: Ensure all required inputs are provided when testing.
4. **Version Conflicts**: When multiple users are editing the same component, conflicts can occur.

### Debugging

For CLI issues, run with the `--debug` flag to get more detailed logging:

```bash
./app/cli/prompt_manager.py --debug list
```

For web interface issues, check the Streamlit logs:

```bash
streamlit run app/ui/streamlit_app.py --log_level=debug
```

## Data Storage

The MCP framework stores components and their versions in a directory structure:

```
~/.bluelabel/
  components/
    [component_id].json
  versions/
    [component_id]/
      [version].json
```

This storage format enables easy backup and transfer of component libraries.

## Advanced Usage

### Bulk Operations

You can use the API to perform bulk operations like importing or exporting multiple components.

### Integration with External Systems

The MCP API can be integrated with external systems like version control, content management systems, or custom applications.

### Custom Component Types

The MCP framework can be extended to support custom component types beyond basic prompt templates.

## Conclusion

The Multi-Component Prompting (MCP) framework provides a powerful system for managing, versioning, and testing prompts in the BlueAbel AIOS ecosystem. With both CLI and web interfaces, it offers flexibility for various workflows and user preferences.